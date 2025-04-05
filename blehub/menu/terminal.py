#!/usr/bin/env python3
import os
import sys

# 로거 임포트
from blehub.utils.logger import logger

# 데몬 함수 임포트
from blehub.daemon.process import (
    is_running,
    start_daemon,
    stop_daemon,
    restart_daemon,
    status_daemon,
    run_setup,
    setup_recv_bluetooth,
    setup_send_bluetooth,
    get_bluetooth_config,
    list_recv_devices,
    add_recv_device,
    remove_recv_device,
    set_target_device
)

def show_recv_devices_menu():
    """수신 디바이스 관리 메뉴를 표시합니다"""
    try:
        while True:
            # 화면 지우기
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 메뉴 제목
            print("\n" + "=" * 50)
            print("수신 디바이스 관리".center(50))
            print("=" * 50)
            
            # 현재 디바이스 목록 표시
            devices = list_recv_devices()
            
            if devices:
                print("현재 등록된 수신 디바이스:")
                for i, device in enumerate(devices, 1):
                    print(f"{i}. {device.get('name', 'Unknown')} - {device.get('mac')}")
            else:
                print("등록된 수신 디바이스가 없습니다.")
            
            print("-" * 50)
            print("1. 디바이스 추가")
            print("2. 디바이스 제거")
            print("0. 이전 메뉴로 돌아가기")
            print("-" * 50)
            
            choice = input("메뉴를 선택하세요 (0-2): ")
            
            if choice == '1':
                # 디바이스 추가
                name = input("디바이스 이름을 입력하세요: ")
                mac = input("MAC 주소를 입력하세요: ")
                
                if name and mac:
                    if add_recv_device(name, mac):
                        print(f"디바이스 '{name}' ({mac})가 추가되었습니다.")
                    else:
                        print("디바이스 추가에 실패했습니다.")
                else:
                    print("이름과 MAC 주소는 비워둘 수 없습니다.")
            
            elif choice == '2':
                # 디바이스 제거
                if not devices:
                    print("제거할 디바이스가 없습니다.")
                else:
                    index = input(f"제거할 디바이스 번호를 입력하세요 (1-{len(devices)}): ")
                    try:
                        index = int(index) - 1  # 0-based 인덱스로 변환
                        if 0 <= index < len(devices):
                            if remove_recv_device(index):
                                print("디바이스가 제거되었습니다.")
                            else:
                                print("디바이스 제거에 실패했습니다.")
                        else:
                            print("잘못된 디바이스 번호입니다.")
                    except ValueError:
                        print("숫자를 입력해주세요.")
            
            elif choice == '0':
                # 이전 메뉴로 돌아가기
                break
            
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
            
            input("\n계속하려면 Enter 키를 누르세요...")
    
    except Exception as e:
        logger.error(f"수신 디바이스 메뉴 표시 중 오류 발생: {e}")
        return False
    
    return True

def show_target_device_menu():
    """송신 디바이스(타겟 디바이스) 설정 메뉴를 표시합니다"""
    try:
        # 화면 지우기
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 메뉴 제목
        print("\n" + "=" * 50)
        print("송신 디바이스 설정".center(50))
        print("=" * 50)
        
        # 현재 타겟 디바이스 표시
        config = get_bluetooth_config()
        target = config.get('target_device', {})
        
        if target and target.get('mac'):
            print(f"현재 송신 디바이스: {target.get('name', 'Unknown')} - {target.get('mac')}")
        else:
            print("설정된 송신 디바이스가 없습니다.")
        
        print("-" * 50)
        print("송신 디바이스를 설정합니다.")
        
        name = input("디바이스 이름을 입력하세요: ")
        mac = input("MAC 주소를 입력하세요: ")
        
        if name and mac:
            if set_target_device(name, mac):
                print(f"송신 디바이스가 '{name}' ({mac})로 설정되었습니다.")
            else:
                print("송신 디바이스 설정에 실패했습니다.")
        else:
            print("이름과 MAC 주소는 비워둘 수 없습니다.")
        
        input("\n이전 메뉴로 돌아가려면 Enter 키를 누르세요...")
        return True
    
    except Exception as e:
        logger.error(f"송신 디바이스 메뉴 표시 중 오류 발생: {e}")
        return False

