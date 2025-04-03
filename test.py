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

def main():
    print("===== 블루투스 어댑터 목록을 가져옵니다. =====\n\n")
    adapters = list_bluetooth_adapters()

    if not adapters:
        print("블루투스 어댑터가 발견되지 않았습니다. USB 동글을 연결하거나, 드라이버를 확인하세요.")
        return

    print("===== 발견된 블루투스 어댑터 =====")
    print("--------------------------------")
    for i, addr, info in adapters:
        print(f"{i}. {addr} - {info}")
    print("--------------------------------\n\n")


    print("===== 수신용, 송신용 선택 =====\n")
    # 수신용, 송신용 선택
    while True:
        print("--------------------------------")
        recv_idx = input("수신용 블루투스로 지정할 번호를 입력하세요: ")
        send_idx = input("송신용 블루투스로 지정할 번호를 입력하세요: ")
        print("--------------------------------\n\n")
        try:
            recv_idx = int(recv_idx)
            send_idx = int(send_idx)
            if recv_idx == send_idx:
                print("수신용과 송신용 번호가 같습니다. 다시 입력해주세요.\n")
                continue
            if 0 <= recv_idx < len(adapters) and 0 <= send_idx < len(adapters):
                break
            else:
                print("입력한 번호가 범위를 벗어났습니다. 다시 입력해주세요.\n")
        except ValueError:
            print("유효한 숫자가 아닙니다. 다시 입력해주세요.\n")

    # 선택한 어댑터 
    recv_adapter = adapters[recv_idx]
    send_adapter = adapters[send_idx]

    print("===== 선택 결과 =====\n")
    print("--------------------------------")
    print(f" - 수신용: {recv_adapter[1]} ({recv_adapter[2]})")
    print(f" - 송신용: {send_adapter[1]} ({send_adapter[2]})")
    print("--------------------------------\n")
    # 각각 setup 수행
    # # 여기서는 adapter_addr 만 넘겨주는데,
    # # hciX 실제 이름이 필요하다면 hciconfig -- all 로부터 역매핑 로직을 추가해야 함.
    # setup_adapter(recv_adapter[1])
    # setup_adapter(send_adapter[1])


if __name__ == "__main__":
    main()
