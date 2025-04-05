#!/usr/bin/env python3
import os
import sys
import argparse

# 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 데몬 함수 임포트
from blehub.daemon.process import (
    start_daemon,
    stop_daemon,
    restart_daemon,
    status_daemon,
    run_setup,
    setup_recv_bluetooth,
    setup_send_bluetooth,
    add_recv_device,
    remove_recv_device,
    set_target_device,
    list_recv_devices
)

# 메뉴 함수 임포트
from blehub.menu.terminal import (
    show_terminal_menu,
    show_recv_devices_menu,
    show_target_device_menu
)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="BLE-HUB 데몬 관리")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--start", action="store_true", help="데몬 시작")
    group.add_argument("--stop", action="store_true", help="데몬 중지")
    group.add_argument("--restart", action="store_true", help="데몬 재시작")
    group.add_argument("--status", action="store_true", help="데몬 상태 확인")
    group.add_argument("--setup", action="store_true", help="설정 실행")
    group.add_argument("--menu", action="store_true", help="터미널 메뉴 표시")
    group.add_argument("--setup-recv", action="store_true", help="수신용 블루투스 설정")
    group.add_argument("--setup-send", action="store_true", help="송신용 블루투스 설정")
    group.add_argument("--recv-devices", action="store_true", help="수신 디바이스 관리")
    group.add_argument("--target-device", action="store_true", help="송신 디바이스 설정")
    group.add_argument("--add-recv", nargs=2, metavar=('NAME', 'MAC'), help="수신 디바이스 추가 (이름, MAC 주소)")
    group.add_argument("--remove-recv", type=int, metavar='INDEX', help="수신 디바이스 제거 (인덱스)")
    group.add_argument("--set-target", nargs=2, metavar=('NAME', 'MAC'), help="송신 디바이스 설정 (이름, MAC 주소)")
    group.add_argument("--list-recv", action="store_true", help="수신 디바이스 목록 조회")
    
    args = parser.parse_args()
    
    # 명령 실행
    if args.start:
        start_daemon()
    elif args.stop:
        stop_daemon()
    elif args.restart:
        restart_daemon()
    elif args.status:
        status_daemon()
    elif args.setup:
        run_setup()
    elif args.setup_recv:
        setup_recv_bluetooth()
    elif args.setup_send:
        setup_send_bluetooth()
    elif args.recv_devices:
        show_recv_devices_menu()
    elif args.target_device:
        show_target_device_menu()
    elif args.add_recv:
        name, mac = args.add_recv
        if add_recv_device(name, mac):
            print(f"수신 디바이스 '{name}' ({mac})가 추가되었습니다.")
        else:
            print("수신 디바이스 추가에 실패했습니다.")
    elif args.remove_recv is not None:
        index = args.remove_recv - 1  # 0-based 인덱스로 변환
        if remove_recv_device(index):
            print(f"수신 디바이스(인덱스: {args.remove_recv})가 제거되었습니다.")
        else:
            print("수신 디바이스 제거에 실패했습니다.")
    elif args.set_target:
        name, mac = args.set_target
        if set_target_device(name, mac):
            print(f"송신 디바이스가 '{name}' ({mac})로 설정되었습니다.")
        else:
            print("송신 디바이스 설정에 실패했습니다.")
    elif args.list_recv:
        devices = list_recv_devices()
        if devices:
            print("수신 디바이스 목록:")
            for i, device in enumerate(devices, 1):
                print(f"{i}. {device.get('name', 'Unknown')} - {device.get('mac')}")
        else:
            print("등록된 수신 디바이스가 없습니다.")
    elif args.menu:
        show_terminal_menu()
    else:
        # 아무 인자도 없으면 터미널 메뉴 표시
        show_terminal_menu()

if __name__ == "__main__":
    main()