def show_terminal_menu():
    """터미널 기반 메뉴를 표시합니다"""
    try:
        # 화면 지우기
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # 현재 데몬 상태 확인
        daemon_running = is_running()
        status_text = "실행 중" if daemon_running else "중지됨"
        
        # 블루투스 설정 정보 가져오기
        bt_config = get_bluetooth_config()
        recv_status = "설정됨" if bt_config['recv_adapter'] else "설정안됨"
        send_status = "설정됨" if bt_config['send_adapter'] else "설정안됨"
        
        while True:
            # 블루투스 설정 정보 업데이트 (메뉴가 반복될 때마다)
            bt_config = get_bluetooth_config()
            recv_status = "설정됨" if bt_config['recv_adapter'] else "설정안됨"
            send_status = "설정됨" if bt_config['send_adapter'] else "설정안됨"
            
            # 수신 디바이스 정보
            recv_devices = bt_config.get('recv_devices', [])
            recv_devices_count = len(recv_devices)
            
            # 송신 디바이스 정보
            target_device = bt_config.get('target_device', {})
            target_device_status = "설정됨" if target_device and target_device.get('mac') else "설정안됨"
            
            # 메뉴 출력
            print("\n" + "=" * 50)
            print("BLE-HUB 데몬 관리".center(50))
            print("=" * 50)
            print(f"현재 상태: {status_text}")
            print(f"수신용 블루투스: {recv_status}", end="")
            if bt_config['recv_adapter']:
                print(f" ({bt_config['recv_adapter']})")
            else:
                print()
            
            print(f"송신용 블루투스: {send_status}", end="")
            if bt_config['send_adapter']:
                print(f" ({bt_config['send_adapter']})")
            else:
                print()
            
            print(f"수신 디바이스: {recv_devices_count}개 등록됨")
            if recv_devices:
                for i, device in enumerate(recv_devices[:3], 1):  # 처음 3개만 표시
                    print(f"  {i}. {device.get('name', 'Unknown')} - {device.get('mac')}")
                if recv_devices_count > 3:
                    print(f"  ... 외 {recv_devices_count - 3}개")
            
            print(f"송신 디바이스: {target_device_status}")
            if target_device and target_device.get('mac'):
                print(f"  {target_device.get('name', 'Unknown')} - {target_device.get('mac')}")
            
            print("-" * 50)
            print("1. 데몬 시작")
            print("2. 데몬 중지")
            print("3. 데몬 재시작")
            print("4. 상태 확인")
            print("5. 설정")
            print("6. 수신용 블루투스 설정")
            print("7. 송신용 블루투스 설정")
            print("8. 수신 디바이스 관리")
            print("9. 송신 디바이스 설정")
            print("0. 종료")
            print("-" * 50)
            
            # 사용자 입력 받기
            choice = input("메뉴를 선택하세요 (0-9): ")
            
            # 입력 처리
            if choice == '1':
                # 데몬 시작
                if daemon_running:
                    print("BLE-HUB 데몬이 이미 실행 중입니다.")
                else:
                    result = start_daemon()
                    if result:
                        print("데몬이 성공적으로 시작되었습니다.")
                        daemon_running = True
                        status_text = "실행 중"
                    else:
                        print("데몬 시작에 실패했습니다. 로그를 확인하세요.")
            
            elif choice == '2':
                # 데몬 중지
                if not daemon_running:
                    print("BLE-HUB 데몬이 실행 중이 아닙니다.")
                else:
                    result = stop_daemon()
                    if result:
                        print("데몬이 중지되었습니다.")
                        daemon_running = False
                        status_text = "중지됨"
                    else:
                        print("데몬 중지에 실패했습니다. 로그를 확인하세요.")
            
            elif choice == '3':
                # 데몬 재시작
                result = restart_daemon()
                if result:
                    print("데몬이 재시작되었습니다.")
                    daemon_running = True
                    status_text = "실행 중"
                else:
                    print("데몬 재시작에 실패했습니다. 로그를 확인하세요.")
            
            elif choice == '4':
                # 상태 확인
                is_active = status_daemon()
                if not is_active:
                    print("데몬이 실행 중이 아닙니다.")
                    daemon_running = False
                    status_text = "중지됨"
                else:
                    daemon_running = True
                    status_text = "실행 중"
                input("\n계속하려면 Enter 키를 누르세요...")
            
            elif choice == '5':
                # 설정
                print("설정 메뉴를 시작합니다...")
                run_setup()
            
            elif choice == '6':
                # 수신용 블루투스 설정
                print("수신용 블루투스 설정을 시작합니다...")
                result = setup_recv_bluetooth()
                if result:
                    print("수신용 블루투스 설정이 완료되었습니다.")
                else:
                    print("수신용 블루투스 설정에 실패했습니다. 로그를 확인하세요.")
            
            elif choice == '7':
                # 송신용 블루투스 설정
                print("송신용 블루투스 설정을 시작합니다...")
                result = setup_send_bluetooth()
                if result:
                    print("송신용 블루투스 설정이 완료되었습니다.")
                else:
                    print("송신용 블루투스 설정에 실패했습니다. 로그를 확인하세요.")
            
            elif choice == '8':
                # 수신 디바이스 관리
                show_recv_devices_menu()
                # 화면 지우기
                os.system('cls' if os.name == 'nt' else 'clear')
                continue  # 메뉴 갱신을 위해 루프 처음으로 돌아감
            
            elif choice == '9':
                # 송신 디바이스 설정
                show_target_device_menu()
                # 화면 지우기
                os.system('cls' if os.name == 'nt' else 'clear')
                continue  # 메뉴 갱신을 위해 루프 처음으로 돌아감
            
            elif choice == '0':
                # 종료
                print("프로그램을 종료합니다.")
                break
            
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
            
            # 잠시 대기 후 계속
            if choice != '4':  # 상태 확인은 이미 대기 중
                input("\n계속하려면 Enter 키를 누르세요...")
            
            # 화면 지우기
            os.system('cls' if os.name == 'nt' else 'clear')
        
        return True
    except Exception as e:
        logger.error(f"터미널 메뉴 표시 중 오류 발생: {e}")
        return False 