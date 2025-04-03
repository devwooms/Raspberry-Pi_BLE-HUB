#!/usr/bin/env python3
import subprocess
import os
import sys
import logging
from pathlib import Path
from bluetooth_scan import disconnect_all_devices

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("daemon_control.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Daemon-Control")

def start_relay_daemon():
    """
    릴레이 데몬을 시작합니다.
    """
    print("\n===== 블루투스 릴레이 데몬 시작 =====")
    print("백그라운드에서 BLE 릴레이 데몬을 시작합니다...")
    
    try:
        # 같은 디렉토리에 있는 ble_relay.py 실행
        script_dir = os.path.dirname(os.path.abspath(__file__))
        relay_script = os.path.join(script_dir, "ble_relay.py")
        
        if os.path.exists(relay_script):
            result = subprocess.run([sys.executable, relay_script, "start"], 
                                   capture_output=True, text=True)
            print(result.stdout)
            if result.returncode == 0:
                print("BLE 릴레이 데몬이 성공적으로 시작되었습니다.")
                print("이제 마우스/키보드 신호가 수신용 어댑터에서 송신용 어댑터로 자동 전달됩니다.\n")
                print("데몬을 중지하려면 다음 명령을 실행하세요:")
                print(f"  {sys.executable} {relay_script} stop")
                return True
            else:
                print(f"릴레이 데몬 시작 실패: {result.stderr}")
                return False
        else:
            print(f"릴레이 스크립트({relay_script})를 찾을 수 없습니다.")
            return False
    except Exception as e:
        print(f"릴레이 데몬 시작 오류: {e}")
        return False

def stop_relay_daemon(disconnect_devices=True):
    """
    릴레이 데몬을 중지합니다.
    :param disconnect_devices: 데몬 종료 시 블루투스 연결도 해제할지 여부
    """
    print("\n===== 블루투스 릴레이 데몬 중지 =====")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        relay_script = os.path.join(script_dir, "ble_relay.py")
        
        if os.path.exists(relay_script):
            result = subprocess.run([sys.executable, relay_script, "stop"], 
                                   capture_output=True, text=True)
            print(result.stdout)
            
            # 데몬이 종료되었지만 연결 해제 옵션이 켜져 있고 데몬이 연결 해제를 못했을 경우
            if disconnect_devices:
                try:
                    # config_manager에서 설정 정보 로드
                    from config_manager import load_config
                    config = load_config()
                    
                    if config:
                        print("\n추가 확인: 블루투스 연결 상태 확인 중...")
                        # 수신 어댑터 연결 상태 확인
                        if 'recv_adapter' in config:
                            print(f"수신 어댑터 {config['recv_adapter']}의 연결 상태 확인 중...")
                            disconnect_all_devices(config['recv_adapter'])
                        
                        # 송신 어댑터 연결 상태 확인
                        if 'send_adapter' in config:
                            print(f"송신 어댑터 {config['send_adapter']}의 연결 상태 확인 중...")
                            disconnect_all_devices(config['send_adapter'])
                except Exception as e:
                    print(f"추가 연결 해제 중 오류: {e}")
            
            if result.returncode == 0:
                print("BLE 릴레이 데몬이 성공적으로 중지되었습니다.")
                return True
            else:
                print(f"릴레이 데몬 중지 실패: {result.stderr}")
                return False
        else:
            print(f"릴레이 스크립트({relay_script})를 찾을 수 없습니다.")
            return False
    except Exception as e:
        print(f"릴레이 데몬 중지 오류: {e}")
        return False

def check_daemon_status():
    """
    데몬 실행 상태를 확인합니다.
    """
    pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ble_relay.pid")
    
    if not os.path.exists(pid_file):
        print("BLE 릴레이 데몬이 실행 중이 아닙니다.")
        return False
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # 프로세스가 실행 중인지 확인
        try:
            os.kill(pid, 0)  # 프로세스 상태 확인 (신호를 보내지 않음)
            print(f"BLE 릴레이 데몬이 실행 중입니다 (PID: {pid})")
            return True
        except OSError:
            print(f"PID 파일이 존재하지만 프로세스(PID: {pid})는 실행 중이 아닙니다.")
            return False
    except Exception as e:
        print(f"데몬 상태 확인 오류: {e}")
        return False

if __name__ == "__main__":
    # 단독 실행 시 테스트 코드
    import argparse
    
    parser = argparse.ArgumentParser(description="블루투스 릴레이 데몬 제어")
    parser.add_argument('action', choices=['start', 'stop', 'status'], 
                        help='수행할 작업 (start, stop, status)')
    parser.add_argument('--no-disconnect', action='store_true',
                        help='종료 시 블루투스 연결 해제하지 않음')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        start_relay_daemon()
    elif args.action == 'stop':
        stop_relay_daemon(disconnect_devices=not args.no_disconnect)
    elif args.action == 'status':
        check_daemon_status() 