#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import signal
import json
from pathlib import Path

# 스크립트의 경로
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PID 파일 경로
PID_FILE = os.path.join(SCRIPT_DIR, "blehub.pid")

# 설정 파일 경로
CONFIG_FILE = os.path.join(SCRIPT_DIR, "ble_config.json")

# 로거 임포트
from blehub.utils.logger import logger

def is_running():
    """데몬이 실행 중인지 확인합니다"""
    if not os.path.exists(PID_FILE):
        return False
    
    try:
        # PID 파일에서 프로세스 ID 읽기
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # 프로세스 존재 확인
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            # 프로세스가 존재하지 않음
            return False
    except Exception:
        return False

def get_bluetooth_config():
    """블루투스 설정 정보를 반환합니다"""
    recv_adapter = None
    send_adapter = None
    target_device = None
    recv_devices = []
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            recv_adapter = config.get('recv_adapter')
            send_adapter = config.get('send_adapter')
            target_device = config.get('target_device')
            # 수신 디바이스 목록을 가져옵니다 (없으면 빈 리스트)
            recv_devices = config.get('recv_devices', [])
        except Exception as e:
            logger.error(f"설정 파일 읽기 오류: {e}")
    
    return {
        'recv_adapter': recv_adapter,
        'send_adapter': send_adapter,
        'target_device': target_device,
        'recv_devices': recv_devices
    }

def save_bluetooth_config(config):
    """블루투스 설정 정보를 저장합니다"""
    try:
        # 기존 설정 파일이 있으면 읽어옵니다
        current_config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                current_config = json.load(f)
        
        # 새 설정 정보로 업데이트합니다
        current_config.update(config)
        
        # 파일에 저장합니다
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=4)
        
        logger.info("블루투스 설정이 저장되었습니다.")
        return True
    except Exception as e:
        logger.error(f"설정 파일 저장 오류: {e}")
        return False

