#!/usr/bin/env python3
import sys
import os
import subprocess

# 자체 모듈 import
from checkbluetoothlist import list_bluetooth_adapters
from bluetooth_scan import scan_devices, connect_device
from config_manager import save_config, load_config, config_exists
from daemon_control import start_relay_daemon

def select_bluetooth_adapters():
    """수신용 및 송신용 블루투스 어댑터를 선택합니다."""
    print("===== 블루투스 어댑터 목록을 가져옵니다. =====\n")
    adapters = list_bluetooth_adapters()

    if not adapters:
        print("블루투스 어댑터가 발견되지 않았습니다. USB 동글을 연결하거나, 드라이버를 확인하세요.")
        return None, None

    # 발견된 어댑터가 하나뿐이면 경고 출력
    if len(adapters) < 2:
        print("경고: 블루투스 릴레이에는 최소 2개의 어댑터가 필요합니다.")
        print("현재 발견된 어댑터는 1개뿐입니다. 추가 USB 블루투스 동글을 연결하세요.")
        return None, None

    print("===== 발견된 블루투스 어댑터 =====")
    print("--------------------------------")
    for i, hci, addr, info in adapters:
        print(f"{i}. {hci} - {addr} - {info}")
    print("--------------------------------\n")

    # 수신용, 송신용 선택
    while True:
        print("--------------------------------")
        recv_idx = input("수신용 블루투스로 지정할 번호를 입력하세요: ")
        send_idx = input("송신용 블루투스로 지정할 번호를 입력하세요: ")
        print("--------------------------------\n")
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
    
    return recv_adapter, send_adapter

def main():
    # 어댑터 선택 로직
    recv_adapter, send_adapter = select_bluetooth_adapters()
    
    # 적절한 어댑터가 선택되지 않은 경우 종료
    if recv_adapter is None or send_adapter is None:
        print("블루투스 어댑터 선택을 완료할 수 없습니다. 프로그램을 종료합니다.")
        return
    
    # 기기 스캔 및 선택 루프
    while True:
        # 수신용 어댑터로 기기 스캔
        print("\n===== 주변 블루투스 기기 스캔 =====\n")
        print("스캔 시간이 길수록 더 많은 기기를 발견할 수 있습니다.")
        print("기본값은 10초입니다. (최소 5초, 최대 60초)\n")
        
        try:
            scan_time_input = input("스캔 시간(초)을 입력하세요 [기본 10초]: ")
            scan_time = 10  # 기본값
            
            if scan_time_input.strip():  # 사용자가 값을 입력했을 경우
                scan_time = int(scan_time_input)
                scan_time = max(5, min(60, scan_time))  # 5~60초 범위로 제한
                
            print(f"\n{scan_time}초 동안 스캔을 시작합니다...\n")
            # hci 이름으로 스캔 (use_hci=True)
            devices = scan_devices(recv_adapter[1], timeout=scan_time, use_hci=True)
        except ValueError:
            print("유효한 숫자가 아닙니다. 기본값(10초)으로 스캔합니다.")
            # hci 이름으로 스캔 (use_hci=True)
            devices = scan_devices(recv_adapter[1], timeout=10, use_hci=True)
        except KeyboardInterrupt:
            print("\n\n스캔이 사용자에 의해 중단되었습니다.")
            return
        except Exception as e:
            print(f"\n스캔 중 오류가 발생했습니다: {e}")
            retry = input("다시 시도하시겠습니까? (y/n, 기본: y): ").lower()
            if retry != 'n':
                continue
            else:
                print("\n프로그램을 종료합니다.")
                return
        
        if not devices:
            print("발견된 블루투스 기기가 없습니다. 다시 시도해보세요.")
            continue  # 다시 스캔 시작
        
        print("\n===== 발견된 블루투스 기기 =====")
        print("--------------------------------")
        print("0. 재검색")  # 0번 선택지를 "재검색"으로 변경
        for i, mac, name in devices:
            print(f"{i+1}. {name} - {mac}")  # 인덱스를 1부터 시작하도록 변경
        print("--------------------------------\n")
        
        # 연결할 기기 선택
        while True:
            device_idx_input = input("연결할 마우스/기기 번호를 입력하세요 (0: 다시 스캔): ")
            try:
                device_idx = int(device_idx_input)
                if device_idx == 0:
                    print("\n다시 스캔을 시작합니다...\n")
                    break  # 내부 루프를 빠져나가 다시 스캔
                elif 1 <= device_idx <= len(devices):
                    # 사용자 인덱스(1부터 시작)에서 실제 인덱스(0부터 시작)로 변환
                    device_idx -= 1
                    # 선택한 기기에 연결
                    selected_device = devices[device_idx]
                    print(f"\n{selected_device[2]}({selected_device[1]})에 연결을 시도합니다...")
                    
                    # 연결 시도 (use_hci=True)
                    try:
                        connect_success = connect_device(recv_adapter[1], selected_device[1], use_hci=True)
                        
                        if connect_success:
                            print("\n===== 연결 성공 =====")
                            print(f"수신용 어댑터({recv_adapter[1]})와 {selected_device[2]}({selected_device[1]})가 연결되었습니다.")
                            
                            # 설정 저장 - MAC 주소 대신 hci 이름을 저장
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
                                    
                                return  # 성공적으로 연결되었으므로 프로그램 종료
                            except Exception as e:
                                print(f"\n설정 저장 오류: {e}")
                                print("설정을 저장할 수 없습니다. 수동으로 릴레이를 설정해야 합니다.")
                                return
                        else:
                            print("\n===== 연결 실패 =====")
                            print("연결에 실패했습니다. 다른 기기를 선택하거나 다시 스캔해 보세요.")
                            retry = input("다시 스캔하시겠습니까? (y/n, 기본: y): ").lower()
                            if retry != 'n':
                                break  # 내부 루프를 빠져나가 다시 스캔
                            # 'n'을 입력하면 프로그램을 종료합니다
                            else:
                                print("\n프로그램을 종료합니다.")
                                return
                    
                    except subprocess.TimeoutExpired:
                        print("\n===== 연결 시간 초과 =====")
                        print("연결 시간이 초과되었습니다(15초). 장치가 페어링 모드인지 확인하거나 다른 장치를 선택하세요.")
                        retry = input("다시 스캔하시겠습니까? (y/n, 기본: y): ").lower()
                        if retry != 'n':
                            break  # 내부 루프를 빠져나가 다시 스캔
                        else:
                            print("\n프로그램을 종료합니다.")
                            return
                            
                    except Exception as e:
                        print(f"\n===== 연결 중 오류 발생 =====")
                        print(f"오류 정보: {e}")
                        retry = input("다시 스캔하시겠습니까? (y/n, 기본: y): ").lower()
                        if retry != 'n':
                            break  # 내부 루프를 빠져나가 다시 스캔
                        else:
                            print("\n프로그램을 종료합니다.")
                            return
                else:
                    print("입력한 번호가 범위를 벗어났습니다. 다시 입력해주세요.")
            except ValueError:
                print("유효한 숫자가 아닙니다. 다시 입력해주세요.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n프로그램 실행 중 오류가 발생했습니다: {e}")
        print("프로그램을 종료합니다.")
