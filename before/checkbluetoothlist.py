#!/usr/bin/env python3
import subprocess
import re

def get_adapter_hci_names():
    """hciconfig 명령을 실행하여 MAC 주소와 hci 이름 매핑을 반환합니다."""
    try:
        result = subprocess.run(["hciconfig", "-a"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        
        hci_map = {}
        current_hci = None
        current_mac = None
        
        for line in lines:
            # hci 이름 찾기 (예: "hci0:")
            hci_match = re.match(r'^(hci\d+):', line)
            if hci_match:
                current_hci = hci_match.group(1)
                continue
            
            # MAC 주소 찾기 (예: "BD Address: 00:1A:7D:DA:71:13")
            mac_match = re.search(r'BD Address:\s+([0-9A-F:]{17})', line)
            if mac_match and current_hci:
                current_mac = mac_match.group(1)
                hci_map[current_mac.upper()] = current_hci
                
        return hci_map
    except Exception as e:
        print(f"hciconfig 실행 중 오류: {e}")
        return {}

def list_bluetooth_adapters():
    """
    'bluetoothctl list' 명령 결과를 파싱해서,
    [(index, hci_name, adapter_addr, info_string), ...] 형태로 반환.
    모든 블루투스 어댑터 정보를 가져옵니다.
    """
    # bluetoothctl list 예시 출력:
    # Controller 00:1A:7D:DA:71:13 raspberrypi [default]
    # Controller AA:BB:CC:DD:EE:FF usb-dongle
    cmd = ["bluetoothctl", "list"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")

    # MAC 주소와 hci 이름 매핑 가져오기
    hci_map = get_adapter_hci_names()

    adapters = []
    idx = 0
    for line in lines:
        line = line.strip()
        if line.startswith("Controller"):
            # "Controller AA:BB:CC:DD:EE:FF <n> ..." 형태
            # split(" ", 2)는 공백을 기준으로 최대 3개 부분으로만 나눔:
            # 1. "Controller" 2. MAC주소 3. 나머지 전체 텍스트
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                # parts[0] = "Controller"
                # parts[1] = "AA:BB:CC:DD:EE:FF"
                # parts[2] = "<adapter_name> [default]" (이후 더 있을 수도)
                adapter_addr = parts[1]
                adapter_rest = parts[2]  # 이름, [default] 등
                
                # MAC 주소에 해당하는 hci 이름 찾기
                hci_name = hci_map.get(adapter_addr.upper(), "알 수 없음")
                
                # 정보에 hci 이름 추가
                full_info = f"{hci_name} | {adapter_rest}"
                
                adapters.append((idx, hci_name, adapter_addr, full_info))
                idx += 1

    return adapters

if __name__ == "__main__":
    # 단독 실행 시 테스트 코드
    adapters = list_bluetooth_adapters()
    if not adapters:
        print("블루투스 어댑터가 발견되지 않았습니다.")
    else:
        print("=== 발견된 블루투스 어댑터 ===")
        for i, hci, addr, info in adapters:
            print(f"{i}. {hci} - {addr} - {info}")
