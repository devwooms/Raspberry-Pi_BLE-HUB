#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 릴레이 데몬 모듈
"""

import os
import sys
import time
import signal
import atexit

class BluetoothRelayDaemon:
    """블루투스 릴레이 데몬 클래스"""
    
    def __init__(self, pid_file='blehub.pid', stdout='blehub.log', stderr='blehub_error.log'):
        """데몬 초기화
        
        Args:
            pid_file (str): PID 파일 경로
            stdout (str): 표준 출력 경로
            stderr (str): 표준 에러 경로
        """
        self.pid_file = pid_file
        self.stdout = stdout
        self.stderr = stderr
        
        # 실행 중 플래그
        self.running = False
    
    def daemonize(self):
        """프로세스를 데몬화"""
        # 첫 번째 포크
        try:
            pid = os.fork()
            if pid > 0:
                # 부모 프로세스 종료
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"첫 번째 포크 실패: {e}\n")
            sys.exit(1)
        
        # 새 세션 생성 및 프로세스 그룹 리더 되기
        os.setsid()
        
        # 작업 디렉토리 변경
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # 파일 생성 마스크 설정
        os.umask(0)
        
        # 두 번째 포크
        try:
            pid = os.fork()
            if pid > 0:
                # 부모 프로세스 종료
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(f"두 번째 포크 실패: {e}\n")
            sys.exit(1)
        
        # 표준 파일 디스크립터 리다이렉션
        sys.stdout.flush()
        sys.stderr.flush()
        
        si = open(os.devnull, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
        # PID 파일 작성
        with open(self.pid_file, 'w+') as f:
            f.write(str(os.getpid()))
        
        # 종료 시 PID 파일 제거
        atexit.register(self.cleanup)
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGTERM, self.sigterm_handler)
    
    def cleanup(self):
        """종료 시 정리 작업"""
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)
    
    def sigterm_handler(self, signum, frame):
        """SIGTERM 시그널 핸들러"""
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """데몬 실행"""
        self.running = True
        
        # 메인 로직 구현
        while self.running:
            # 릴레이 작업 수행
            # TODO: 실제 릴레이 로직 구현
            time.sleep(1)

def main():
    """메인 함수"""
    daemon = BluetoothRelayDaemon()
    daemon.daemonize()
    daemon.run()

if __name__ == "__main__":
    main() 