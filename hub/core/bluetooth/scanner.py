#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 스캐너 모듈
"""

import os
import re
import subprocess
import time

class BluetoothScanner:
    """블루투스 스캐너 클래스"""
    
    def __init__(self):
        """스캐너 초기화"""
        self.interfaces = []
        self.devices = []
    
    def get_bluetooth_interfaces(self):
        """시스템에서 블루투스 인터페이스를 가져옵니다.
        
        Returns:
            list: 블루투스 인터페이스 목록 (각 항목은 dict 형태: {'name': 'hci0', 'mac': '00:11:22:33:44:55'})
        """
        self.interfaces = []
        
        try:
            # hciconfig 명령으로 블루투스 인터페이스 목록 가져오기
            output = self._execute_command(['hciconfig', '-a'])
            
            # 인터페이스 블록 패턴
            interface_blocks = output.split('\n\n')
            
            for block in interface_blocks:
                if not block.strip():
                    continue
                
                # 인터페이스 이름 추출 (hci0, hci1 등)
                name_match = re.search(r'^(hci\d+):', block, re.MULTILINE)
                if not name_match:
                    continue
                
                name = name_match.group(1)
                
                # MAC 주소 추출
                mac_match = re.search(r'BD Address: ([0-9A-F:]{17})', block, re.IGNORECASE)
                mac = mac_match.group(1) if mac_match else "알 수 없음"
                
                # 기본 정보만 추가
                device_info = {
                    'name': name,
                    'mac': mac
                }
                
                # 상태 정보 추출 (UP RUNNING 등)
                status_match = re.search(r'(UP|DOWN) (RUNNING|NOT RUNNING)', block, re.IGNORECASE)
                if status_match:
                    state = 'UP' in status_match.group(0)
                    running = 'RUNNING' in status_match.group(0)
                    device_info['state'] = 'Ready' if state and running else 'Not ready'
                
                self.interfaces.append(device_info)
            
            # hciconfig가 설치되어 있지 않거나 권한이 없는 경우 bluetoothctl 시도
            if not self.interfaces:
                output = self._execute_command(['bluetoothctl', 'list'])
                controller_lines = output.strip().split('\n')
                
                for line in controller_lines:
                    if not line.strip():
                        continue
                    
                    # Controller XX:XX:XX:XX:XX:XX [default]
                    match = re.search(r'Controller ([0-9A-F:]{17}) \[(.*?)\]', line, re.IGNORECASE)
                    if match:
                        mac = match.group(1)
                        is_default = 'default' in match.group(2)
                        
                        # Show 명령으로 추가 정보 가져오기
                        device_info = {
                            'name': f'hci{len(self.interfaces)}',  # 추정
                            'mac': mac,
                        }
                        
                        self.interfaces.append(device_info)
        except Exception as e:
            print(f"블루투스 인터페이스 검색 중 오류 발생: {e}")
            
        # 인터페이스를 찾지 못한 경우 기본 hci0 추가 시도
        if not self.interfaces:
            try:
                output = self._execute_command(['ls', '/sys/class/bluetooth'])
                for name in output.strip().split():
                    if name.startswith('hci'):
                        self.interfaces.append({
                            'name': name,
                            'mac': '알 수 없음',
                        })
            except Exception as e:
                print(f"블루투스 디렉토리 확인 중 오류 발생: {e}")
        
        return self.interfaces
    
    def scan_devices(self, interface='hci0', timeout=10):
        """지정된 인터페이스에서 블루투스 장치를 스캔합니다.
        
        Args:
            interface (str): 스캔에 사용할 블루투스 인터페이스
            timeout (int): 스캔 시간(초)
            
        Returns:
            list: 발견된 블루투스 장치 목록
        """
        self.devices = []
        
        try:
            # 스캐닝 전 인터페이스 가용성 확인
            self._execute_command(['hciconfig', interface, 'up'])
            
            # 일시적 스캔 파일 생성
            scan_output_file = '/tmp/bt_scan_output.txt'
            
            # 백그라운드에서 스캔 시작
            scan_proc = subprocess.Popen(
                ['timeout', str(timeout), 'hcitool', '-i', interface, 'lescan'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 동시에 장치 정보 수집
            time.sleep(2)  # 초기 스캔 시간 부여
            
            # 스캔 중 일정 간격으로 장치 정보 수집
            for _ in range(int(timeout/2)):
                try:
                    # 블루투스 장치 목록 조회
                    output = self._execute_command(['hcitool', '-i', interface, 'dev'])
                    lescan_output = self._execute_command(['bluetoothctl', 'devices'])
                    
                    # 결과 파싱
                    for line in lescan_output.splitlines():
                        # 'Device XX:XX:XX:XX:XX:XX DeviceName'
                        match = re.search(r'Device ([0-9A-F:]{17}) (.+)', line, re.IGNORECASE)
                        if match:
                            mac = match.group(1)
                            name = match.group(2)
                            
                            # 중복 확인
                            if not any(d['mac'] == mac for d in self.devices):
                                # 장치 정보 가져오기
                                device_info = self.get_device_info(mac)
                                if device_info:
                                    self.devices.append(device_info)
                                else:
                                    # 기본 정보만 추가
                                    self.devices.append({
                                        'name': name,
                                        'mac': mac,
                                        'type': self._guess_device_type(name),
                                        'rssi': None
                                    })
                    
                    time.sleep(2)
                except Exception as e:
                    print(f"장치 정보 수집 중 오류: {e}")
            
            # 스캔 프로세스 종료
            if scan_proc.poll() is None:
                scan_proc.terminate()
                try:
                    scan_proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    scan_proc.kill()
            
            # bluetoothctl로 장치 검색 시도
            if not self.devices:
                try:
                    # bluetoothctl로 장치 목록 가져오기
                    self._execute_command(['bluetoothctl', 'scan', 'on'])
                    time.sleep(5)
                    devices_output = self._execute_command(['bluetoothctl', 'devices'])
                    self._execute_command(['bluetoothctl', 'scan', 'off'])
                    
                    for line in devices_output.splitlines():
                        match = re.search(r'Device ([0-9A-F:]{17}) (.+)', line, re.IGNORECASE)
                        if match:
                            mac = match.group(1)
                            name = match.group(2)
                            
                            if not any(d['mac'] == mac for d in self.devices):
                                self.devices.append({
                                    'name': name,
                                    'mac': mac,
                                    'type': self._guess_device_type(name),
                                    'rssi': None
                                })
                except Exception as e:
                    print(f"bluetoothctl 검색 중 오류: {e}")
                    
        except Exception as e:
            print(f"블루투스 스캔 중 오류 발생: {e}")
        
        return self.devices
    
    def get_device_info(self, mac_address):
        """특정 MAC 주소의 장치 정보를 상세하게 가져옵니다.
        
        Args:
            mac_address (str): 장치의 MAC 주소
            
        Returns:
            dict: 장치 상세 정보 또는 None (찾지 못한 경우)
        """
        try:
            # bluetoothctl로 장치 정보 가져오기
            info_output = self._execute_command(['bluetoothctl', 'info', mac_address])
            
            if not info_output or 'No default controller available' in info_output:
                return None
                
            # 기본 정보 초기화
            device_info = {
                'mac': mac_address,
                'name': 'Unknown',
                'type': 'Unknown',
                'connected': False,
                'paired': False,
                'services': []
            }
            
            # 정보 파싱
            name_match = re.search(r'Name: (.+)', info_output)
            if name_match:
                device_info['name'] = name_match.group(1)
                device_info['type'] = self._guess_device_type(device_info['name'])
            
            # 연결 상태
            if 'Connected: yes' in info_output:
                device_info['connected'] = True
                
            # 페어링 상태
            if 'Paired: yes' in info_output:
                device_info['paired'] = True
                
            # UUID (서비스) 수집
            uuid_matches = re.findall(r'UUID: ([0-9a-fA-F-]+) \((.+?)\)', info_output)
            for uuid, desc in uuid_matches:
                device_info['services'].append({'uuid': uuid, 'desc': desc})
                
            # RSSI 정보 추가 (가능한 경우)
            rssi_match = re.search(r'RSSI: (-?\d+)', info_output)
            if rssi_match:
                device_info['rssi'] = int(rssi_match.group(1))
                
            return device_info
            
        except Exception as e:
            print(f"장치 정보 조회 중 오류: {e}")
            return None
            
    def _guess_device_type(self, device_name):
        """장치 이름을 기반으로 장치 유형을 추정합니다.
        
        Args:
            device_name (str): 장치 이름
            
        Returns:
            str: 추정된 장치 유형
        """
        name_lower = device_name.lower()
        
        # 키보드
        if any(keyword in name_lower for keyword in ['keyboard', '키보드', 'keeb']):
            return 'Keyboard'
            
        # 마우스
        if any(keyword in name_lower for keyword in ['mouse', '마우스']):
            return 'Mouse'
            
        # 헤드폰/이어폰
        if any(keyword in name_lower for keyword in ['headphone', 'earphone', 'earbuds', 'buds', '이어폰', '헤드폰']):
            return 'Audio'
            
        # 스피커
        if any(keyword in name_lower for keyword in ['speaker', '스피커']):
            return 'Speaker'
            
        # 기타 일반 장치
        return 'Device'
    
    def _execute_command(self, command):
        """시스템 명령을 실행하고 출력을 반환합니다.
        
        Args:
            command (list): 실행할 명령과 인자
            
        Returns:
            str: 명령 실행 결과
        """
        try:
            result = subprocess.run(command, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   universal_newlines=True, 
                                   check=False,  # 에러가 발생해도 진행
                                   timeout=15)  # 타임아웃 설정
                                   
            # 명령이 실패하더라도 출력은 반환
            return result.stdout
            
        except subprocess.TimeoutExpired:
            print(f"명령 실행 시간 초과: {' '.join(command)}")
            return ""
        except Exception as e:
            print(f"명령 실행 오류: {e}")
            return "" 