#!/usr/bin/env python3
import os
import json
import time
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("config_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Config-Manager")

# 설정 파일 경로
CONFIG_FILE = "ble_config.json"

def save_config(recv_adapter, send_adapter, target_device):
    """
    블루투스 릴레이 설정을 파일에 저장합니다.
    """
    config = {
        "recv_adapter": recv_adapter,
        "send_adapter": send_adapter,
        "target_device": target_device,
        "last_updated": time.time()
    }
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"설정이 {CONFIG_FILE}에 저장되었습니다.")
        return True
    except Exception as e:
        logger.error(f"설정 저장 오류: {e}")
        return False

def load_config():
    """
    저장된 블루투스 릴레이 설정을 로드합니다.
    """
    if not os.path.exists(CONFIG_FILE):
        logger.info(f"{CONFIG_FILE}이 존재하지 않습니다.")
        return None
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        logger.info(f"설정을 {CONFIG_FILE}에서 로드했습니다.")
        return config
    except Exception as e:
        logger.error(f"설정 로드 오류: {e}")
        return None

def get_adapters_info():
    """
    현재 설정에서 어댑터 정보를 가져옵니다.
    """
    config = load_config()
    if not config:
        return None, None
    
    recv = config.get("recv_adapter")
    send = config.get("send_adapter")
    
    return recv, send

def get_target_device():
    """
    현재 설정된 타겟 기기(마우스 등)의 MAC 주소를 가져옵니다.
    """
    config = load_config()
    if not config:
        return None
    
    return config.get("target_device")

def config_exists():
    """
    설정 파일이 존재하는지 확인합니다.
    """
    return os.path.exists(CONFIG_FILE)

if __name__ == "__main__":
    # 단독 실행 시 테스트 코드
    if config_exists():
        print("현재 설정:")
        config = load_config()
        if config:
            print(f"수신용 어댑터: {config.get('recv_adapter')}")
            print(f"송신용 어댑터: {config.get('send_adapter')}")
            print(f"타겟 기기: {config.get('target_device')}")
            print(f"마지막 업데이트: {time.ctime(config.get('last_updated', 0))}")
    else:
        print("저장된 설정이 없습니다.") 