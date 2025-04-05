#!/usr/bin/env python3
import os
import sys
import json

# 스크립트의 경로
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 설정 파일 경로
CONFIG_FILE = os.path.join(SCRIPT_DIR, "ble_config.json")

# 로거와 블루투스 유틸리티 임포트
from blehub.utils.logger import logger
from blehub.utils.bluetooth import (
    select_bluetooth_interface,
    select_bluetooth_device
)

def setup_recv_bluetooth_adapter():
    """수신용 블루투스 어댑터를 설정합니다"""
    try:
        print("\n" + "=" * 50)
        print("수신용 블루투스 어댑터 설정".center(50))
        print("=" * 50)
        
        print("수신용으로 사용할 블루투스 어댑터를 선택하세요.")
        interface = select_bluetooth_interface()
        
        if not interface:
            logger.info("수신용 블루투스 어댑터 설정이 취소되었습니다.")
            print("설정이 취소되었습니다.")
            return False
        
        # 설정 파일 읽기
        current_config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                current_config = json.load(f)
        
        # 어댑터 정보 업데이트
        current_config['recv_adapter'] = interface['id']
        
        # 설정 저장
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=4)
        
        logger.info(f"수신용 블루투스 어댑터가 {interface['id']}({interface['name']})로 설정되었습니다.")
        print(f"\n수신용 블루투스 어댑터가 설정되었습니다:")
        print(f"- 인터페이스: {interface['id']}")
        print(f"- 이름: {interface['name']}")
        print(f"- MAC 주소: {interface['mac']}")
        
        return True
        
    except Exception as e:
        logger.error(f"수신용 블루투스 어댑터 설정 중 오류 발생: {e}")
        print(f"오류가 발생했습니다: {e}")
        return False

def setup_send_bluetooth_adapter():
    """송신용 블루투스 어댑터를 설정합니다"""
    try:
        print("\n" + "=" * 50)
        print("송신용 블루투스 어댑터 설정".center(50))
        print("=" * 50)
        
        print("송신용으로 사용할 블루투스 어댑터를 선택하세요.")
        interface = select_bluetooth_interface()
        
        if not interface:
            logger.info("송신용 블루투스 어댑터 설정이 취소되었습니다.")
            print("설정이 취소되었습니다.")
            return False
        
        # 설정 파일 읽기
        current_config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                current_config = json.load(f)
        
        # 어댑터 정보 업데이트
        current_config['send_adapter'] = interface['id']
        
        # 설정 저장
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=4)
        
        logger.info(f"송신용 블루투스 어댑터가 {interface['id']}({interface['name']})로 설정되었습니다.")
        print(f"\n송신용 블루투스 어댑터가 설정되었습니다:")
        print(f"- 인터페이스: {interface['id']}")
        print(f"- 이름: {interface['name']}")
        print(f"- MAC 주소: {interface['mac']}")
        
        return True
        
    except Exception as e:
        logger.error(f"송신용 블루투스 어댑터 설정 중 오류 발생: {e}")
        print(f"오류가 발생했습니다: {e}")
        return False

def setup_target_device(adapter_id=None):
    """타겟 디바이스(송신 디바이스)를 설정합니다"""
    try:
        print("\n" + "=" * 50)
        print("송신 디바이스 설정".center(50))
        print("=" * 50)
        
        # 설정된 송신용 어댑터 또는 기본값 사용
        if not adapter_id:
            # 설정 파일 읽기
            current_config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    current_config = json.load(f)
            
            adapter_id = current_config.get('send_adapter', 'hci0')
        
        print(f"블루투스 어댑터 {adapter_id}를 사용하여 장치를 검색합니다.")
        device = select_bluetooth_device(adapter_id)
        
        if not device:
            logger.info("송신 디바이스 설정이 취소되었습니다.")
            print("설정이 취소되었습니다.")
            return False
        
        # 설정 파일 읽기
        current_config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                current_config = json.load(f)
        
        # 디바이스 정보 업데이트
        current_config['target_device'] = {
            'name': device['name'],
            'mac': device['mac']
        }
        
        # 설정 저장
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=4)
        
        logger.info(f"송신 디바이스가 {device['name']}({device['mac']})로 설정되었습니다.")
        print(f"\n송신 디바이스가 설정되었습니다:")
        print(f"- 이름: {device['name']}")
        print(f"- MAC 주소: {device['mac']}")
        
        return True
        
    except Exception as e:
        logger.error(f"송신 디바이스 설정 중 오류 발생: {e}")
        print(f"오류가 발생했습니다: {e}")
        return False

def setup_recv_device(adapter_id=None):
    """수신 디바이스를 설정합니다"""
    try:
        print("\n" + "=" * 50)
        print("수신 디바이스 추가".center(50))
        print("=" * 50)
        
        # 설정된 수신용 어댑터 또는 기본값 사용
        if not adapter_id:
            # 설정 파일 읽기
            current_config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    current_config = json.load(f)
            
            adapter_id = current_config.get('recv_adapter', 'hci0')
        
        print(f"블루투스 어댑터 {adapter_id}를 사용하여 장치를 검색합니다.")
        device = select_bluetooth_device(adapter_id)
        
        if not device:
            logger.info("수신 디바이스 추가가 취소되었습니다.")
            print("설정이 취소되었습니다.")
            return False
        
        # 설정 파일 읽기
        current_config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                current_config = json.load(f)
        
        # 현재 디바이스 목록 가져오기
        recv_devices = current_config.get('recv_devices', [])
        
        # 이미 존재하는지 확인
        for existing_device in recv_devices:
            if existing_device.get('mac') == device['mac']:
                logger.warning(f"디바이스 {device['name']}({device['mac']})가 이미 등록되어 있습니다.")
                print(f"\n디바이스 {device['name']}({device['mac']})가 이미 등록되어 있습니다.")
                return False
        
        # 디바이스 추가
        recv_devices.append({
            'name': device['name'],
            'mac': device['mac']
        })
        
        # 업데이트된 목록 저장
        current_config['recv_devices'] = recv_devices
        
        # 설정 저장
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=4)
        
        logger.info(f"수신 디바이스 {device['name']}({device['mac']})가 추가되었습니다.")
        print(f"\n수신 디바이스가 추가되었습니다:")
        print(f"- 이름: {device['name']}")
        print(f"- MAC 주소: {device['mac']}")
        
        return True
        
    except Exception as e:
        logger.error(f"수신 디바이스 추가 중 오류 발생: {e}")
        print(f"오류가 발생했습니다: {e}")
        return False 