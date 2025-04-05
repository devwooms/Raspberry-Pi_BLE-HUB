#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데몬 제어 관련 클래스
"""

import os
import signal
import subprocess
import time
import sys

class DaemonController:
    """데몬 제어 클래스"""
    
    def __init__(self):
        """데몬 컨트롤러 초기화"""
        self.pid_file = "blehub.pid"
        self.daemon_status = "중지됨"
        
        # 시작 시 PID 파일 확인으로 상태 초기화
        if self._is_running():
            self.daemon_status = "실행 중"
    
    def start(self):
        """데몬 시작"""
        if self._is_running():
            return False
        
        # 실제 구현에서는 데몬 프로세스 시작
        # subprocess.Popen([sys.executable, "-m", "core.bluetooth.relay_daemon"])
        
        # 샘플 구현 (실제 작동은 안함)
        with open(self.pid_file, 'w') as f:
            f.write("12345")
        
        self.daemon_status = "실행 중"
        return True
    
    def stop(self):
        """데몬 중지"""
        if not self._is_running():
            return False
        
        try:
            # PID 파일에서 PID 읽기
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 프로세스에 종료 신호 보내기
            os.kill(pid, signal.SIGTERM)
            
            # 종료 대기
            for _ in range(10):
                if not self._is_running():
                    break
                time.sleep(0.1)
            
            # 강제 종료
            if self._is_running():
                os.kill(pid, signal.SIGKILL)
            
            # PID 파일 삭제
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                
            self.daemon_status = "중지됨"
            return True
            
        except (IOError, OSError):
            # PID 파일 삭제
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            self.daemon_status = "중지됨"
            return False
    
    def restart(self):
        """데몬 재시작"""
        self.stop()
        time.sleep(1)
        return self.start()
    
    def get_status(self):
        """데몬 상태 확인
        
        Returns:
            str: 데몬 상태 ("실행 중" 또는 "중지됨")
        """
        if self._is_running():
            self.daemon_status = "실행 중"
        else:
            self.daemon_status = "중지됨"
            
        return self.daemon_status
    
    def _is_running(self):
        """데몬 실행 여부 확인
        
        Returns:
            bool: 데몬 실행 중 여부
        """
        # PID 파일 존재 확인
        if not os.path.exists(self.pid_file):
            return False
        
        try:
            # PID 파일에서 PID 읽기
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 프로세스 존재 확인
            os.kill(pid, 0)
            return True
        except (IOError, OSError):
            return False 