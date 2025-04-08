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
        
        # 실행 전 블루투스 서비스 상태 확인 및 재시작 시도
        try:
            print("블루투스 서비스 상태 확인 중...")
            status_result = subprocess.run(
                ["systemctl", "is-active", "bluetooth.service"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 블루투스 서비스가 inactive 또는 failed 상태인 경우 재시작 시도
            if "inactive" in status_result.stdout or "failed" in status_result.stdout:
                print("블루투스 서비스가 비활성 상태입니다. 재시작 시도...")
                try:
                    subprocess.run(
                        ["sudo", "systemctl", "restart", "bluetooth.service"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=10
                    )
                    print("블루투스 서비스를 재시작했습니다. 잠시 기다리는 중...")
                    time.sleep(3)  # 서비스 시작 대기
                except Exception as e:
                    print(f"블루투스 서비스 재시작 실패: {e}")
            else:
                print("블루투스 서비스가 활성 상태입니다.")
        except Exception as e:
            print(f"블루투스 서비스 상태 확인 실패: {e}")
        
        # 어댑터 초기화 시도
        try:
            print(f"{adapter} 어댑터 초기화 중...")
            # 먼저 어댑터 down
            subprocess.run(
                ["sudo", "hciconfig", adapter, "down"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3
            )
            time.sleep(1)
            
            # 어댑터 up
            subprocess.run(
                ["sudo", "hciconfig", adapter, "up"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3
            )
            print(f"{adapter} 어댑터 초기화 완료")
            time.sleep(1)
        except Exception as e:
            print(f"어댑터 초기화 중 오류 (무시): {e}")
        
        # 먼저 진행 중인 스캔 작업이 있으면 중지
        try:
            print("기존 스캔 중지 중...")
            subprocess.run(
                ["bluetoothctl", "scan", "off"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3
            )
            time.sleep(1)
        except Exception as e:
            print(f"스캔 중지 중 오류 (무시): {e}")
        
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
            
            # 명령어 전송 및 출력 확인 함수
            def send_command_and_check(cmd, wait_time=2.0, check_for_passkey=False):
                print(f"명령 실행: {cmd.strip()}")
                process.stdin.write(cmd)
                process.stdin.flush()
                
                start_time = time.time()
                output = ""
                
                # 명령 실행 결과 확인
                while time.time() - start_time < wait_time:
                    if process.stdout in select.select([process.stdout], [], [], 0.1)[0]:
                        line = process.stdout.readline()
                        if line:
                            output += line
                            print(f"출력: {line.strip()}")
                            
                            # 페어링 시 암호 확인 감지 및 자동 응답
                            if check_for_passkey and "[agent]" in line and "Confirm passkey" in line:
                                print("🔑 암호 확인 요청 감지, 자동으로 'yes' 응답...")
                                process.stdin.write("yes\n")
                                process.stdin.flush()
                                
                                # 추가 시간 대기 (응답 후 처리 시간)
                                extra_start = time.time()
                                while time.time() - extra_start < 3.0:
                                    if process.stdout in select.select([process.stdout], [], [], 0.1)[0]:
                                        response_line = process.stdout.readline()
                                        if response_line:
                                            output += response_line
                                            print(f"출력: {response_line.strip()}")
                                    time.sleep(0.1)
                    
                    # 잠시 대기
                    time.sleep(0.1)
                
                return output
            
            # 필요한 명령어 순차적 실행
            # 먼저 간단한 setup 명령으로 초기화
            initial_commands = [
                "power on\n",
                "discoverable on\n",
                "pairable on\n",
                "agent on\n",
                "default-agent\n"
            ]
            
            print("기본 설정 명령 실행 중...")
            for cmd in initial_commands:
                send_command_and_check(cmd, 1.0)
            
            # 특정 어댑터 선택 (실행에 실패하더라도 계속 진행)
            if adapter:
                select_output = send_command_and_check(f"select {adapter}\n", 3.0)
                if "Controller" not in select_output and "not available" in select_output:
                    print(f"⚠️ {adapter} 어댑터를 사용할 수 없습니다. 다른 어댑터를 확인해보세요.")
                    # 어댑터 목록 확인 (어댑터가 사용 불가능한 경우)
                    interfaces = self.scanner.get_bluetooth_interfaces()
                    if interfaces:
                        print("사용 가능한 어댑터 목록:")
                        for iface in interfaces:
                            print(f"  - {iface['name']} ({iface['mac']})")
                    else:
                        print("  사용 가능한 블루투스 어댑터가 없습니다.")
            
            # 스캔 시작 및 대기
            scan_output = send_command_and_check("scan on\n", 2.0)
            print("스캔 시작됨. 장치 발견 대기 중...")
            
            # 스캔 대기 - 시간이 너무 짧으면 장치를 발견하지 못할 수 있음
            time.sleep(8)
            
            # 페어링, 신뢰, 연결 명령 실행
            pair_output = send_command_and_check(f"pair {device_mac}\n", 15.0, True)  # 페어링은 시간이 더 걸리고 passkey 확인이 필요할 수 있음
            
            # 페어링이 실패했는지 확인
            if "Failed to pair" in pair_output:
                print("⚠️ 페어링 실패. 장치가 페어링 가능 상태인지 확인하세요.")
                # 연결 해제 시도 후 다시 페어링 시도
                send_command_and_check(f"disconnect {device_mac}\n", 5.0)
                time.sleep(2)
                send_command_and_check(f"remove {device_mac}\n", 5.0)
                time.sleep(2)
                pair_output = send_command_and_check(f"pair {device_mac}\n", 15.0, True)
            
            # 신뢰 및 연결 명령
            trust_output = send_command_and_check(f"trust {device_mac}\n", 5.0)
            connect_output = send_command_and_check(f"connect {device_mac}\n", 10.0)
            
            # 스캔 중지 및 종료
            send_command_and_check("scan off\n", 2.0)
            send_command_and_check("quit\n", 1.0)
            
            # 프로세스 종료 확인
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("프로세스 종료 대기 시간 초과")
                process.terminate()
            
            # 최종 장치 상태 확인
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
            
            # 성공적인 페어링 여부 확인
            if "Paired: yes" in info_result:
                print(f"✅ {device_name} 페어링 성공!")
                return True
                
            # 연결 여부 확인 (Connected: yes)
            if "Connected: yes" in info_result:
                print(f"✅ {device_name} 연결 성공!")
                return True
            
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
    
    def _guess_device_type(self, device_name):
        """장치 이름으로 장치 유형을 추측
        
        Args:
            device_name (str): 장치 이름
            
        Returns:
            str: 추측된 장치 유형
        """
        device_name_lower = device_name.lower()
        
        # 키워드 기반 장치 유형 추측
        if any(keyword in device_name_lower for keyword in ['mouse', 'mx', 'trackpad']):
            return 'mouse'
        elif any(keyword in device_name_lower for keyword in ['keyboard', 'keypad', 'k780']):
            return 'keyboard'
        elif any(keyword in device_name_lower for keyword in ['speaker', 'audio', 'sound']):
            return 'speaker'
        elif any(keyword in device_name_lower for keyword in ['headphone', 'headset', 'earbuds', 'airpods']):
            return 'headphone'
        elif any(keyword in device_name_lower for keyword in ['phone', 'galaxy', 'iphone', 'pixel']):
            return 'smartphone'
        else:
            return 'other'
    
    def scan_with_progress(self, adapter, timeout=30):
        """진행 상황을 표시하며 블루투스 디바이스 스캔
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            timeout (int): 스캔 제한 시간(초)
            
        Returns:
            list: 발견된 디바이스 목록
        """
        print(f"\n🔍 {adapter} 어댑터로 {timeout}초 동안 블루투스 디바이스 스캔 중...")
        
        # 어댑터 상태 확인
        try:
            # hciconfig로 어댑터 확인
            hci_result = subprocess.run(
                ["hciconfig", adapter],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if "No such device" in hci_result.stderr:
                print(f"❌ {adapter} 어댑터를 찾을 수 없습니다.")
                print("사용 가능한 어댑터 목록:")
                interfaces = self.scanner.get_bluetooth_interfaces()
                if interfaces:
                    for iface in interfaces:
                        print(f"  - {iface['name']} ({iface['mac']})")
                else:
                    print("  사용 가능한 블루투스 어댑터가 없습니다.")
                return []
        except Exception as e:
            print(f"어댑터 상태 확인 중 오류: {e}")
        
        # 디바이스 목록 저장용
        devices = []
        
        # 방법 1: 기존 bluetoothctl로 스캔
        try:
            # bluetoothctl 실행
            process = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 명령어 전송 및 출력 확인 함수
            def send_command_and_print(cmd, wait_time=2):
                print(f"명령 실행: {cmd.strip()}")
                process.stdin.write(cmd)
                process.stdin.flush()
                
                end_time = time.time() + wait_time
                output = ""
                
                while time.time() < end_time:
                    if process.stdout in select.select([process.stdout], [], [], 0.1)[0]:
                        line = process.stdout.readline()
                        if line:
                            output += line
                            print(f"출력: {line.strip()}")
                    time.sleep(0.1)
                
                return output
            
            # 어댑터 선택
            send_command_and_print(f"select {adapter}\n", 3)
            
            # 블루투스 에이전트 설정
            send_command_and_print("agent on\n")
            send_command_and_print("default-agent\n")
            
            # 스캔 시작
            send_command_and_print("scan on\n")
            
            # 타이머 설정
            start_time = time.time()
            
            # 진행 표시 문자
            progress_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            i = 0
            
            # 스캔 중 표시
            try:
                while time.time() - start_time < timeout:
                    # 진행 표시 업데이트
                    remaining = int(timeout - (time.time() - start_time))
                    sys.stdout.write(f"\r{progress_chars[i]} 스캔 중... 남은 시간: {remaining}초  ")
                    sys.stdout.flush()
                    i = (i + 1) % len(progress_chars)
                    
                    # 잠시 대기
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n스캔이 사용자에 의해 중단되었습니다.")
            
            # 개행
            print("\n")
            
            # 스캔 중지
            send_command_and_print("scan off\n")
            
            # 발견된 장치 확인
            devices_output = send_command_and_print("devices\n", 3)
            print(f"발견된 장치 목록: {devices_output}")
            
            # 프로세스 종료
            send_command_and_print("quit\n")
            process.wait(timeout=5)
            
            # 장치 정보 제대로 가져오지 못했을 경우 대체 방법 사용
            if not devices_output.strip() or "No default controller available" in devices_output:
                print("bluetoothctl 방식으로 장치 목록 가져오기 실패")
                # 이미 발견된 디바이스 목록 사용
                print("이미 발견된 디바이스 목록을 사용합니다...")
                devices = self.scanner.get_discovered_devices(adapter)
            else:
                # 장치 목록 파싱
                for line in devices_output.splitlines():
                    match = re.search(r'Device ([0-9A-F:]{17}) (.+)', line, re.IGNORECASE)
                    if match:
                        mac = match.group(1)
                        name = match.group(2)
                        
                        # 추가 정보 가져오기
                        device_type = self._guess_device_type(name)
                        
                        # RSSI 값 가져오기 시도
                        rssi = None
                        try:
                            info_result = subprocess.run(
                                ["bluetoothctl", "info", mac],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=3
                            )
                            info_output = info_result.stdout
                            
                            # RSSI 값 추출
                            rssi_match = re.search(r'RSSI: (-?\d+)', info_output)
                            if rssi_match:
                                rssi = int(rssi_match.group(1))
                        except Exception as e:
                            print(f"장치 정보 가져오기 실패: {e}")
                        
                        device = {
                            'mac': mac,
                            'name': name,
                            'type': device_type,
                            'rssi': rssi
                        }
                        
                        devices.append(device)
        
        except Exception as e:
            print(f"bluetoothctl을 이용한 스캔 중 오류: {e}")
        
        # 장치 목록을 가져오지 못했을 경우 대체 방법 사용
        if not devices:
            print("bluetoothctl 방식 실패, hcitool 방식으로 재시도...")
            
            # 방법 2: hcitool을 사용한 스캔
            try:
                # 어댑터 초기화 (권한 문제가 있을 수 있음)
                try:
                    subprocess.run(["sudo", "hciconfig", adapter, "reset"], stderr=subprocess.PIPE, stdout=subprocess.PIPE, timeout=3)
                except Exception as e:
                    print(f"어댑터 초기화 중 오류 (무시): {e}")
                
                # hcitool scan 실행 (약식 스캔)
                print(f"hcitool을 사용하여 {adapter} 어댑터로 스캔 중...")
                
                # 어댑터를 활성화하여 준비
                try:
                    subprocess.run(
                        ["sudo", "hciconfig", adapter, "up"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=3
                    )
                except Exception:
                    pass  # 예외 무시
                
                # 타임아웃이 너무 길면 명령이 중단될 수 있으므로 더 짧게 설정
                scan_timeout = min(timeout, 15)  # 최대 15초로 제한
                
                try:
                    scan_result = subprocess.run(
                        ["hcitool", "-i", adapter, "scan"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=scan_timeout
                    )
                    
                    scan_output = scan_result.stdout
                    print(f"hcitool 스캔 결과: {scan_output}")
                    
                    # 장치 목록 파싱
                    for line in scan_output.splitlines():
                        if line.startswith("Scanning"):
                            continue
                            
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            mac = parts[0].strip()
                            name = parts[1].strip()
                            
                            # 추가 정보 가져오기
                            device_type = self._guess_device_type(name)
                            
                            device = {
                                'mac': mac,
                                'name': name,
                                'type': device_type,
                                'rssi': None  # hcitool scan에서는 RSSI 정보 제공 안함
                            }
                            
                            devices.append(device)
                except subprocess.TimeoutExpired:
                    print(f"hcitool 스캔 시간 초과 ({scan_timeout}초). 대체 방식으로 시도합니다...")
                    
                    # 대체 스캔: hcitool lescan 시도 (저전력 스캔)
                    try:
                        print("hcitool lescan으로 재시도...")
                        lescan_result = subprocess.run(
                            ["timeout", "5", "hcitool", "-i", adapter, "lescan"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        print(f"lescan 결과: {lescan_result.stdout}")
                        
                        # 장치 MAC 주소와 이름 추출
                        for line in lescan_result.stdout.splitlines():
                            if not line or line.startswith("LE Scan"):
                                continue
                                
                            parts = line.strip().split(' ', 1)
                            if len(parts) >= 2:
                                mac = parts[0].strip()
                                name = parts[1].strip() if len(parts) > 1 else "Unknown"
                                
                                device = {
                                    'mac': mac,
                                    'name': name,
                                    'type': self._guess_device_type(name),
                                    'rssi': None
                                }
                                
                                # 중복 검사
                                if not any(d['mac'] == mac for d in devices):
                                    devices.append(device)
                    except Exception as e:
                        print(f"lescan 시도 중 오류: {e}")
            
            except Exception as e:
                print(f"hcitool을 이용한 스캔 중 오류: {e}")
                
                # 마지막 시도: 이미 발견된 디바이스 목록 사용
                print("스캔에 실패했습니다. 이미 발견된 디바이스 목록을 사용합니다...")
                devices = self.scanner.get_discovered_devices(adapter)
        
        # 최종 상태 확인
        print(f"\n총 {len(devices)}개 장치 발견\n")
        
        # 장치 상태 확인
        if len(devices) == 0:
            print("장치가 발견되지 않았습니다. 장치 상태 확인 중...")
            
            try:
                # 최종 장치 상태 확인
                info_cmd = ["bluetoothctl", "info", "F0:F5:64:55:36:3D"]  # 상태 확인할 장치 MAC 지정
                info_result = subprocess.run(
                    info_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                ).stdout
                
                print("장치 상태 정보:")
                print(info_result)
            except Exception as e:
                print(f"장치 상태 확인 중 오류: {e}")
        
        return devices 