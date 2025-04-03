#!/usr/bin/env python3
import subprocess
import time

def scan_devices(adapter_addr, timeout=10):
    """
    지정된 어댑터로 주변 블루투스 기기를 스캔하고 목록을 반환합니다.
    [(index, device_mac, device_name), ...] 형태로 반환합니다.
    """
    print(f"[{adapter_addr}] 에서 블루투스 기기 스캔 중... ({timeout}초)")
    
    # 스캔 시작
    subprocess.run(["bluetoothctl", "select", adapter_addr], capture_output=True)
    subprocess.run(["bluetoothctl", "scan", "on"], capture_output=False, shell=True, start_new_session=True)
    
    # 지정된 시간 동안 스캔
    time.sleep(timeout)
    
    # 스캔 중지
    subprocess.run(["bluetoothctl", "scan", "off"], capture_output=True)
    
    # 기기 목록 가져오기
    result = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")
    
    devices = []
    idx = 0
    for line in lines:
        line = line.strip()
        if line.startswith("Device"):
            parts = line.split(" ", 2)  # "Device MAC 이름" 형태로 분리
            if len(parts) >= 3:
                device_mac = parts[1]
                device_name = parts[2]
                devices.append((idx, device_mac, device_name))
                idx += 1
            elif len(parts) == 2:
                # 이름이 없는 경우
                device_mac = parts[1]
                devices.append((idx, device_mac, "(No Name)"))
                idx += 1
    
    return devices

def connect_device(adapter_addr, device_mac):
    """
    지정된 어댑터를 사용하여 블루투스 기기에 연결합니다.
    """
    print(f"[{adapter_addr}] 에서 [{device_mac}] 에 연결 시도 중...")
    
    # 어댑터 선택
    subprocess.run(["bluetoothctl", "select", adapter_addr], capture_output=True)
    
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
    import sys
    if len(sys.argv) > 1:
        adapter_mac = sys.argv[1]
        print(f"어댑터 {adapter_mac}에서 스캔 테스트 중...")
        
        devices = scan_devices(adapter_mac, timeout=5)
        
        if not devices:
            print("발견된 블루투스 기기가 없습니다.")
            sys.exit(0)
            
        print("\n발견된 블루투스 기기:")
        for i, mac, name in devices:
            print(f"{i}. {mac} - {name}")
            
        # 연결된 기기 확인
        print("\n현재 연결된 기기:")
        connected = get_connected_devices(adapter_mac)
        for mac, name in connected:
            print(f"* {mac} - {name}") 