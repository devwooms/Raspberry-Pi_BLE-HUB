#!/usr/bin/env python3
import os
import sys
import argparse
import time
import signal

from blehub.utils.logger import logger, set_log_level
from blehub.configs.config_manager import ConfigManager
from blehub.daemon.manager import DaemonManager
from blehub.bluetooth.relay import BluetoothRelayDaemon
from blehub.bluetooth.scanner import (
    list_bluetooth_modules,
    select_bluetooth_module
)
from blehub.menu.terminal_menu import (
    run_terminal_menu,
    parse_arguments,
    process_arguments
)

"""
BLE-HUB 메인 모듈

블루투스 릴레이 데몬 프로그램의 진입점입니다.
"""

def daemon_mode(config=None):
    """데몬 모드로 실행
    
    Args:
        config (dict): 설정 정보
    """
    logger.info("BLE-HUB 데몬을 시작합니다...")
    
    # 설정 로드
    if config is None:
        config_manager = ConfigManager()
        config = config_manager.get_full_config()
    
    # 데몬 인스턴스 생성
    daemon = BluetoothRelayDaemon(config)
    
    # 시그널 핸들러 등록
    def signal_handler(signum, frame):
        logger.info(f"시그널 {signum} 수신. 데몬 종료 중...")
        daemon.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 데몬 실행
    daemon.run()

def main():
    """메인 함수"""
    args = parse_arguments()
    
    # --daemon 인수로 데몬 모드 실행
    if hasattr(args, 'daemon') and args.daemon:
        daemon_mode()
        return
    
    # 다른 인수 처리
    success = process_arguments(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 