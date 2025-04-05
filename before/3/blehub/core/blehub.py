#!/usr/bin/env python3
import os
import sys
import argparse

from blehub_new.utils.logger import logger
from blehub_new.daemon.manager import (
    start_daemon,
    stop_daemon,
    restart_daemon,
    status_daemon
)
from blehub_new.bluetooth.setup import (
    run_setup,
    setup_recv_bluetooth,
    setup_send_bluetooth,
    list_recv_devices,
    add_recv_device,
    remove_recv_device,
    set_target_device
)
from blehub_new.bluetooth.scanner import (
    list_bluetooth_modules,
    select_bluetooth_module,
    select_bluetooth_interface,
    select_bluetooth_device
)
from blehub_new.menu.terminal_menu import (
    show_terminal_menu,
    show_recv_devices_menu,
    show_target_device_menu
)

"""
BLE-HUB 코어 모듈

블루투스 중계 데몬 애플리케이션의 메인 진입점과 CLI 인터페이스를 제공합니다.
"""

def parse_args():
    """명령행 인자를 파싱합니다
    
    Returns:
        argparse.Namespace: 파싱된 인자
    """
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
    group.add_argument("--scan-bluetooth", action="store_true", help="블루투스 장치 검색")
    group.add_argument("--scan-add-recv", action="store_true", help="블루투스 장치 검색 후 수신 디바이스 추가")
    group.add_argument("--scan-set-target", action="store_true", help="블루투스 장치 검색 후 송신 디바이스 설정")
    group.add_argument("--list-modules", action="store_true", help="시스템 블루투스 모듈 목록 표시")
    group.add_argument("--select-module", action="store_true", help="블루투스 모듈 선택")
    
    return parser.parse_args()

def main():
    """메인 함수"""
    args = parse_args()
    
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
    elif args.scan_bluetooth:
        # 블루투스 검색 실행
        interface = select_bluetooth_interface()
        if interface:
            print(f"인터페이스 {interface['id']}({interface['name']})를 사용하여 장치를 검색합니다.")
            select_bluetooth_device(interface['id'])
    elif args.scan_add_recv:
        # 블루투스 검색 후 수신 디바이스 추가
        from blehub_new.bluetooth.setup import get_bluetooth_setup
        setup = get_bluetooth_setup()
        setup.setup_recv_device()
    elif args.scan_set_target:
        # 블루투스 검색 후 송신 디바이스 설정
        from blehub_new.bluetooth.setup import get_bluetooth_setup
        setup = get_bluetooth_setup()
        setup.setup_target_device()
    elif args.list_modules:
        # 블루투스 모듈 목록 표시
        list_bluetooth_modules()
    elif args.select_module:
        # 블루투스 모듈 선택
        module = select_bluetooth_module()
        if module:
            print("\n선택된 블루투스 모듈:")
            print(f"타입: {module['type'].upper()}")
            print(f"ID: {module['id']}")
            print(f"설명: {module['description']}")
            if module.get('interface'):
                print(f"인터페이스: {module['interface']}")
            if module.get('mac'):
                print(f"MAC 주소: {module['mac']}")
    elif args.menu:
        show_terminal_menu()
    else:
        # 아무 인자도 없으면 터미널 메뉴 표시
        show_terminal_menu()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 