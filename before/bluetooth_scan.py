#!/usr/bin/env python3
import subprocess
import time
import sys
import threading
import os

def get_device_info(adapter, device_mac, use_hci=False):
    """
    특정 기기의 상세 정보를 가져옵니다.
    adapter는 MAC 주소 또는 hci 이름일 수 있습니다.
    """
    if use_hci:
        # hci 이름 직접 사용
        result = subprocess.run(["hcitool", "-i", adapter, "info", device_mac], capture_output=True, text=True)
        info = {}
        
        for line in result.stdout.split("\n"):
            line = line.strip()
            if not line:
                continue
                
            # 주요 정보 파싱
            if ": " in line:
                key, value = line.split(": ", 1)
                info[key.strip()] = value.strip()
                
        # 이름 정보가 없으면 bluetoothctl로 추가 정보 가져오기
        if "Name" not in info:
            bt_result = subprocess.run(["bluetoothctl", "info", device_mac], capture_output=True, text=True)
            for line in bt_result.stdout.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if ": " in line:
                    key, value = line.split(": ", 1)
                    # 기존 정보에 없는 경우에만 추가
                    if key.strip() not in info:
                        info[key.strip()] = value.strip()
    else:
        # 기존 방식 유지
        subprocess.run(["bluetoothctl", "select", adapter], capture_output=True)
        result = subprocess.run(["bluetoothctl", "info", device_mac], capture_output=True, text=True)
        info = {}
        
        for line in result.stdout.split("\n"):
            line = line.strip()
            if not line:
                continue
                
            # 주요 정보 파싱
            if ": " in line:
                key, value = line.split(": ", 1)
                info[key.strip()] = value.strip()
    
    return info

