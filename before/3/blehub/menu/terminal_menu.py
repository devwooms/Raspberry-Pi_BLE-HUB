#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import argparse
import logging
from datetime import datetime

from blehub.utils.logger import setup_logger, set_log_level
from blehub.configs.config_manager import ConfigManager
from blehub.daemon.manager import DaemonManager
from blehub.bluetooth.scanner import BluetoothScanner, select_bluetooth_device, select_bluetooth_interface, select_bluetooth_module, list_bluetooth_modules

"""
BLE-HUB 터미널 메뉴 모듈

명령줄 인터페이스를 제공합니다.
"""

# 로그 설정
logger = setup_logger("terminal_menu", "blehub.log")

class TerminalMenu:
    """터미널 메뉴 클래스"""
    
    def __init__(self):
        """터미널 메뉴 초기화"""
        self.config_manager = ConfigManager()
        self.daemon_manager = DaemonManager(self.config_manager)
    
    def main_menu(self):
        """메인 메뉴 표시"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("BLE-HUB 블루투스 릴레이 관리 시스템".center(60))
            print("=" * 60)
            
            daemon_status = self.daemon_manager.status()
            
            # 데몬 상태 표시
            if daemon_status["running"]:
                print("✅ 데몬 상태: 실행 중")
            else:
                print("⚠️  데몬 상태: 중지됨")
                
            # 블루투스 모듈 정보 표시
            source_adapter = daemon_status.get('source_adapter', 'Unknown')
            source_adapter_mac = "Unknown"
            target_adapter = daemon_status.get('target_adapter', 'Unknown')
            target_adapter_mac = "Unknown"
            
            # 어댑터의 MAC 주소 가져오기
            interfaces = BluetoothScanner.get_bluetooth_interfaces()
            for interface in interfaces:
                if interface.get('id') == source_adapter:
                    source_adapter_mac = interface.get('mac', 'Unknown')
                if interface.get('id') == target_adapter:
                    target_adapter_mac = interface.get('mac', 'Unknown')
            
            print(f"수신 블루투스 모듈: {source_adapter} - {source_adapter_mac}")
            print(f"송신 블루투스 모듈: {target_adapter} - {target_adapter_mac}")
            
            # 수신 디바이스 목록 표시 (여러 개 가능)
            source_devices = daemon_status.get('source_devices', [])
            print("수신 블루투스 디바이스:")
            if source_devices:
                for i, device in enumerate(source_devices, 1):
                    device_name = device.get('name', 'Unknown')
                    device_mac = device.get('mac', 'Unknown')
                    device_type = BluetoothScanner.get_device_type(device_name, device_mac)
                    print(f"  {i}. {device_type} - {device_mac}")
            else:
                print("  설정된 디바이스 없음")
            
            # 송신 디바이스 표시
            target_device_mac = daemon_status.get('target_device', '')
            print("송신 블루투스 디바이스:")
            if target_device_mac and target_device_mac != '알 수 없음':
                # 설정에서 디바이스 정보 찾기
                target_device_name = "Unknown"
                config = self.config_manager.get_full_config()
                # 검색된 디바이스 캐시가 있으면 사용
                if 'device_cache' in config and target_device_mac in config['device_cache']:
                    target_device_name = config['device_cache'][target_device_mac]
                    
                device_type = BluetoothScanner.get_device_type(target_device_name, target_device_mac)
                print(f"  1. {device_type} - {target_device_mac}")
            else:
                print("  설정된 디바이스 없음")
            
            print("\n메뉴:")
            print("1. 데몬 관리")
            print("2. 블루투스 모듈 관리")
            print("3. 설정 관리")
            print("4. 로그 레벨 설정")
            print("0. 종료")
            
            choice = input("\n선택: ")
            
            if choice == "1":
                self.daemon_menu()
            elif choice == "2":
                self.bluetooth_menu()
            elif choice == "3":
                self.config_menu()
            elif choice == "4":
                self.log_level_menu()
            elif choice == "0":
                print("프로그램을 종료합니다.")
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def daemon_menu(self):
        """데몬 관리 메뉴"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("데몬 관리".center(60))
            print("=" * 60)
            
            daemon_status = self.daemon_manager.status()
            
            # 데몬 상태 표시
            if daemon_status["running"]:
                print("✅ 데몬 상태: 실행 중")
            else:
                print("⚠️  데몬 상태: 중지됨")
                
            # 블루투스 모듈 정보 표시
            source_adapter = daemon_status.get('source_adapter', 'Unknown')
            source_adapter_mac = "Unknown"
            target_adapter = daemon_status.get('target_adapter', 'Unknown')
            target_adapter_mac = "Unknown"
            
            # 어댑터의 MAC 주소 가져오기
            interfaces = BluetoothScanner.get_bluetooth_interfaces()
            for interface in interfaces:
                if interface.get('id') == source_adapter:
                    source_adapter_mac = interface.get('mac', 'Unknown')
                if interface.get('id') == target_adapter:
                    target_adapter_mac = interface.get('mac', 'Unknown')
            
            print(f"수신 블루투스 모듈: {source_adapter} - {source_adapter_mac}")
            print(f"송신 블루투스 모듈: {target_adapter} - {target_adapter_mac}")
            
            # 수신 디바이스 목록 표시 (여러 개 가능)
            source_devices = daemon_status.get('source_devices', [])
            print("수신 블루투스 디바이스:")
            if source_devices:
                for i, device in enumerate(source_devices, 1):
                    device_name = device.get('name', 'Unknown')
                    device_mac = device.get('mac', 'Unknown')
                    device_type = BluetoothScanner.get_device_type(device_name, device_mac)
                    print(f"  {i}. {device_type} - {device_mac}")
            else:
                print("  설정된 디바이스 없음")
            
            # 송신 디바이스 표시
            target_device_mac = daemon_status.get('target_device', '')
            print("송신 블루투스 디바이스:")
            if target_device_mac and target_device_mac != '알 수 없음':
                # 설정에서 디바이스 정보 찾기
                target_device_name = "Unknown"
                config = self.config_manager.get_full_config()
                # 검색된 디바이스 캐시가 있으면 사용
                if 'device_cache' in config and target_device_mac in config['device_cache']:
                    target_device_name = config['device_cache'][target_device_mac]
                    
                device_type = BluetoothScanner.get_device_type(target_device_name, target_device_mac)
                print(f"  1. {device_type} - {target_device_mac}")
            else:
                print("  설정된 디바이스 없음")
            
            print("\n메뉴:")
            print("1. 데몬 시작")
            print("2. 데몬 중지")
            print("3. 데몬 재시작")
            print("4. 데몬 상태 확인")
            print("0. 이전 메뉴로 돌아가기")
            
            choice = input("\n선택: ")
            
            if choice == "1":
                if not self.daemon_manager.start():
                    input("계속하려면 Enter 키를 누르세요...")
                else:
                    print("데몬이 시작되었습니다.")
                    input("계속하려면 Enter 키를 누르세요...")
            elif choice == "2":
                if not self.daemon_manager.stop():
                    input("계속하려면 Enter 키를 누르세요...")
                else:
                    print("데몬이 중지되었습니다.")
                    input("계속하려면 Enter 키를 누르세요...")
            elif choice == "3":
                if not self.daemon_manager.restart():
                    input("계속하려면 Enter 키를 누르세요...")
                else:
                    print("데몬이 재시작되었습니다.")
                    input("계속하려면 Enter 키를 누르세요...")
            elif choice == "4":
                status = self.daemon_manager.status()
                print("\n데몬 상태:")
                for key, value in status.items():
                    print(f"{key}: {value}")
                input("\n계속하려면 Enter 키를 누르세요...")
            elif choice == "0":
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def bluetooth_menu(self):
        """블루투스 관리 메뉴"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("블루투스 관리".center(60))
            print("=" * 60)
            
            print("\n메뉴:")
            print("1. 블루투스 모듈 목록 표시")
            print("2. 소스 블루투스 인터페이스 선택")
            print("3. 타겟 블루투스 인터페이스 선택")
            print("4. 수신 블루투스 디바이스 추가")
            print("5. 수신 블루투스 디바이스 삭제")
            print("6. 송신 블루투스 디바이스 선택")
            print("0. 이전 메뉴로 돌아가기")
            
            choice = input("\n선택: ")
            
            if choice == "1":
                list_bluetooth_modules()
                input("\n계속하려면 Enter 키를 누르세요...")
            elif choice == "2":
                interface = select_bluetooth_interface()
                if interface:
                    print(f"\n선택된 인터페이스: {interface['id']}")
                    self.config_manager.set("source_adapter", interface['id'])
                    self.config_manager.save()
                    print(f"소스 어댑터가 {interface['id']}로 설정되었습니다.")
                input("\n계속하려면 Enter 키를 누르세요...")
            elif choice == "3":
                interface = select_bluetooth_interface()
                if interface:
                    print(f"\n선택된 인터페이스: {interface['id']}")
                    self.config_manager.set("target_adapter", interface['id'])
                    self.config_manager.save()
                    print(f"타겟 어댑터가 {interface['id']}로 설정되었습니다.")
                input("\n계속하려면 Enter 키를 누르세요...")
            elif choice == "4":
                # 수신 디바이스를 스캔하기 위해 소스 어댑터 확인
                source_adapter = self.config_manager.get("source_adapter", "hci0")
                device = select_bluetooth_device(source_adapter)
                if device:
                    print(f"\n선택된 디바이스: {device['name']} ({device['mac']})")
                    
                    # 장치 페어링 및 연결 시도
                    print(f"\n{device['name']} 장치와 페어링 및 연결 시도 중...")
                    if BluetoothScanner.pair_and_connect_device(source_adapter, device['mac']):
                        print(f"\n{device['name']} 장치와 페어링 및 연결 성공!")
                    else:
                        print(f"\n{device['name']} 장치와 페어링 및 연결 실패")
                        print("하지만 장치 정보는 추가합니다.")
                    
                    # 설정에 장치 추가
                    self.config_manager.add_source_device(device)
                    print(f"수신 디바이스 '{device['name']}'이(가) 추가되었습니다.")
                input("\n계속하려면 Enter 키를 누르세요...")
            elif choice == "5":
                # 수신 디바이스 목록 표시 및 삭제
                source_devices = self.config_manager.get("source_devices", [])
                if not source_devices:
                    print("\n등록된 수신 디바이스가 없습니다.")
                else:
                    print("\n수신 디바이스 목록:")
                    for i, device in enumerate(source_devices, 1):
                        print(f"{i}. {device.get('name', 'Unknown')} - {device.get('mac', 'Unknown')}")
                    
                    device_choice = input("\n삭제할 디바이스 번호를 선택하세요 (0=취소): ")
                    if device_choice != "0":
                        try:
                            device_index = int(device_choice) - 1
                            if 0 <= device_index < len(source_devices):
                                device = source_devices[device_index]
                                source_adapter = self.config_manager.get("source_adapter", "hci0")
                                
                                # 장치 연결 해제 및 페어링 제거
                                print(f"\n{device['name']} 장치 연결 해제 및 제거 중...")
                                BluetoothScanner.disconnect_and_remove_device(source_adapter, device['mac'])
                                
                                # 설정에서 장치 제거
                                self.config_manager.remove_source_device(device['mac'])
                                print(f"\n수신 디바이스 '{device['name']}'이(가) 삭제되었습니다.")
                            else:
                                print("\n잘못된 선택입니다.")
                        except ValueError:
                            print("\n잘못된 입력입니다.")
                
                input("\n계속하려면 Enter 키를 누르세요...")
            elif choice == "6":
                # 송신 디바이스를 스캔하기 위해 타겟 어댑터 확인
                target_adapter = self.config_manager.get("target_adapter", "hci0")
                device = select_bluetooth_device(target_adapter)
                if device:
                    print(f"\n선택된 디바이스: {device['name']} ({device['mac']})")
                    
                    # 장치 페어링 및 연결 시도
                    print(f"\n{device['name']} 장치와 페어링 및 연결 시도 중...")
                    if BluetoothScanner.pair_and_connect_device(target_adapter, device['mac']):
                        print(f"\n{device['name']} 장치와 페어링 및 연결 성공!")
                    else:
                        print(f"\n{device['name']} 장치와 페어링 및 연결 실패")
                        print("하지만 장치 정보는 등록합니다.")
                    
                    # 디바이스를 캐시에 추가
                    self.config_manager.cache_device(device)
                    
                    # 타겟 디바이스 설정
                    self.config_manager.set("target_device", device['mac'])
                    
                    device_type = BluetoothScanner.get_device_type(device['name'], device['mac'])
                    print(f"송신 디바이스가 {device_type}({device['mac']})로 설정되었습니다.")
                input("\n계속하려면 Enter 키를 누르세요...")
            elif choice == "0":
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def config_menu(self):
        """설정 관리 메뉴"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("설정 관리".center(60))
            print("=" * 60)
            
            # 현재 설정 표시
            config = self.config_manager.get_full_config()
            print("\n현재 설정:")
            for section, values in config.items():
                print(f"{section}:")
                if isinstance(values, dict):
                    for key, value in values.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {values}")
            
            print("\n메뉴:")
            print("1. 설정 저장")
            print("2. 설정 불러오기")
            print("3. 설정 초기화")
            print("0. 이전 메뉴로 돌아가기")
            
            choice = input("\n선택: ")
            
            if choice == "1":
                self.config_manager.save_config()
                print("설정이 저장되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "2":
                self.config_manager.load_config()
                print("설정이 불러와졌습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "3":
                confirm = input("정말로 설정을 초기화하시겠습니까? (y/n): ")
                if confirm.lower() == 'y':
                    self.config_manager.reset_config()
                    print("설정이 초기화되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "0":
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def log_level_menu(self):
        """로그 레벨 설정 메뉴"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("로그 레벨 설정".center(60))
            print("=" * 60)
            
            print("\n메뉴:")
            print("1. DEBUG 레벨 설정")
            print("2. INFO 레벨 설정")
            print("3. WARNING 레벨 설정")
            print("4. ERROR 레벨 설정")
            print("0. 이전 메뉴로 돌아가기")
            
            choice = input("\n선택: ")
            
            if choice == "1":
                set_log_level("DEBUG")
                print("로그 레벨이 DEBUG로 설정되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "2":
                set_log_level("INFO")
                print("로그 레벨이 INFO로 설정되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "3":
                set_log_level("WARNING")
                print("로그 레벨이 WARNING으로 설정되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "4":
                set_log_level("ERROR")
                print("로그 레벨이 ERROR로 설정되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "0":
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def _clear_screen(self):
        """화면 지우기"""
        os.system('cls' if os.name == 'nt' else 'clear')

def run_terminal_menu():
    """터미널 메뉴 실행"""
    menu = TerminalMenu()
    menu.main_menu()

def parse_arguments():
    """명령줄 인수 파싱
    
    Returns:
        argparse.Namespace: 파싱된 인수
    """
    parser = argparse.ArgumentParser(description="BLE-HUB 블루투스 릴레이 데몬 관리")
    
    # 데몬 관리 인수
    parser.add_argument('--start', action='store_true', help='데몬 시작')
    parser.add_argument('--stop', action='store_true', help='데몬 중지')
    parser.add_argument('--restart', action='store_true', help='데몬 재시작')
    parser.add_argument('--status', action='store_true', help='데몬 상태 확인')
    
    # 블루투스 관리 인수
    parser.add_argument('--list-modules', action='store_true', help='블루투스 모듈 목록 표시')
    parser.add_argument('--select-module', action='store_true', help='블루투스 모듈 선택')
    
    # 설정 인수
    parser.add_argument('--config', action='store_true', help='설정 표시')
    parser.add_argument('--set-source', type=str, help='소스 어댑터 설정')
    parser.add_argument('--set-target-adapter', type=str, help='타겟 어댑터 설정')
    parser.add_argument('--set-target-device', type=str, help='타겟 장치 설정')
    
    # 로그 인수
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='로그 레벨 설정')
    
    # 메뉴 인수
    parser.add_argument('--menu', action='store_true', help='터미널 메뉴 실행')
    
    return parser.parse_args()

def process_arguments(args):
    """명령줄 인수 처리
    
    Args:
        args (argparse.Namespace): 파싱된 인수
        
    Returns:
        bool: 처리 성공 여부
    """
    config_manager = ConfigManager()
    daemon_manager = DaemonManager(config_manager)
    
    # 로그 레벨 설정
    if args.log_level:
        set_log_level(args.log_level)
        print(f"로그 레벨이 {args.log_level}로 설정되었습니다.")
    
    # 블루투스 관리
    if args.list_modules:
        list_bluetooth_modules()
        return True
    
    if args.select_module:
        select_bluetooth_module()
        return True
    
    # 설정 관리
    if args.set_source:
        config_manager.set_config("source_adapter", args.set_source)
        config_manager.save_config()
        print(f"소스 어댑터가 {args.set_source}로 설정되었습니다.")
    
    if args.set_target_adapter:
        config_manager.set_config("target_adapter", args.set_target_adapter)
        config_manager.save_config()
        print(f"타겟 어댑터가 {args.set_target_adapter}로 설정되었습니다.")
    
    if args.set_target_device:
        config_manager.set_config("target_device", args.set_target_device)
        config_manager.save_config()
        print(f"타겟 장치가 {args.set_target_device}로 설정되었습니다.")
    
    if args.config:
        config = config_manager.get_full_config()
        print("\n현재 설정:")
        for section, values in config.items():
            print(f"{section}:")
            if isinstance(values, dict):
                for key, value in values.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {values}")
        return True
    
    # 데몬 관리
    if args.start:
        return daemon_manager.start()
    
    if args.stop:
        return daemon_manager.stop()
    
    if args.restart:
        return daemon_manager.restart()
    
    if args.status:
        status = daemon_manager.status()
        print("\n데몬 상태:")
        for key, value in status.items():
            print(f"{key}: {value}")
        return True
    
    # 메뉴 실행
    if args.menu:
        run_terminal_menu()
        return True
    
    # 아무 인수도 지정되지 않은 경우 메뉴 실행
    if len(sys.argv) <= 1:
        run_terminal_menu()
        return True
    
    return False

def main():
    """메인 함수"""
    args = parse_arguments()
    success = process_arguments(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 