#!/usr/bin/env python3
import subprocess
import time
import sys
import threading
import os

def get_device_info(adapter_addr, device_mac):
    """
    특정 기기의 상세 정보를 가져옵니다.
    """
    subprocess.run(["bluetoothctl", "select", adapter_addr], capture_output=True)
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

def scan_devices(adapter_addr, timeout=10):
    """
    지정된 어댑터로 주변 블루투스 기기를 스캔하고 목록을 반환합니다.
    [(index, device_mac, device_name), ...] 형태로 반환합니다.
    """
    print(f"[{adapter_addr}] 에서 블루투스 기기 스캔 중...")
    
    # 스캔 시작
    subprocess.run(["bluetoothctl", "select", adapter_addr], capture_output=True)
    
    # 스캔 시작 - 대화형 모드 대신 비동기로 실행
    scan_process = None
    try:
        # bluetoothctl scan on을 background에서 실행
        scan_process = subprocess.Popen(
            ["bluetoothctl", "scan", "on"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        
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
                device_info = get_device_info(adapter_addr, mac)
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
        
        # bluetoothctl 프로세스 종료
        if scan_process:
            try:
                # 먼저 bluetoothctl scan off 실행
                subprocess.run(["bluetoothctl", "scan", "off"], 
                              capture_output=True, timeout=3)
                
                # 그래도 실행 중이면 강제 종료
                if scan_process.poll() is None:  # 프로세스가 여전히 실행 중인지 확인
                    scan_process.terminate()
                    time.sleep(0.5)
                    if scan_process.poll() is None:  # 여전히 종료되지 않았다면
                        scan_process.kill()  # 강제 종료
            except Exception as e:
                print(f"스캔 중지 중 오류: {e}")

def connect_device(adapter_addr, device_mac):
    """
    지정된 어댑터를 사용하여 블루투스 기기에 연결합니다.
    """
    print(f"[{adapter_addr}] 에서 [{device_mac}] 에 연결 시도 중...")
    
    # 어댑터 선택
    subprocess.run(["bluetoothctl", "select", adapter_addr], capture_output=True)
    
    try:
        # 페어링 시도
        pair_result = subprocess.run(["bluetoothctl", "pair", device_mac], capture_output=True, text=True, timeout=15)
        
        # 연결 시도
        connect_result = subprocess.run(["bluetoothctl", "connect", device_mac], capture_output=True, text=True, timeout=15)
        
        if "successful" in connect_result.stdout.lower():
            print(f"[{device_mac}] 연결 성공!")
            return True
        else:
            print(f"[{device_mac}] 연결 실패. 출력: {connect_result.stdout}")
            return False
    except subprocess.TimeoutExpired:
        print(f"[{device_mac}] 연결 시간이 초과되었습니다. (15초)")
        return False

def disconnect_device(adapter_addr, device_mac):
    """
    지정된 어댑터와 기기의 연결을 해제합니다.
    """
    print(f"[{adapter_addr}] 에서 [{device_mac}] 연결 해제 중...")
    
    # 어댑터 선택
    subprocess.run(["bluetoothctl", "select", adapter_addr], capture_output=True)
    
    # 연결 해제
    disconnect_result = subprocess.run(["bluetoothctl", "disconnect", device_mac], 
                                      capture_output=True, text=True, timeout=10)
    
    if "successful" in disconnect_result.stdout.lower() or "not connected" in disconnect_result.stdout.lower():
        print(f"[{device_mac}] 연결 해제 성공!")
        return True
    else:
        print(f"[{device_mac}] 연결 해제 실패. 출력: {disconnect_result.stdout}")
        return False

def get_connected_devices(adapter_addr):
    """
    현재 어댑터에 연결된 모든 기기 목록을 반환합니다.
    """
    # 어댑터 선택
    subprocess.run(["bluetoothctl", "select", adapter_addr], capture_output=True)
    
    # 페어링된 기기 목록
    paired_result = subprocess.run(["bluetoothctl", "paired-devices"], 
                                  capture_output=True, text=True)
    
    connected_devices = []
    for line in paired_result.stdout.strip().split("\n"):
        if not line:
            continue
            
        # Device MAC NAME 형태로 파싱
        parts = line.split(" ", 2)
        if len(parts) >= 2:
            device_mac = parts[1]
            
            # 연결 상태 확인
            if check_device_connected(adapter_addr, device_mac):
                device_name = parts[2] if len(parts) >= 3 else "(No Name)"
                connected_devices.append((device_mac, device_name))
    
    return connected_devices

def disconnect_all_devices(adapter_addr):
    """
    해당 어댑터에 연결된 모든 기기의 연결을 해제합니다.
    """
    connected_devices = get_connected_devices(adapter_addr)
    
    if not connected_devices:
        print(f"[{adapter_addr}] 에 연결된 기기가 없습니다.")
        return True
    
    print(f"[{adapter_addr}] 에 연결된 {len(connected_devices)}개 기기 연결 해제 중...")
    
    success = True
    for device_mac, device_name in connected_devices:
        print(f"- {device_name}({device_mac}) 연결 해제 중...")
        if not disconnect_device(adapter_addr, device_mac):
            success = False
    
    return success

def check_device_connected(adapter_addr, device_mac):
    """
    기기가 현재 연결되어 있는지 확인합니다.
    """
    subprocess.run(["bluetoothctl", "select", adapter_addr], capture_output=True)
    result = subprocess.run(["bluetoothctl", "info", device_mac], capture_output=True, text=True)
    return "Connected: yes" in result.stdout

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