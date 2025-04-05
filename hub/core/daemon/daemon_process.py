#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 릴레이 데몬 프로세스
"""

import os
import sys
import time
import signal
import atexit
import argparse

def cleanup():
    """종료 시 정리 작업"""
    with open('blehub.log', 'a') as f:
        f.write(f'데몬 종료됨(PID: {os.getpid()})\n')

def signal_handler(signum, frame):
    """시그널 핸들러"""
    sys.exit(0)

def run_daemon():
    """데몬 메인 함수"""
    # 시그널 핸들러 등록
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)
    
    # 데몬 시작 메시지
    pid = os.getpid()
    print(f'데몬 프로세스 시작됨(PID: {pid})')
    with open('blehub.log', 'a') as f:
        f.write(f'데몬 시작됨(PID: {pid})\n')
    
    # 무한 루프로 계속 실행
    try:
        while True:
            with open('blehub.log', 'a') as f:
                f.write(f'데몬 실행 중(PID: {pid})\n')
            time.sleep(60)  # 1분마다 로그 기록
    except KeyboardInterrupt:
        print("데몬 종료 중...")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='블루투스 릴레이 데몬')
    parser.add_argument('--pid-file', help='PID 파일 경로', default='blehub.pid')
    parser.add_argument('--log-file', help='로그 파일 경로', default='blehub.log')
    args = parser.parse_args()
    
    # PID 파일 생성
    with open(args.pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # 데몬 실행
    run_daemon() 