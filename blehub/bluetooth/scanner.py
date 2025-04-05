#!/usr/bin/env python3
import os
import subprocess
import re
import time

from blehub.utils.logger import logger

"""
BLE-HUB 블루투스 스캐너 모듈

블루투스 모듈, 인터페이스 및 장치 검색 기능을 제공합니다.
"""

class BluetoothScanner:
    """블루투스 스캐너 클래스"""
    
    @staticmethod
    def get_bluetooth_interfaces():
        """시스템에서 사용 가능한 블루투스 인터페이스 목록을 반환합니다
        
        Returns:
            list: 블루투스 인터페이스 정보 목록
        """
        interfaces = []
        
        try:
            # 블루투스 어댑터 목록 조회
            result = subprocess.run(
                ["hciconfig"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"블루투스 인터페이스 조회 실패: {result.stderr}")
                return interfaces
            
            # 출력 분석
            output = result.stdout
            
            # 정규 표현식으로 인터페이스 정보 추출
            pattern = r"(hci\d+):\s+Type:\s+(\w+)\s+.*?BD Address:\s+([0-9A-F:]+)"
            matches = re.finditer(pattern, output, re.DOTALL)
            
            for match in matches:
                interface_id = match.group(1)
                interface_type = match.group(2)
                mac_address = match.group(3)
                
                # 추가 정보 가져오기
                name = BluetoothScanner.get_interface_name(interface_id)
                
                interfaces.append({
                    'id': interface_id,
                    'type': interface_type,
                    'mac': mac_address,
                    'name': name
                })
            
        except Exception as e:
            logger.error(f"블루투스 인터페이스 조회 중 오류 발생: {e}")
        
        return interfaces
    
    @staticmethod
    def scan_bluetooth_modules():
        """시스템에 연결된 블루투스 모듈을 검색합니다
        
        Returns:
            list: 블루투스 모듈 정보 목록
        """
        modules = []
        
        try:
            # 시스템 명령을 사용하여 블루투스 모듈 정보 가져오기
            # lsusb 명령으로 USB 연결 블루투스 모듈 확인
            lsusb_result = subprocess.run(
                ["lsusb"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if lsusb_result.returncode == 0:
                # 블루투스 관련 디바이스 찾기
                for line in lsusb_result.stdout.splitlines():
                    if "Bluetooth" in line or "bluetooth" in line.lower():
                        # ID와 설명 추출
                        match = re.search(r"ID\s+([0-9a-f:]+)\s+(.*)", line)
                        if match:
                            device_id = match.group(1)
                            description = match.group(2)
                            modules.append({
                                'type': 'usb',
                                'id': device_id,
                                'description': description,
                                'line': line.strip()
                            })
            
            # lspci 명령으로 PCI 연결 블루투스 모듈 확인
            lspci_result = subprocess.run(
                ["lspci"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if lspci_result.returncode == 0:
                # 블루투스 관련 디바이스 찾기
                for line in lspci_result.stdout.splitlines():
                    if "Bluetooth" in line or "bluetooth" in line.lower():
                        # ID와 설명 추출
                        match = re.search(r"([0-9a-f:.]+)\s+(.*)", line)
                        if match:
                            device_id = match.group(1)
                            description = match.group(2)
                            modules.append({
                                'type': 'pci',
                                'id': device_id,
                                'description': description,
                                'line': line.strip()
                            })
            
            # 블루투스 인터페이스 정보 가져오기
            interfaces = BluetoothScanner.get_bluetooth_interfaces()
            
            # 모듈과 인터페이스 연결 시도
            for module in modules:
                for interface in interfaces:
                    # 간단한 휴리스틱으로 연결 - 더 정확한 방법은 추가 연구 필요
                    module['interface'] = interface['id']
                    module['mac'] = interface['mac']
                    break  # 일단 첫 번째 인터페이스와 연결
            
            # 인터페이스 정보를 기반으로 추가 모듈 정보 추가
            for interface in interfaces:
                # 이미 모듈 목록에 있는지 확인
                already_added = False
                for module in modules:
                    if module.get('interface') == interface['id']:
                        already_added = True
                        break
                
                # 없으면 추가
                if not already_added:
                    modules.append({
                        'type': 'interface',
                        'id': interface['id'],
                        'description': interface['name'],
                        'interface': interface['id'],
                        'mac': interface['mac']
                    })
            
        except Exception as e:
            logger.error(f"블루투스 모듈 검색 중 오류 발생: {e}")
        
        return modules
    
    @staticmethod
    def scan_bluetooth_devices(interface_id="hci0", timeout=10):
        """블루투스 장치를 스캔합니다
        
        Args:
            interface_id (str): 사용할 블루투스 인터페이스 ID
            timeout (int): 스캔 시간(초)
            
        Returns:
            list: 블루투스 장치 정보 목록
        """
        devices = []
        
        try:
            logger.info(f"블루투스 장치 스캔 중... ({timeout}초)")
            
            # 장치 검색 명령 실행
            # 먼저 검색 활성화
            subprocess.run(
                ["hciconfig", interface_id, "up"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 검색 시작
            scan_process = subprocess.Popen(
                ["hcitool", "-i", interface_id, "scan"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 지정된 시간만큼 대기
            time.sleep(timeout)
            
            # 프로세스 종료
            scan_process.terminate()
            output, error = scan_process.communicate()
            
            if scan_process.returncode != 0 and not output:
                logger.error(f"블루투스 장치 스캔 실패: {error}")
                
                # lescan 시도
                logger.info("BLE 장치 스캔 시도 중...")
                lescan_process = subprocess.Popen(
                    ["hcitool", "-i", interface_id, "lescan"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                time.sleep(timeout)
                lescan_process.terminate()
                output, error = lescan_process.communicate()
                
                if lescan_process.returncode != 0 and not output:
                    logger.error(f"BLE 장치 스캔 실패: {error}")
                    
                    # 대체 방법 시도
                    devices = BluetoothScanner.scan_bluetooth_devices_alternative()
                    if devices:
                        return devices
                    
                    return devices
            
            # 출력 분석
            lines = output.strip().split('\n')
            
            # 첫 줄은 헤더이므로 건너뜀
            for line in lines[1:]:
                if not line.strip():
                    continue
                    
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    mac = parts[1]
                    name = parts[2] if len(parts) >= 3 else "Unknown"
                    
                    devices.append({
                        'mac': mac,
                        'name': name
                    })
                
        except Exception as e:
            logger.error(f"블루투스 장치 스캔 중 오류 발생: {e}")
        
        return devices
    
    @staticmethod
    def scan_bluetooth_devices_alternative():
        """대체 방법으로 블루투스 장치를 스캔합니다
        
        Returns:
            list: 블루투스 장치 정보 목록
        """
        devices = []
        
        # bluetoothctl이 있는지 확인
        if BluetoothScanner.test_bluetooth_tool("bluetoothctl", ["--version"]):
            try:
                # bluetoothctl 실행
                scan_cmd = subprocess.Popen(
                    ["bluetoothctl"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 명령어 전송
                commands = [
                    "power on",
                    "scan on",
                    # 5초 대기 (sleep 명령은 작동하지 않으므로 비어있는 명령 전송)
                    "scan off",
                    "devices",
                    "quit"
                ]
                
                # 명령어 실행
                for cmd in commands:
                    scan_cmd.stdin.write(cmd + "\n")
                    scan_cmd.stdin.flush()
                    if cmd == "scan on":
                        # 스캔 시간 5초 
                        time.sleep(5)
                
                # 결과 읽기
                output, _ = scan_cmd.communicate()
                
                # 출력 분석
                device_pattern = r"Device\s+([0-9A-F:]+)\s+(.+)"
                for line in output.splitlines():
                    match = re.search(device_pattern, line)
                    if match:
                        mac = match.group(1)
                        name = match.group(2)
                        devices.append({
                            'mac': mac,
                            'name': name
                        })
                
            except Exception as e:
                logger.error(f"bluetoothctl을 사용한 스캔 중 오류 발생: {e}")
        
        return devices
    
    @staticmethod
    def get_interface_name(interface_id):
        """블루투스 인터페이스 이름을 가져옵니다
        
        Args:
            interface_id (str): 블루투스 인터페이스 ID
            
        Returns:
            str: 인터페이스 이름
        """
        try:
            result = subprocess.run(
                ["hcitool", "-i", interface_id, "name"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                # 장치 정보 가져오기 시도
                result = subprocess.run(
                    ["bt-device", "-i", interface_id],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if result.returncode == 0:
                    name_match = re.search(r"Name:\s+(.+)", result.stdout)
                    if name_match:
                        return name_match.group(1).strip()
                
                return f"Bluetooth {interface_id}"
        except Exception as e:
            logger.error(f"인터페이스 이름 조회 중 오류 발생: {e}")
            return f"Bluetooth {interface_id}"
    
    @staticmethod
    def test_bluetooth_tool(command, args):
        """지정된 블루투스 도구가 사용 가능한지 테스트합니다
        
        Args:
            command (str): 테스트할 명령어
            args (list): 명령어 인자
            
        Returns:
            bool: 명령어 사용 가능 여부
        """
        try:
            result = subprocess.run(
                [command] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

# 편의 함수들
def list_bluetooth_modules():
    """블루투스 모듈 목록을 출력합니다
    
    Returns:
        list: 블루투스 모듈 목록
    """
    modules = BluetoothScanner.scan_bluetooth_modules()
    
    if not modules:
        print("시스템에서 블루투스 모듈을 찾을 수 없습니다.")
        return None
    
    print("\n" + "=" * 60)
    print("시스템 블루투스 모듈 목록".center(60))
    print("=" * 60)
    
    for i, module in enumerate(modules, 1):
        print(f"{i}. 타입: {module['type'].upper()}")
        print(f"   ID: {module['id']}")
        print(f"   설명: {module['description']}")
        if module.get('interface'):
            print(f"   인터페이스: {module['interface']}")
        if module.get('mac'):
            print(f"   MAC 주소: {module['mac']}")
        print("-" * 60)
    
    return modules

def select_bluetooth_module():
    """사용자에게 블루투스 모듈을 선택하도록 합니다
    
    Returns:
        dict: 선택된 블루투스 모듈 정보
    """
    modules = BluetoothScanner.scan_bluetooth_modules()
    
    if not modules:
        logger.error("시스템에서 블루투스 모듈을 찾을 수 없습니다.")
        print("시스템에서 블루투스 모듈을 찾을 수 없습니다.")
        return None
    
    print("\n" + "=" * 60)
    print("블루투스 모듈 선택".center(60))
    print("=" * 60)
    
    print("시스템에서 검색된 블루투스 모듈:")
    for i, module in enumerate(modules, 1):
        print(f"{i}. {module['description']} ({module['type'].upper()}: {module['id']})")
        if module.get('interface'):
            print(f"   인터페이스: {module['interface']}")
        if module.get('mac'):
            print(f"   MAC 주소: {module['mac']}")
    
    print("-" * 60)
    
    while True:
        choice = input("모듈 번호를 선택하세요 (0=취소): ")
        
        if choice == "0":
            return None
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(modules):
                return modules[index]
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
        except ValueError:
            print("숫자를 입력해주세요.")
    
    return None

def select_bluetooth_interface():
    """사용자에게 블루투스 인터페이스를 선택하도록 합니다
    
    Returns:
        dict: 선택된 블루투스 인터페이스 정보
    """
    interfaces = BluetoothScanner.get_bluetooth_interfaces()
    
    if not interfaces:
        logger.error("사용 가능한 블루투스 인터페이스가 없습니다.")
        print("사용 가능한 블루투스 인터페이스가 없습니다.")
        return None
    
    print("\n" + "=" * 50)
    print("블루투스 인터페이스 선택".center(50))
    print("=" * 50)
    
    print("사용 가능한 블루투스 인터페이스:")
    for i, interface in enumerate(interfaces, 1):
        print(f"{i}. {interface['name']} ({interface['id']}) - {interface['mac']}")
    
    print("-" * 50)
    
    while True:
        choice = input("인터페이스 번호를 선택하세요 (0=취소): ")
        
        if choice == "0":
            return None
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(interfaces):
                return interfaces[index]
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
        except ValueError:
            print("숫자를 입력해주세요.")
    
    return None

def select_bluetooth_device(interface_id="hci0"):
    """사용자에게 블루투스 장치를 선택하도록 합니다
    
    Args:
        interface_id (str): 사용할 블루투스 인터페이스 ID
        
    Returns:
        dict: 선택된 블루투스 장치 정보
    """
    print("\n블루투스 장치 검색 중입니다...")
    
    # 장치 스캔
    devices = BluetoothScanner.scan_bluetooth_devices(interface_id)
    
    # 검색된 장치가 없으면 대체 방법 시도
    if not devices:
        logger.warning("기본 방법으로 장치를 찾지 못했습니다. 대체 방법을 시도합니다.")
        print("대체 방법으로 장치 검색 중...")
        devices = BluetoothScanner.scan_bluetooth_devices_alternative()
    
    if not devices:
        logger.error("블루투스 장치를 찾을 수 없습니다.")
        print("블루투스 장치를 찾을 수 없습니다.")
        return None
    
    print("\n" + "=" * 50)
    print("블루투스 장치 선택".center(50))
    print("=" * 50)
    
    print("검색된 블루투스 장치:")
    for i, device in enumerate(devices, 1):
        print(f"{i}. {device['name']} - {device['mac']}")
    
    print("-" * 50)
    
    while True:
        choice = input("장치 번호를 선택하세요 (0=취소): ")
        
        if choice == "0":
            return None
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(devices):
                return devices[index]
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
        except ValueError:
            print("숫자를 입력해주세요.")
    
    return None 