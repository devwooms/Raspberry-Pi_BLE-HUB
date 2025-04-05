#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import signal
import json
from pathlib import Path

from blehub.utils.logger import logger
from blehub.bluetooth.relay import BluetoothRelayDaemon

"""
BLE-HUB 데몬 관리 모듈

데몬 프로세스 시작, 중지, 상태 확인 등의 기능을 제공합니다.
"""

class DaemonManager:
    """데몬 관리 클래스"""
    
    def __init__(self, config_manager=None):
        """데몬 관리자 초기화
        
        Args:
            config_manager: 설정 관리자 인스턴스
        """
        self.config_manager = config_manager
        self.pid_file = Path("/tmp/blehub.pid")
        
    def is_running(self):
        """데몬이 실행 중인지 확인
        
        Returns:
            bool: 데몬 실행 중 여부
        """
        if not self.pid_file.exists():
            return False
        
        try:
            # PID 파일에서 PID 읽기
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())
            
            # 프로세스 존재 확인
            os.kill(pid, 0)  # 신호 0은 프로세스 존재 확인용
            return True
            
        except ProcessLookupError:
            # 프로세스가 존재하지 않음
            logger.warning(f"PID 파일은 존재하지만 PID {pid}의 프로세스를 찾을 수 없습니다.")
            self.pid_file.unlink(missing_ok=True)
            return False
            
        except Exception as e:
            logger.error(f"데몬 상태 확인 중 오류 발생: {e}")
            return False
    
    def start(self):
        """데몬 시작
        
        Returns:
            bool: 시작 성공 여부
        """
        # 이미 실행 중인지 확인
        if self.is_running():
            logger.warning("데몬이 이미 실행 중입니다.")
            return False
        
        # 설정 파일 존재 확인
        config = self._get_config()
        if not config:
            logger.error("설정 파일이 존재하지 않거나 정상적이지 않습니다.")
            return False
        
        # 필수 설정 확인
        if "target_device" not in config:
            logger.error("타겟 장치가 설정되지 않았습니다.")
            print("타겟 장치를 먼저 설정해야 합니다.")
            return False
        
        try:
            # 스크립트 경로 가져오기
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "blehub.py")
            
            # 실행 명령 구성
            cmd = [sys.executable, script_path, "--daemon"]
            
            # 백그라운드에서 실행
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # 프로세스 시작 확인
            time.sleep(1)
            if process.poll() is not None:
                stderr = process.stderr.read().decode("utf-8")
                logger.error(f"데몬 시작 실패: {stderr}")
                return False
            
            logger.info("데몬이 시작되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"데몬 시작 중 오류 발생: {e}")
            return False
    
    def stop(self):
        """데몬 중지
        
        Returns:
            bool: 중지 성공 여부
        """
        if not self.is_running():
            logger.warning("데몬이 실행 중이 아닙니다.")
            return False
        
        try:
            # PID 파일에서 PID 읽기
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())
            
            # 프로세스 종료
            logger.info(f"PID {pid}의 프로세스 종료 시도 중...")
            os.kill(pid, signal.SIGTERM)
            
            # 프로세스 종료 확인
            for _ in range(5):
                time.sleep(1)
                try:
                    # 프로세스 상태 확인
                    os.kill(pid, 0)
                except ProcessLookupError:
                    # 프로세스가 종료됨
                    logger.info("데몬이 정상적으로 종료되었습니다.")
                    self.pid_file.unlink(missing_ok=True)
                    return True
            
            # 프로세스가 종료되지 않음
            logger.warning(f"프로세스가 SIGTERM에 응답하지 않습니다. SIGKILL 시도 중...")
            os.kill(pid, signal.SIGKILL)
            
            # 프로세스 종료 확인
            time.sleep(1)
            try:
                os.kill(pid, 0)
                logger.error("데몬을 종료할 수 없습니다.")
                return False
            except ProcessLookupError:
                logger.info("데몬이 강제 종료되었습니다.")
                self.pid_file.unlink(missing_ok=True)
                return True
            
        except ProcessLookupError:
            logger.warning(f"PID {pid}의 프로세스를 찾을 수 없습니다.")
            self.pid_file.unlink(missing_ok=True)
            return True
            
        except Exception as e:
            logger.error(f"데몬 중지 중 오류 발생: {e}")
            return False
    
    def restart(self):
        """데몬 재시작
        
        Returns:
            bool: 재시작 성공 여부
        """
        logger.info("데몬 재시작 중...")
        
        # 먼저 중지
        if self.is_running():
            if not self.stop():
                logger.error("데몬 중지 실패")
                return False
        
        # 잠시 대기
        time.sleep(1)
        
        # 시작
        if not self.start():
            logger.error("데몬 시작 실패")
            return False
        
        logger.info("데몬이 재시작되었습니다.")
        return True
    
    def status(self):
        """데몬 상태 반환
        
        Returns:
            dict: 데몬 상태 정보
        """
        running = self.is_running()
        
        # 기본 상태 정보
        status_info = {
            'running': running,
            'pid_file': str(self.pid_file)
        }
        
        # 설정 정보 추가
        config = self._get_config()
        if config:
            # 수신용 블루투스 어댑터 정보
            status_info['source_adapter'] = config.get('source_adapter', 'hci0')
            
            # 송신용 블루투스 어댑터 정보
            status_info['target_adapter'] = config.get('target_adapter', 'hci1')
            
            # 수신용 블루투스 디바이스 목록 (여러 개 가능)
            source_devices = config.get('source_devices', [])
            status_info['source_devices'] = source_devices
            
            # 송신 대상 블루투스 디바이스
            status_info['target_device'] = config.get('target_device', '알 수 없음')
        
        # PID 정보 추가
        if running and self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    status_info['pid'] = int(f.read().strip())
            except Exception:
                status_info['pid'] = '알 수 없음'
        
        logger.info(f"데몬 상태: {'실행 중' if running else '중지됨'}")
        return status_info
    
    def _get_config(self):
        """설정 정보 가져오기
        
        Returns:
            dict: 설정 정보
        """
        if self.config_manager:
            return self.config_manager.get_full_config()
        
        # 설정 파일 경로
        config_file = Path.home() / ".blehub" / "config.json"
        
        if not config_file.exists():
            logger.error(f"설정 파일 {config_file}이 존재하지 않습니다.")
            return None
        
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"설정 파일 읽기 중 오류 발생: {e}")
            return None

# 전역 데몬 관리자 인스턴스
_daemon_manager = None

def get_daemon_manager():
    """전역 데몬 관리자 인스턴스를 반환합니다
    
    Returns:
        DaemonManager: 데몬 관리자 인스턴스
    """
    global _daemon_manager
    if _daemon_manager is None:
        _daemon_manager = DaemonManager()
    return _daemon_manager

# 편의 함수들
def is_running():
    """데몬이 실행 중인지 확인합니다"""
    return get_daemon_manager().is_running()

def start_daemon():
    """데몬을 시작합니다"""
    return get_daemon_manager().start()

def stop_daemon():
    """실행 중인 데몬을 중지합니다"""
    return get_daemon_manager().stop()

def restart_daemon():
    """데몬을 재시작합니다"""
    return get_daemon_manager().restart()

def status_daemon():
    """데몬의 상태를 확인합니다"""
    return get_daemon_manager().status() 