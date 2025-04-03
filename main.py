#!/usr/bin/env python3
import sys
import os

# 자체 모듈 import
from checkbluetoothlist import list_bluetooth_adapters
from bluetooth_scan import scan_devices, connect_device
from config_manager import save_config, load_config, config_exists
from daemon_control import start_relay_daemon

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
    
    # 수신용 어댑터로 기기 스캔
    print("\n===== 주변 블루투스 기기 스캔 =====\n")
    scan_time = int(input("스캔 시간(초)을 입력하세요 (기본 10초): ") or "10")
    devices = scan_devices(recv_adapter[1], timeout=scan_time)
    
    if not devices:
        print("발견된 블루투스 기기가 없습니다.")
        return
    
    print("\n===== 발견된 블루투스 기기 =====")
    print("--------------------------------")
    for i, mac, name in devices:
        print(f"{i}. {mac} - {name}")
    print("--------------------------------\n")
    
    # 연결할 기기 선택
    while True:
        device_idx = input("연결할 마우스/기기 번호를 입력하세요: ")
        try:
            device_idx = int(device_idx)
            if 0 <= device_idx < len(devices):
                break
            else:
                print("입력한 번호가 범위를 벗어났습니다. 다시 입력해주세요.")
        except ValueError:
            print("유효한 숫자가 아닙니다. 다시 입력해주세요.")
    
    # 선택한 기기에 연결
    selected_device = devices[device_idx]
    print(f"\n{selected_device[2]}({selected_device[1]})에 연결을 시도합니다...")
    
    # 연결 시도
    connect_success = connect_device(recv_adapter[1], selected_device[1])
    
    if connect_success:
        print("\n===== 연결 성공 =====")
        print(f"수신용 어댑터({recv_adapter[1]})와 {selected_device[2]}({selected_device[1]})가 연결되었습니다.")
        
        # 설정 저장
        try:
            save_config(recv_adapter[1], send_adapter[1], selected_device[1])
            print("\n설정이 저장되었습니다.")
            
            # 사용자에게 데몬 시작 여부 묻기
            start_daemon = input("\n블루투스 릴레이 데몬을 시작하시겠습니까? (y/n): ").lower()
            if start_daemon == 'y':
                if start_relay_daemon():
                    print("\n설정이 완료되었습니다! 시스템이 계속 실행됩니다.")
                else:
                    print("\n데몬 시작 실패. 수동으로 시작하려면 다음 명령을 실행하세요:")
                    print(f"  python3 {os.path.join(os.path.dirname(__file__), 'ble_relay.py')} start")
            else:
                print("\n데몬을 시작하지 않았습니다. 나중에 다음 명령으로 시작할 수 있습니다:")
                print(f"  python3 {os.path.join(os.path.dirname(__file__), 'ble_relay.py')} start")
                
        except Exception as e:
            print(f"\n설정 저장 오류: {e}")
            print("설정을 저장할 수 없습니다. 수동으로 릴레이를 설정해야 합니다.")
    else:
        print("\n===== 연결 실패 =====")
        print("연결에 실패했습니다. 다시 시도하거나 기기 설정을 확인해보세요.")


if __name__ == "__main__":
    main()