def scan_devices(adapter, timeout=10, use_hci=False):
    """
    지정된 어댑터로 주변 블루투스 기기를 스캔하고 목록을 반환합니다.
    [(index, device_mac, device_name), ...] 형태로 반환합니다.
    
    adapter: MAC 주소 또는 hci 이름(hci0, hci1 등)
    use_hci: True이면 adapter를 hci 이름으로 간주합니다.
    """
    print(f"[{adapter}] 에서 블루투스 기기 스캔 중...")
    
    # 스캔 시작
    scan_process = None
    scan_tool = None  # 사용 중인 스캔 도구 (bluetoothctl 또는 hcitool)
    
    try:
        if use_hci:
            # hci 이름을 직접 사용하는 경우
            # 어댑터를 초기화하고 스캔 활성화
            subprocess.run(["hciconfig", adapter, "reset"], capture_output=True)
            subprocess.run(["hciconfig", adapter, "up"], capture_output=True)
            
            # hcitool scan을 background에서 실행
            scan_process = subprocess.Popen(
                ["hcitool", "-i", adapter, "scan"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            scan_tool = "hcitool"
        else:
            # 기존 방식 - bluetoothctl 사용
            subprocess.run(["bluetoothctl", "select", adapter], capture_output=True)
            
            # bluetoothctl scan on을 background에서 실행
            scan_process = subprocess.Popen(
                ["bluetoothctl", "scan", "on"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            scan_tool = "bluetoothctl"
        
        # 발견된 기기를 저장할 딕셔너리 (MAC 주소 -> 이름)
        discovered_devices = {}
        stop_event = threading.Event()
        
        # 스레드 간 공유할 변수들
        shared_data = {
            'remaining': timeout,
            'new_device_found': False
        }
        
        # 스캔 중 발견된 기기를 실시간으로 가져오는 함수
        def update_devices():
            while not stop_event.is_set():
                try:
                    if scan_tool == "bluetoothctl":
                        # bluetoothctl devices 명령으로 기기 목록 가져오기
                        result = subprocess.run(["bluetoothctl", "devices"], 
                                              capture_output=True, text=True)
                        lines = result.stdout.strip().split("\n")
                        
                        # 새로운 기기 목록 생성
                        new_devices = {}
                        for line in lines:
                            if not line.strip():
                                continue
                            
                            parts = line.split(" ", 2)
                            if len(parts) >= 3 and parts[0] == "Device":
                                mac = parts[1]
                                name = parts[2]
                                new_devices[mac] = name
                            elif len(parts) == 2 and parts[0] == "Device":
                                mac = parts[1]
                                new_devices[mac] = "(No Name)"
                    else:  # hcitool
                        # hcitool scan 결과를 처리
                        result = subprocess.run(["hcitool", "-i", adapter, "scan"], 
                                              capture_output=True, text=True, timeout=2)
                        lines = result.stdout.strip().split("\n")
                        
                        # 새로운 기기 목록 생성
                        new_devices = {}
                        for line in lines:
                            if not line.strip() or line.startswith("Scanning"):
                                continue
                            
                            parts = line.strip().split("\t")
                            if len(parts) >= 2:
                                mac = parts[0].strip()
                                name = parts[1].strip() if len(parts) > 1 else "(No Name)"
                                new_devices[mac] = name
                    
                    # 새 기기 발견 시 출력
                    for mac, name in new_devices.items():
                        if mac not in discovered_devices:
                            sys.stdout.write(f"\r새 기기 발견: {name} ({mac})              \n")
                            sys.stdout.write(f"\r스캔 중... 남은 시간: {shared_data['remaining']}초  ")
                            sys.stdout.flush()
                            shared_data['new_device_found'] = True
                    
                    # 발견된 기기 목록 갱신
                    discovered_devices.update(new_devices)
                    
                    time.sleep(0.5)
                except Exception as e:
                    # 오류 발생 시 무시하고 계속 진행
                    pass
        
        # 백그라운드 스레드로 기기 업데이트 시작
        bg_thread = threading.Thread(target=update_devices)
        bg_thread.daemon = True
        bg_thread.start()
        
        # 카운트다운 표시하면서 지정된 시간 동안 스캔
        while shared_data['remaining'] > 0:
            if not shared_data['new_device_found']:  # 새 기기가 발견되지 않은 경우에만 출력
                sys.stdout.write(f"\r스캔 중... 남은 시간: {shared_data['remaining']}초  ")
                sys.stdout.flush()
            shared_data['new_device_found'] = False  # 플래그 초기화
            time.sleep(1)
            shared_data['remaining'] -= 1
        
        # 스레드 중지
        stop_event.set()
        
        # 스레드가 완전히 종료될 때까지 짧게 대기
        time.sleep(0.5)
        
        sys.stdout.write("\r스캔 완료!                                     \n")
        sys.stdout.flush()
        
        # 각 기기의 실제 이름 가져오기 (상세 정보 쿼리)
        print("기기 정보 확인 중...")
        devices_with_names = []
        idx = 0
        for mac, raw_name in discovered_devices.items():
            # 기기 정보 가져오기를 시도
            try:
                device_info = get_device_info(adapter, mac, use_hci)
                # 이름이 'Name' 필드에 있으면 사용, 없으면 'Alias' 필드, 둘 다 없으면 초기 이름 사용
                name = device_info.get("Name", device_info.get("Alias", raw_name))
                
                # 여전히 이름이 없으면 MAC 주소로 표시
                if name == "(No Name)" or name == mac:
                    name = f"장치 {idx+1}"
                    
                devices_with_names.append((idx, mac, name))
                idx += 1
            except Exception as e:
                # 정보 가져오기 실패 시 원래 이름 사용
                devices_with_names.append((idx, mac, raw_name))
                idx += 1
        
        print(f"총 {len(devices_with_names)}개 기기 발견")
        return devices_with_names
        
    finally:
        # 스캔 중지 및 정리
        print("스캔 중지 중...")
        
        # 스캔 프로세스 종료
        if scan_process:
            try:
                if scan_tool == "bluetoothctl":
                    # bluetoothctl scan off 실행
                    subprocess.run(["bluetoothctl", "scan", "off"], 
                                 capture_output=True, timeout=3)
                else:  # hcitool
                    # hcitool 프로세스 종료만으로 충분
                    pass
                
                # 그래도 실행 중이면 강제 종료
                if scan_process.poll() is None:  # 프로세스가 여전히 실행 중인지 확인
                    scan_process.terminate()
                    time.sleep(0.5)
                    if scan_process.poll() is None:  # 여전히 종료되지 않았다면
                        scan_process.kill()  # 강제 종료
            except Exception as e:
                print(f"스캔 중지 중 오류: {e}")

def connect_device(adapter, device_mac, use_hci=False):
    """
    지정된 어댑터를 사용하여 블루투스 기기에 연결합니다.
    
    adapter: MAC 주소 또는 hci 이름(hci0, hci1 등)
    use_hci: True이면 adapter를 hci 이름으로 간주합니다.
    """
    print(f"[{adapter}] 에서 [{device_mac}] 에 연결 시도 중...")
    
    if use_hci:
        # hci 이름으로 직접 연결
        # 명확한 어댑터 지정을 위해 BLUETOOTH_ADAPTER 환경 변수 설정
        env = os.environ.copy()
        env["BLUETOOTH_ADAPTER"] = adapter
        
        try:
            # 블루투스 연결
            print(f"[{device_mac}] 연결 시도 중 (hci 모드)...")
            
            # bluetoothctl로 연결, 어댑터 선택은 필요 없음 (hci 이름으로 직접 지정)
            subprocess.run(["bluetoothctl", "remove", device_mac], 
                          capture_output=True, timeout=5, env=env)
            time.sleep(1)
            
            # 신뢰 및 페어링
            subprocess.run(["bluetoothctl", "agent", "on"], 
                          capture_output=True, timeout=5, env=env)
            
            trust_result = subprocess.run(["bluetoothctl", "trust", device_mac], 
                                         capture_output=True, text=True, timeout=5, env=env)
            
            if "trusted" in trust_result.stdout.lower():
                print(f"[{device_mac}] 신뢰 설정 완료")
            
            pair_result = subprocess.run(["bluetoothctl", "pair", device_mac], 
                                        capture_output=True, text=True, timeout=15, env=env)
            
            if "successful" in pair_result.stdout.lower() or "already paired" in pair_result.stdout.lower():
                print(f"[{device_mac}] 페어링 완료")
            
            time.sleep(2)
            
            connect_result = subprocess.run(["bluetoothctl", "connect", device_mac], 
                                           capture_output=True, text=True, timeout=15, env=env)
            
            if "successful" in connect_result.stdout.lower():
                print(f"[{device_mac}] 연결 성공!")
                return True
            else:
                print(f"[{device_mac}] 연결 실패. 출력: {connect_result.stdout}")
                
                # 연결 실패 후 수동 확인
                time.sleep(2)
                if check_device_connected(adapter, device_mac, use_hci):
                    print(f"[{device_mac}] 연결 상태 확인: 실제로 연결되어 있습니다!")
                    return True
                    
                return False
        except subprocess.TimeoutExpired:
            print(f"[{device_mac}] 연결 시간이 초과되었습니다. (15초)")
            # 타임아웃 후 연결 상태 확인
            if check_device_connected(adapter, device_mac, use_hci):
                print(f"[{device_mac}] 타임아웃이 발생했지만 실제로 연결되어 있습니다!")
                return True
            return False
    else:
        # 기존 방식 - bluetoothctl의 select 명령 사용
        # 어댑터 선택
        subprocess.run(["bluetoothctl", "select", adapter], capture_output=True)
        
        try:
            # 이전 연결 해제 (연결 문제가 있을 경우 도움이 될 수 있음)
            subprocess.run(["bluetoothctl", "disconnect", device_mac], capture_output=True, timeout=5)
            time.sleep(1)
            
            # 신뢰 설정 (이 단계가 연결 안정성을 높일 수 있음)
            trust_result = subprocess.run(["bluetoothctl", "trust", device_mac], 
                                         capture_output=True, text=True, timeout=5)
            
            if "trusted" in trust_result.stdout.lower():
                print(f"[{device_mac}] 신뢰 설정 완료")
            
            # 페어링 시도 
            print(f"[{device_mac}] 페어링 시도 중...")
            pair_result = subprocess.run(["bluetoothctl", "pair", device_mac], 
                                        capture_output=True, text=True, timeout=15)
            
            # 성공 또는 이미 페어링된 경우
            if "successful" in pair_result.stdout.lower() or "already paired" in pair_result.stdout.lower():
                print(f"[{device_mac}] 페어링 완료")
            
            # 잠시 대기 (연결 안정화)
            time.sleep(2)
            
            # 연결 시도
            print(f"[{device_mac}] 연결 시도 중...")
            connect_result = subprocess.run(["bluetoothctl", "connect", device_mac], 
                                           capture_output=True, text=True, timeout=15)
            
            # 성공 여부 확인
            if "successful" in connect_result.stdout.lower():
                print(f"[{device_mac}] 연결 성공!")
                return True
            else:
                # 실패했을 경우 정보 출력
                print(f"[{device_mac}] 연결 실패. 출력: {connect_result.stdout}")
                
                # 연결 실패 후 수동 확인 (연결은 성공했지만 메시지가 다를 수 있음)
                time.sleep(2)
                if check_device_connected(adapter, device_mac):
                    print(f"[{device_mac}] 연결 상태 확인: 실제로 연결되어 있습니다!")
                    return True
                    
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[{device_mac}] 연결 시간이 초과되었습니다. (15초)")
            # 타임아웃 후 연결 상태 확인
            if check_device_connected(adapter, device_mac):
                print(f"[{device_mac}] 타임아웃이 발생했지만 실제로 연결되어 있습니다!")
                return True
            return False

def disconnect_device(adapter, device_mac, use_hci=False):
    """
    지정된 어댑터와 기기의 연결을 해제합니다.
    
    adapter: MAC 주소 또는 hci 이름(hci0, hci1 등)
    use_hci: True이면 adapter를 hci 이름으로 간주합니다.
    """
    print(f"[{adapter}] 에서 [{device_mac}] 연결 해제 중...")
    
    if use_hci:
        # hci 이름 직접 사용
        env = os.environ.copy()
        env["BLUETOOTH_ADAPTER"] = adapter
        
        # 연결 해제
        disconnect_result = subprocess.run(["bluetoothctl", "disconnect", device_mac], 
                                          capture_output=True, text=True, timeout=10, env=env)
    else:
        # 어댑터 선택
        subprocess.run(["bluetoothctl", "select", adapter], capture_output=True)
        
        # 연결 해제
        disconnect_result = subprocess.run(["bluetoothctl", "disconnect", device_mac], 
                                          capture_output=True, text=True, timeout=10)
    
    if "successful" in disconnect_result.stdout.lower() or "not connected" in disconnect_result.stdout.lower():
        print(f"[{device_mac}] 연결 해제 성공!")
        return True
    else:
        print(f"[{device_mac}] 연결 해제 실패. 출력: {disconnect_result.stdout}")
        return False

def get_connected_devices(adapter, use_hci=False):
    """
    현재 어댑터에 연결된 모든 기기 목록을 반환합니다.
    
    adapter: MAC 주소 또는 hci 이름(hci0, hci1 등)
    use_hci: True이면 adapter를 hci 이름으로 간주합니다.
    """
    if use_hci:
        # hci 이름 직접 사용
        env = os.environ.copy()
        env["BLUETOOTH_ADAPTER"] = adapter
        
        result = subprocess.run(["bluetoothctl", "paired-devices"], 
                               capture_output=True, text=True, env=env)
    else:
        # 어댑터 선택
        subprocess.run(["bluetoothctl", "select", adapter], capture_output=True)
        
        # 연결된 기기 확인
        result = subprocess.run(["bluetoothctl", "paired-devices"], 
                               capture_output=True, text=True)
    
    devices = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        
        parts = line.split(" ", 2)
        if len(parts) >= 3 and parts[0] == "Device":
            mac = parts[1]
            name = parts[2]
            
            # 실제 연결 상태 확인
            if check_device_connected(adapter, mac, use_hci):
                devices.append((mac, name))
    
    return devices

def disconnect_all_devices(adapter, use_hci=False):
    """
    현재 어댑터에 연결된 모든 기기의 연결을 해제합니다.
    
    adapter: MAC 주소 또는 hci 이름(hci0, hci1 등)
    use_hci: True이면 adapter를 hci 이름으로 간주합니다.
    """
    connected_devices = get_connected_devices(adapter, use_hci)
    
    success_count = 0
    for mac, name in connected_devices:
        print(f"연결 해제 중: {name} ({mac})")
        if disconnect_device(adapter, mac, use_hci):
            success_count += 1
    
    return success_count

def check_device_connected(adapter, device_mac, use_hci=False):
    """
    특정 기기가 어댑터에 연결되어 있는지 확인합니다.
    
    adapter: MAC 주소 또는 hci 이름(hci0, hci1 등)
    use_hci: True이면 adapter를 hci 이름으로 간주합니다.
    """
    if use_hci:
        # hci 이름 직접 사용
        env = os.environ.copy()
        env["BLUETOOTH_ADAPTER"] = adapter
        
        info_result = subprocess.run(["bluetoothctl", "info", device_mac], 
                                    capture_output=True, text=True, env=env)
    else:
        # 어댑터 선택
        subprocess.run(["bluetoothctl", "select", adapter], capture_output=True)
        
        # 기기 정보 확인
        info_result = subprocess.run(["bluetoothctl", "info", device_mac], 
                                    capture_output=True, text=True)
    
    # "Connected: yes"가 출력에 있는지 확인
    for line in info_result.stdout.strip().split("\n"):
        if line.strip().startswith("Connected:"):
            status = line.split(":", 1)[1].strip().lower()
            return status == "yes"
    
    return False

if __name__ == "__main__":
    # 단독 실행 시 테스트 코드
    if len(sys.argv) > 1:
        adapter_mac = sys.argv[1]
        print(f"어댑터 {adapter_mac}에서 스캔 테스트 중...")
        
        devices = scan_devices(adapter_mac, timeout=5)
        
        if not devices:
            print("발견된 블루투스 기기가 없습니다.")
            sys.exit(0)
            
        print("\n발견된 블루투스 기기:")
        for i, mac, name in devices:
            print(f"{i}. {name} - {mac}")
            
        # 연결된 기기 확인
        print("\n현재 연결된 기기:")
        connected = get_connected_devices(adapter_mac)
        for mac, name in connected:
            print(f"* {name} - {mac}") 