def start_daemon():
    """데몬을 시작합니다"""
    # 이미 실행 중인지 확인
    if is_running():
        logger.info("BLE-HUB 데몬이 이미 실행 중입니다.")
        return False
        
    # 설정 파일 확인
    if not os.path.exists(CONFIG_FILE):
        logger.error("설정 파일이 존재하지 않습니다. 먼저 설정을 완료해주세요.")
        logger.info("설정을 위해 'python3 main.py'를 실행하세요.")
        return False
    
    logger.info("BLE-HUB 데몬을 시작합니다...")
    
    try:
        # 데몬 프로세스 시작
        process = subprocess.Popen(
            ["python3", os.path.join(SCRIPT_DIR, "ble_relay.py"), "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # 잠시 대기 후 프로세스가 실행 중인지 확인
        time.sleep(2)
        if process.poll() is None:  # 여전히 실행 중이면
            # PID 파일에 프로세스 ID 저장
            with open(PID_FILE, 'w') as f:
                f.write(str(process.pid))
            
            logger.info(f"BLE-HUB 데몬이 성공적으로 시작되었습니다. (PID: {process.pid})")
            return True
        else:
            # 프로세스가 종료된 경우
            stdout, stderr = process.communicate()
            logger.error(f"BLE-HUB 데몬 시작 실패: {stderr.decode()}")
            return False
    except Exception as e:
        logger.error(f"데몬 시작 중 오류 발생: {e}")
        return False

def stop_daemon():
    """실행 중인 데몬을 중지합니다"""
    if not is_running():
        logger.info("BLE-HUB 데몬이 실행 중이 아닙니다.")
        return True
    
    try:
        # PID 파일에서 프로세스 ID 읽기
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        logger.info(f"BLE-HUB 데몬(PID: {pid})을 중지합니다...")
        
        # 프로세스 종료 명령 실행
        subprocess.run(["python3", os.path.join(SCRIPT_DIR, "ble_relay.py"), "stop"])
        
        # 프로세스가 실제로 종료되었는지 확인
        tries = 0
        while tries < 5:
            try:
                # 프로세스 존재 확인
                os.kill(pid, 0)
                # 여전히 존재하면 잠시 대기
                time.sleep(1)
                tries += 1
            except OSError:
                # 프로세스가 존재하지 않음
                break
        
        # 5번 시도해도 종료되지 않으면 강제 종료
        if tries >= 5:
            logger.warning("정상적으로 종료되지 않아 강제 종료합니다...")
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass  # 이미 종료됨
        
        # PID 파일 삭제
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        
        logger.info("BLE-HUB 데몬이 중지되었습니다.")
        return True
    except Exception as e:
        logger.error(f"데몬 중지 중 오류 발생: {e}")
        return False

def restart_daemon():
    """데몬을 재시작합니다"""
    stop_daemon()
    time.sleep(2)  # 종료 후 잠시 대기
    return start_daemon()

def status_daemon():
    """데몬의 상태를 확인합니다"""
    if not is_running():
        logger.info("BLE-HUB 데몬이 실행 중이 아닙니다.")
        return False
    
    try:
        # PID 파일에서 프로세스 ID 읽기
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # 프로세스 상태 확인
        try:
            os.kill(pid, 0)
            logger.info(f"BLE-HUB 데몬이 실행 중입니다. (PID: {pid})")
            
            # 설정 정보 표시
            config = get_bluetooth_config()
            
            logger.info("현재 설정:")
            logger.info(f"- 수신용 어댑터: {config['recv_adapter']}")
            logger.info(f"- 송신용 어댑터: {config['send_adapter']}")
            logger.info(f"- 타겟 기기: {config['target_device']}")
            
            # 수신 디바이스 목록 표시
            if config['recv_devices']:
                logger.info("- 수신 디바이스 목록:")
                for i, device in enumerate(config['recv_devices'], 1):
                    logger.info(f"  {i}. {device.get('name', 'Unknown')} - {device.get('mac')}")
            
            return True
        except OSError:
            # 프로세스가 존재하지 않음
            logger.warning("PID 파일이 존재하지만 프로세스는 실행 중이 아닙니다.")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            return False
    except Exception as e:
        logger.error(f"상태 확인 중 오류 발생: {e}")
        return False

def run_setup():
    """설정 메뉴를 실행합니다"""
    logger.info("설정 메뉴를 시작합니다...")
    try:
        # main.py 실행
        subprocess.run(["python3", os.path.join(SCRIPT_DIR, "main.py")])
        return True
    except Exception as e:
        logger.error(f"설정 실행 중 오류 발생: {e}")
        return False

def setup_recv_bluetooth():
    """수신용 블루투스를 설정합니다"""
    logger.info("수신용 블루투스 설정을 시작합니다...")
    try:
        # 블루투스 설정 모듈 임포트
        from blehub.daemon.bluetooth_setup import setup_recv_bluetooth_adapter, setup_recv_device
        
        # 어댑터 설정
        if not setup_recv_bluetooth_adapter():
            return False
        
        # 사용자에게 디바이스도 설정할지 물어봄
        print("\n수신 디바이스도 추가하시겠습니까? (y/n): ", end="")
        choice = input().strip().lower()
        
        if choice == 'y' or choice == 'yes':
            setup_recv_device()
        
        return True
    except Exception as e:
        logger.error(f"수신용 블루투스 설정 중 오류 발생: {e}")
        return False

def setup_send_bluetooth():
    """송신용 블루투스를 설정합니다"""
    logger.info("송신용 블루투스 설정을 시작합니다...")
    try:
        # 블루투스 설정 모듈 임포트
        from blehub.daemon.bluetooth_setup import setup_send_bluetooth_adapter, setup_target_device
        
        # 어댑터 설정
        if not setup_send_bluetooth_adapter():
            return False
        
        # 사용자에게 디바이스도 설정할지 물어봄
        print("\n송신 디바이스도 설정하시겠습니까? (y/n): ", end="")
        choice = input().strip().lower()
        
        if choice == 'y' or choice == 'yes':
            setup_target_device()
        
        return True
    except Exception as e:
        logger.error(f"송신용 블루투스 설정 중 오류 발생: {e}")
        return False

def list_recv_devices():
    """수신 디바이스 목록을 조회합니다"""
    config = get_bluetooth_config()
    devices = config.get('recv_devices', [])
    return devices

def add_recv_device(name, mac):
    """수신 디바이스를 추가합니다"""
    try:
        # 현재 설정 정보 가져오기
        config = get_bluetooth_config()
        devices = config.get('recv_devices', [])
        
        # 새 디바이스 추가
        devices.append({'name': name, 'mac': mac})
        
        # 설정 저장
        return save_bluetooth_config({'recv_devices': devices})
    except Exception as e:
        logger.error(f"수신 디바이스 추가 중 오류 발생: {e}")
        return False

def remove_recv_device(index):
    """수신 디바이스를 제거합니다"""
    try:
        # 현재 설정 정보 가져오기
        config = get_bluetooth_config()
        devices = config.get('recv_devices', [])
        
        # 인덱스 검증
        if 0 <= index < len(devices):
            # 디바이스 제거
            device = devices.pop(index)
            logger.info(f"디바이스 '{device.get('name')}' ({device.get('mac')})가 제거되었습니다.")
            
            # 설정 저장
            return save_bluetooth_config({'recv_devices': devices})
        else:
            logger.error(f"잘못된 디바이스 인덱스: {index}")
            return False
    except Exception as e:
        logger.error(f"수신 디바이스 제거 중 오류 발생: {e}")
        return False

def set_target_device(name, mac):
    """송신 디바이스(타겟 디바이스)를 설정합니다"""
    try:
        # 설정 저장
        return save_bluetooth_config({'target_device': {'name': name, 'mac': mac}})
    except Exception as e:
        logger.error(f"송신 디바이스 설정 중 오류 발생: {e}")
        return False 