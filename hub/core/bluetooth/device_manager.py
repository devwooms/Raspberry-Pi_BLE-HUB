#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 디바이스 관리 클래스
"""

import os
import re
import time
import subprocess
import sys
import select

class BluetoothDeviceManager:
    """블루투스 디바이스 관리 클래스"""
    
    def __init__(self, scanner):
        """초기화
        
        Args:
            scanner: 블루투스 스캐너 인스턴스
        """
        self.scanner = scanner
    
    def pair_device(self, adapter, device_mac):
        """블루투스 디바이스 페어링
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치 페어링 시도 중...")
            
            # 페어링 전 장치 상태 확인
            print("장치 상태 확인 중...")
            info_cmd = ["bluetoothctl", "info", device_mac]
            info_result = subprocess.run(
                info_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            ).stdout
            
            print(f"현재 장치 상태:\n{info_result}")
            
            # 이미 페어링되어 있는지 확인
            if "Paired: yes" in info_result:
                print("이미 페어링되어 있습니다.")
                return True
            
            # 직접 bluetoothctl과 상호작용 (더 안정적인 방법)
            print("bluetoothctl을 이용한 대화식 페어링 시도...")
            
            process = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 필요한 명령어 순차적 실행
            commands = [
                f"select {adapter}\n",
                "agent on\n",
                "default-agent\n",
                f"pair {device_mac}\n"
            ]
            
            output = ""
            
            for cmd in commands:
                print(f"명령 실행: {cmd.strip()}")
                process.stdin.write(cmd)
                process.stdin.flush()
                
                # 명령마다 잠시 대기
                time.sleep(2)
                
                # 출력 확인
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    output += line
                    print(f"블루투스 출력: {line.strip()}")
            
            # 프로세스 종료
            process.stdin.write("quit\n")
            process.stdin.flush()
            remaining_output, _ = process.communicate(timeout=5)
            output += remaining_output
            
            # 결과 분석
            if "Pairing successful" in output:
                print(f"페어링 성공: {device_mac}")
                return True
            elif "Already paired" in output:
                print("이미 페어링되어 있습니다.")
                return True
            else:
                print(f"페어링 실패. 자세한 출력:\n{output}")
                
                # 재시도: 단순 페어링 방식
                print("단순 페어링 방식으로 재시도 중...")
                simple_cmd = ["bluetoothctl", "pair", device_mac]
                simple_result = subprocess.run(
                    simple_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15
                )
                
                if "Pairing successful" in simple_result.stdout:
                    print(f"단순 방식으로 페어링 성공: {device_mac}")
                    return True
                else:
                    print(f"단순 방식도 실패. 출력:\n{simple_result.stdout}")
                    return False
                
        except subprocess.TimeoutExpired:
            print("페어링 시간 초과. 장치가 응답하지 않습니다.")
            return False
        except Exception as e:
            print(f"페어링 중 오류: {e}")
            return False
    
    def trust_device(self, adapter, device_mac):
        """블루투스 디바이스 신뢰 설정
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치 신뢰 설정 중...")
            
            # bluetoothctl 명령으로 신뢰 설정
            cmd = [
                "bluetoothctl",
                "trust",
                device_mac
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if "trusted: yes" in process.stdout:
                print(f"신뢰 설정 성공: {device_mac}")
                return True
            else:
                print(f"신뢰 설정 실패: {process.stdout}")
                return False
                
        except Exception as e:
            print(f"신뢰 설정 중 오류: {e}")
            return False
    
    def connect_device(self, adapter, device_mac):
        """블루투스 디바이스 연결
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치에 연결 시도 중...")
            
            # bluetoothctl 명령으로 연결
            cmd = [
                "bluetoothctl",
                "connect",
                device_mac
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15  # 연결에는 시간이 걸릴 수 있음
            )
            
            if "Connection successful" in process.stdout:
                print(f"연결 성공: {device_mac}")
                return True
            else:
                print(f"연결 실패: {process.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            print("연결 시간 초과. 장치가 응답하지 않습니다.")
            return False
        except Exception as e:
            print(f"연결 중 오류: {e}")
            return False
    
    def disconnect_device(self, adapter, device_mac):
        """블루투스 디바이스 연결 해제
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치 연결 해제 중...")
            
            # bluetoothctl 명령으로 연결 해제
            cmd = [
                "bluetoothctl",
                "disconnect",
                device_mac
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if "Successful disconnected" in process.stdout or "Device has been disconnected" in process.stdout:
                print(f"연결 해제 성공: {device_mac}")
                return True
            else:
                print(f"연결 해제 실패: {process.stdout}")
                return False
                
        except Exception as e:
            print(f"연결 해제 중 오류: {e}")
            return False
    
    def remove_device(self, adapter, device_mac):
        """블루투스 디바이스 제거 (페어링 삭제)
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치 제거 중...")
            
            # bluetoothctl 명령으로 장치 제거
            cmd = [
                "bluetoothctl",
                "remove",
                device_mac
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if "Device has been removed" in process.stdout or "was removed" in process.stdout:
                print(f"장치 제거 성공: {device_mac}")
                return True
            else:
                print(f"장치 제거 실패: {process.stdout}")
                return False
                
        except Exception as e:
            print(f"장치 제거 중 오류: {e}")
            return False
    
    def setup_device(self, adapter, device_mac, device_name):
        """블루투스 디바이스 설정 (페어링, 신뢰, 연결 순서로 진행)
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            device_name (str): 장치 이름
            
        Returns:
            bool: 성공 여부
        """
        print(f"\n== {device_name} ({device_mac}) 장치 설정 ==")
        
        # 한번에 여러 명령을 연속 실행하는 방법 시도
        try:
            print("bluetoothctl을 이용한 통합 설정 시도...")
            
            # bluetoothctl 실행
            process = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 필요한 명령어 순차적 실행 (수동으로 성공한 방식 그대로)
            commands = [
                f"select {adapter}\n",
                "agent on\n",
                "default-agent\n",
                f"scan on\n",  # 먼저 스캔을 시작하여 장치가 발견되도록 함
                f"pair {device_mac}\n",
                f"trust {device_mac}\n",
                f"connect {device_mac}\n",
                f"scan off\n",
                "quit"
            ]
            
            print("수동 방식과 동일한 명령어 시퀀스로 실행합니다...")
            for cmd in commands:
                print(f"명령 실행: {cmd.strip()}")
                process.stdin.write(cmd)
                process.stdin.flush()
                
                # 잠시 기다림 (명령마다 약간의 시간을 줌)
                time.sleep(1)
                
                # 실시간으로 일부 출력 확인
                while select.select([process.stdout], [], [], 0.1)[0]:
                    line = process.stdout.readline()
                    if line:
                        print(f"출력: {line.strip()}")
            
            # 나머지 출력 확인
            output, _ = process.communicate(timeout=5)
            print(output)
            
            # 최종 장치 상태 확인 (이 부분이 가장 중요)
            print("최종 장치 상태 확인 중...")
            info_cmd = ["bluetoothctl", "info", device_mac]
            info_result = subprocess.run(
                info_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            ).stdout
            
            print(f"장치 상태 정보:\n{info_result}")
            
            # 다양한 성공 지표 확인
            connection_success = "Connected: yes" in info_result
            paired_success = "Paired: yes" in info_result
            trusted_success = "Trusted: yes" in info_result
            
            if connection_success:
                print(f"✅ 연결 성공: {device_name} ({device_mac})가 성공적으로 연결되었습니다!")
                return True
            elif paired_success and trusted_success:
                print(f"⚠️ 부분 성공: 페어링과 신뢰는 완료됐으나 연결되지 않았습니다.")
                
                # 한번 더 연결 시도
                print("연결 한번 더 시도 중...")
                connect_cmd = ["bluetoothctl", "connect", device_mac]
                connect_result = subprocess.run(
                    connect_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10
                )
                
                if "Connection successful" in connect_result.stdout:
                    print(f"✅ 두번째 연결 시도 성공: {device_name} ({device_mac}) 연결됨!")
                    return True
                else:
                    print(f"⚠️ 두번째 연결 시도 실패. 출력: {connect_result.stdout}")
            
            # 출력에서 성공 지표 확인 (로그 기반)
            success_indicators = [
                "Pairing successful",
                "Connection successful",
                "trust succeeded",
                "paired: yes",
                "trusted: yes",
                "connected: yes"
            ]
            
            # 하나라도 성공 지표가 있으면 성공으로 간주
            if any(indicator in output for indicator in success_indicators):
                print(f"📝 로그 기반 성공: {device_name} ({device_mac}) 설정 완료!")
                return True
                
            # 모든 시도가 실패한 경우 기존 방법으로 시도
            print("통합 방법 실패, 개별 명령 방식으로 다시 시도합니다...")
            
        except Exception as e:
            print(f"통합 설정 중 오류 (무시): {e}")
            print("개별 명령 방식으로 다시 시도합니다...")
            
        # 개별 명령 방식 (기존 코드)
        # 페어링 진행
        if not self.pair_device(adapter, device_mac):
            print("페어링 실패로 설정을 중단합니다.")
            return False
            
        # 신뢰 설정
        if not self.trust_device(adapter, device_mac):
            print("신뢰 설정 실패. 연결을 시도합니다.")
            
        # 연결 진행
        if not self.connect_device(adapter, device_mac):
            print("연결 실패. 장치가 가까이 있는지 확인하세요.")
            return False
            
        print(f"{device_name} ({device_mac}) 장치 설정 완료!")
        return True
        
    def remove_device_completely(self, adapter, device_mac, device_name):
        """블루투스 디바이스 완전 제거 (연결 해제 후 장치 제거)
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            device_name (str): 장치 이름
            
        Returns:
            bool: 성공 여부
        """
        print(f"\n== {device_name} ({device_mac}) 장치 제거 ==")
        
        # 연결 해제
        self.disconnect_device(adapter, device_mac)
        
        # 잠시 대기
        time.sleep(1)
        
        # 장치 제거
        if self.remove_device(adapter, device_mac):
            print(f"{device_name} ({device_mac}) 장치가 완전히 제거되었습니다.")
            return True
        else:
            print(f"{device_name} ({device_mac}) 장치 제거에 실패했습니다.")
            return False
            
    def get_adapter_name_from_mac(self, mac_address):
        """MAC 주소로 어댑터 이름 찾기
        
        Args:
            mac_address (str): 어댑터 MAC 주소
            
        Returns:
            str: 어댑터 이름 (hci0, hci1 등) 또는 None
        """
        interfaces = self.scanner.get_bluetooth_interfaces()
        
        for interface in interfaces:
            if interface['mac'].lower() == mac_address.lower():
                return interface['name']
                
        return None
    
    def scan_with_progress(self, adapter, timeout=30):
        """진행 상황을 표시하며 블루투스 디바이스 스캔
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            timeout (int): 스캔 제한 시간(초)
            
        Returns:
            list: 발견된 디바이스 목록
        """
        try:
            print(f"{adapter} 어댑터를 이용하여 주변 디바이스 스캔을 시작합니다...")
            print(f"스캔 시간: {timeout}초")
            
            # 어댑터 준비
            try:
                subprocess.run(
                    ["hciconfig", adapter, "up"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=3
                )
                # 기존 스캔 중지
                subprocess.run(
                    ["bluetoothctl", "scan", "off"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=3
                )
            except Exception as e:
                print(f"어댑터 초기화 중 오류 (무시): {e}")
            
            # 먼저 기존에 발견된 장치 가져오기
            initial_devices = self.scanner.get_discovered_devices(adapter)
            
            # 스캔 시작 명령 (분리된 프로세스로 실행)
            scan_process = subprocess.Popen(
                ["bluetoothctl", "-i", adapter, "scan", "on"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True
            )
            
            # 동시에 legacy 스캔도 시작 (별도 프로세스)
            legacy_scan_process = None
            try:
                legacy_scan_process = subprocess.Popen(
                    ["hcitool", "-i", adapter, "scan"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True
                )
            except Exception as e:
                print(f"Legacy 스캔 시작 실패 (무시): {e}")
            
            # 디바이스 목록 관리
            devices = []
            if initial_devices:
                devices = initial_devices
                print(f"\n이미 발견된 장치: {len(initial_devices)}개")
                for device in initial_devices:
                    print(f"기존 장치: {device['name']} ({device['mac']})")
            
            # 시간 경과와 함께 진행 상황 표시
            for current_time in range(timeout):
                time_left = timeout - current_time
                print(f"\r스캔 중... {current_time+1}/{timeout}초 경과 (남은 시간: {time_left}초)", end="")
                
                # 1초마다 발견된 장치 가져오기
                # 다양한 방법으로 장치 검색 시도
                found_devices = []
                
                # 1. bluetoothctl devices
                try:
                    bt_devices = self.scanner.get_discovered_devices(adapter)
                    found_devices.extend(bt_devices)
                except Exception as e:
                    print(f"\n장치 목록 가져오기 오류 (무시): {e}")
                
                # 2. hcitool lescan 결과 (만약 실행 중이라면)
                if current_time > 3 and current_time % 5 == 0:  # 5초마다 추가 스캔
                    try:
                        # 임시 스캔 실행
                        temp_scan = subprocess.run(
                            ["timeout", "2", "hcitool", "-i", adapter, "lescan"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        # hcitool로 장치 확인
                        subprocess.run(
                            ["hcitool", "-i", adapter, "dev"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                    except Exception as e:
                        print(f"\n추가 스캔 오류 (무시): {e}")
                
                # 새로운 장치가 있으면 추가
                for device in found_devices:
                    if not any(d['mac'] == device['mac'] for d in devices):
                        devices.append(device)
                        # 진행 막대 아래에 찾은 장치 실시간으로 표시
                        print(f"\n발견: {device['name']} ({device['mac']})")
                
                # 중간에 장치가 발견되면 빠르게 반환
                if devices and current_time > 10 and current_time % 5 == 0:
                    print("\n장치를 발견했습니다. 계속 스캔하려면 Enter 키를 누르세요. 중단하려면 'q'를 입력하세요. (5초 후 자동으로 계속)")
                    if select.select([sys.stdin], [], [], 5)[0]:
                        user_input = sys.stdin.readline().strip()
                        if user_input.lower() == 'q':
                            print("사용자에 의해 스캔이 중단되었습니다.")
                            break
                
                time.sleep(1)
            
            # 스캔 종료
            print("\n\n스캔 완료!")
            
            # 스캔 중지 명령
            try:
                subprocess.run(
                    ["bluetoothctl", "scan", "off"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=3
                )
            except Exception as e:
                print(f"스캔 중지 오류 (무시): {e}")
            
            # 스캔 프로세스 종료
            try:
                if scan_process and scan_process.poll() is None:
                    scan_process.terminate()
                if legacy_scan_process and legacy_scan_process.poll() is None:
                    legacy_scan_process.terminate()
            except Exception as e:
                print(f"프로세스 종료 오류 (무시): {e}")
                
            # 장치가 없는 경우 다른 방법 시도
            if not devices:
                print("\n장치를 찾을 수 없습니다. 다른 방법으로 다시 시도합니다...")
                
                try:
                    # bluetoothctl interactive 모드로 직접 명령 실행
                    bluetoothctl_process = subprocess.Popen(
                        ["bluetoothctl"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    commands = [
                        f"select {adapter}\n",
                        "scan on\n",
                        "sleep 10\n",
                        "devices\n",
                        "scan off\n",
                        "quit\n"
                    ]
                    
                    for cmd in commands:
                        bluetoothctl_process.stdin.write(cmd)
                        bluetoothctl_process.stdin.flush()
                        time.sleep(1)
                    
                    output, _ = bluetoothctl_process.communicate(timeout=15)
                    
                    # 결과 파싱
                    for line in output.splitlines():
                        match = re.search(r'Device ([0-9A-F:]{17}) (.+)', line, re.IGNORECASE)
                        if match:
                            mac = match.group(1)
                            name = match.group(2)
                            
                            if not any(d['mac'] == mac for d in devices):
                                devices.append({
                                    'name': name,
                                    'mac': mac,
                                    'type': self.scanner._guess_device_type(name),
                                    'rssi': None
                                })
                                print(f"추가 발견: {name} ({mac})")
                except Exception as e:
                    print(f"대체 스캔 방법 오류 (무시): {e}")
            
            return devices
                
        except Exception as e:
            print(f"\n스캔 중 오류 발생: {e}")
            return [] 