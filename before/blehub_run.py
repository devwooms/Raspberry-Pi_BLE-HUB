#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BLE-HUB 블루투스 릴레이 데몬 실행 스크립트
"""

import os
import sys
import time
import argparse
import logging
import signal
from datetime import datetime

# 로컬 모듈 임포트
from blehub.utils.logger import setup_logger
from blehub.bluetooth.scanner import BluetoothScanner
from blehub.configs.config_manager import ConfigManager
from blehub.daemon.daemon_control import start_bluetooth_relay
from blehub.menu.terminal_menu import run_terminal_menu

# 로그 설정
logger = setup_logger("blehub_daemon", "blehub.log")

def daemon_mode():
    """데몬 모드로 실행
    
    블루투스 릴레이 기능을 데몬으로 실행합니다.
    """
    logger.info("데몬 모드로 실행을 시작합니다.")
    
    # 설정 로드
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    if not config:
        logger.error("설정 파일이 존재하지 않거나 정상적이지 않습니다.")
        sys.exit(1)
    
    # 필수 설정 확인
    if "device_list" not in config or len(config["device_list"]) == 0:
        logger.error("타겟 장치가 설정되지 않았습니다.")
        sys.exit(1)
    
    # 종료 핸들러 설정
    def signal_handler(sig, frame):
        logger.info("데몬 종료 신호를 받았습니다.")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("블루투스 릴레이 시작 중...")
    
    try:
        # 블루투스 릴레이 시작
        start_bluetooth_relay()
        
        # 데몬 계속 실행
        while True:
            time.sleep(10)
            
    except Exception as e:
        logger.error(f"데몬 실행 중 오류 발생: {e}")
        sys.exit(1)

def parse_arguments():
    """명령줄 인수 파싱
    
    Returns:
        argparse.Namespace: 파싱된 인수
    """
    parser = argparse.ArgumentParser(description="BLE-HUB 블루투스 릴레이 데몬")
    parser.add_argument('--daemon', action='store_true', help='데몬 모드로 실행')
    parser.add_argument('--menu', action='store_true', help='터미널 메뉴 실행')
    
    return parser.parse_args()

def main():
    """메인 함수"""
    args = parse_arguments()
    
    if args.daemon:
        daemon_mode()
    elif args.menu or len(sys.argv) == 1:  # 인수가 없거나 --menu 인수가 있으면 메뉴 실행
        run_terminal_menu()
    else:
        print("알 수 없는 인수가 제공되었습니다. --daemon 또는 --menu 플래그를 사용하세요.")
        sys.exit(1)

if __name__ == "__main__":
    main() 