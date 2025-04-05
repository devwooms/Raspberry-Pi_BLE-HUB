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
    parser.add_argument('--daemon', action='store_true', help='데몬 모드로 실행')
    
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

if __name__ == "__main__":
    main() 