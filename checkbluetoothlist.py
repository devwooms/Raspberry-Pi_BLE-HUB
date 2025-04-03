#!/usr/bin/env python3
import subprocess

def list_bluetooth_adapters():
    """
    'bluetoothctl list' 명령 결과를 파싱해서,
    [(index, hci_name, info_string), ...] 형태로 반환.
    모든 블루투스 어댑터 정보를 가져옵니다.
    """
    # bluetoothctl list 예시 출력:
    # Controller 00:1A:7D:DA:71:13 raspberrypi [default]
    # Controller AA:BB:CC:DD:EE:FF usb-dongle
    cmd = ["bluetoothctl", "list"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")

    adapters = []
    idx = 0
    for line in lines:
        line = line.strip()
        if line.startswith("Controller"):
            # "Controller AA:BB:CC:DD:EE:FF <name> ..." 형태
            # split(" ", 2)는 공백을 기준으로 최대 3개 부분으로만 나눔:
            # 1. "Controller" 2. MAC주소 3. 나머지 전체 텍스트
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                # parts[0] = "Controller"
                # parts[1] = "AA:BB:CC:DD:EE:FF"
                # parts[2] = "<adapter_name> [default]" (이후 더 있을 수도)
                adapter_addr = parts[1]
                adapter_rest = parts[2]  # 이름, [default] 등
                # hciX 이름을 알기 위해 hciconfig를 통해 addr → hci이름 매핑도 가능
                # 여기선 단순히 "adapter_addr + (optional)adapter_rest"로 보여줌
                adapters.append((idx, adapter_addr, adapter_rest))
                idx += 1

    return adapters

if __name__ == "__main__":
    # 단독 실행 시 테스트 코드
    adapters = list_bluetooth_adapters()
    if not adapters:
        print("블루투스 어댑터가 발견되지 않았습니다.")
    else:
        print("=== 발견된 블루투스 어댑터 ===")
        for i, addr, info in adapters:
            print(f"{i}. {addr} - {info}")
