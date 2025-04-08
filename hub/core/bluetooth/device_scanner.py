import subprocess
import re
import time

class DeviceScanner:
    def get_discovered_devices(self, adapter=None):
        """발견된 디바이스 목록 가져오기
        
        Args:
            adapter (str, optional): 블루투스 어댑터 이름 (hci0, hci1 등)
            
        Returns:
            list: 발견된 디바이스 목록
        """
        print(f"발견된 디바이스 목록 가져오기 (어댑터: {adapter or '모든 어댑터'})")
        
        try:
            # 어댑터 지정된 경우와 아닌 경우 구분
            cmd = ["bluetoothctl", "devices"]
            if adapter:
                # 어댑터 상태 확인
                try:
                    hci_result = subprocess.run(
                        ["hciconfig", adapter],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    if "No such device" in hci_result.stderr:
                        print(f"❌ {adapter} 어댑터를 찾을 수 없습니다.")
                        interfaces = self.get_bluetooth_interfaces()
                        print("사용 가능한 어댑터:")
                        for iface in interfaces:
                            print(f"  - {iface['name']} ({iface['mac']})")
                        return []
                except Exception as e:
                    print(f"어댑터 확인 오류 (무시): {e}")
            
            # bluetoothctl devices 명령 실행
            print(f"bluetoothctl devices 명령 실행 중...")
            devices_result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            if devices_result.stderr:
                print(f"명령 실행 중 오류: {devices_result.stderr}")
            
            devices_output = devices_result.stdout
            print(f"명령 실행 결과:\n{devices_output}")
            
            devices = []
            for line in devices_output.splitlines():
                match = re.search(r'Device ([0-9A-F:]{17}) (.+)', line, re.IGNORECASE)
                if match:
                    mac = match.group(1)
                    name = match.group(2)
                    
                    # 어댑터 필터링 (어댑터가 지정된 경우에만)
                    if adapter:
                        try:
                            # info 명령으로 장치가 어떤 어댑터에 연결되어 있는지 확인
                            info_result = subprocess.run(
                                ["bluetoothctl", "info", mac],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=3
                            )
                            info_output = info_result.stdout
                            
                            # 어댑터 정보 추출
                            controller_match = re.search(r'Controller ([0-9A-F:]{17})', info_output, re.IGNORECASE)
                            if controller_match:
                                controller_mac = controller_match.group(1)
                                # 어댑터 MAC 주소로 어댑터 이름 찾기
                                for interface in self.get_bluetooth_interfaces():
                                    if interface['mac'].upper() == controller_mac.upper():
                                        device_adapter = interface['name']
                                        if device_adapter != adapter:
                                            print(f"장치 {name} ({mac})는 {device_adapter}에 있어 {adapter}에서 제외됨")
                                            continue
                        except Exception as e:
                            print(f"장치 정보 확인 오류 (무시): {e}")
                    
                    # 장치 유형 추측
                    device_type = self._guess_device_type(name)
                    
                    # RSSI 정보 가져오기
                    rssi = None
                    try:
                        # info 명령으로 RSSI 정보 가져오기
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
                        print(f"RSSI 정보 가져오기 오류 (무시): {e}")
                    
                    device = {
                        'mac': mac,
                        'name': name,
                        'type': device_type,
                        'rssi': rssi
                    }
                    
                    devices.append(device)
                    print(f"장치 발견: {name} ({mac}), 유형: {device_type}, RSSI: {rssi}")
            
            # 장치를 찾지 못한 경우 추가 정보 제공
            if not devices:
                print("발견된 장치가 없습니다. 추가 정보 확인 중...")
                
                # 어댑터 상태 확인
                try:
                    if adapter:
                        hci_info = subprocess.run(
                            ["hciconfig", adapter],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        print(f"어댑터 상태:\n{hci_info.stdout}")
                    
                    # bluetoothctl show로 컨트롤러 상태 확인
                    show_result = subprocess.run(
                        ["bluetoothctl", "show"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=3
                    )
                    print(f"컨트롤러 상태:\n{show_result.stdout}")
                    
                    # 스캔이 활성화 되어 있는지 확인
                    if "Discovering: yes" in show_result.stdout:
                        print("⚠️ 스캔이 이미 활성화 되어 있음. 스캔 재설정 필요할 수 있음.")
                    
                    # 수동으로 강제 디바이스 검색 시도 (bluetoothctl devices 대신 직접 스캔 결과 확인)
                    print("강제 스캔 시도...")
                    
                    # bluetoothctl 프로세스 시작
                    process = subprocess.Popen(
                        ["bluetoothctl"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # 필요한 명령어 전송
                    commands = [
                        f"scan off\n",  # 기존 스캔 중지
                        f"scan on\n",   # 새로 스캔 시작
                        "sleep 5\n",    # 5초 기다림
                        "devices\n",     # 장치 목록 확인
                        "quit\n"
                    ]
                    
                    # 명령어 전송
                    for cmd in commands:
                        process.stdin.write(cmd)
                        process.stdin.flush()
                        time.sleep(1)
                    
                    # 출력 확인
                    output, _ = process.communicate(timeout=10)
                    print(f"강제 스캔 결과:\n{output}")
                    
                    # 장치 목록 추출
                    for line in output.splitlines():
                        match = re.search(r'Device ([0-9A-F:]{17}) (.+)', line, re.IGNORECASE)
                        if match:
                            mac = match.group(1)
                            name = match.group(2)
                            
                            # 중복 확인
                            if not any(d['mac'] == mac for d in devices):
                                devices.append({
                                    'mac': mac,
                                    'name': name,
                                    'type': self._guess_device_type(name),
                                    'rssi': None
                                })
                                print(f"강제 스캔으로 발견: {name} ({mac})")
                    
                except Exception as e:
                    print(f"추가 정보 확인 중 오류: {e}")
            
            return devices
            
        except Exception as e:
            print(f"장치 목록 가져오기 오류: {e}")
            return []
    
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