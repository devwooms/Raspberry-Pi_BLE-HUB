#!/usr/bin/env python3
import os
import subprocess
import time
import threading
import signal
import sys
from pathlib import Path

from blehub.utils.logger import logger

"""
BLE-HUB 블루투스 릴레이 모듈

블루투스 장치 간 데이터 릴레이 기능을 제공합니다.
"""

class BluetoothRelay:
    """블루투스 릴레이 클래스"""
    
    def __init__(self, source_adapter="hci0", target_adapter="hci1", target_device=None, config=None):
        """블루투스 릴레이 초기화
        
        Args:
            source_adapter (str): 소스 블루투스 어댑터 ID
            target_adapter (str): 타겟 블루투스 어댑터 ID
            target_device (str): 타겟 블루투스 장치 MAC 주소
            config (dict): 설정 정보
        """
        self.source_adapter = source_adapter
        self.target_adapter = target_adapter
        self.target_device = target_device
        self.config = config or {}
        self.running = False
        self.relay_thread = None
        self.stop_event = threading.Event()
    
    def start(self):
        """릴레이 시작"""
        if self.running:
            logger.warning("릴레이가 이미 실행 중입니다.")
            return False
        
        if not self.target_device:
            logger.error("타겟 장치가 지정되지 않았습니다.")
            return False
        
        # 어댑터 상태 확인
        if not self._check_adapters():
            return False
        
        # 릴레이 스레드 시작
        self.stop_event.clear()
        self.relay_thread = threading.Thread(target=self._relay_process)
        self.relay_thread.daemon = True
        self.relay_thread.start()
        
        self.running = True
        logger.info(f"블루투스 릴레이 시작: {self.source_adapter} -> {self.target_adapter} (장치: {self.target_device})")
        return True
    
    def stop(self):
        """릴레이 중지"""
        if not self.running:
            logger.warning("릴레이가 실행 중이지 않습니다.")
            return False
        
        # 스레드 중지 신호 전송
        self.stop_event.set()
        
        # 스레드 종료 대기
        if self.relay_thread and self.relay_thread.is_alive():
            self.relay_thread.join(timeout=5)
            if self.relay_thread.is_alive():
                logger.warning("릴레이 스레드가 정상적으로 종료되지 않았습니다.")
        
        self.running = False
        logger.info("블루투스 릴레이 중지")
        return True
    
    def status(self):
        """릴레이 상태 반환
        
        Returns:
            dict: 릴레이 상태 정보
        """
        return {
            'running': self.running,
            'source_adapter': self.source_adapter,
            'target_adapter': self.target_adapter,
            'target_device': self.target_device,
            'config': self.config
        }
    
    def _check_adapters(self):
        """블루투스 어댑터 상태 확인
        
        Returns:
            bool: 어댑터 상태 정상 여부
        """
        # 소스 어댑터 확인
        if not self._check_adapter(self.source_adapter):
            logger.error(f"소스 블루투스 어댑터 {self.source_adapter}를 사용할 수 없습니다.")
            return False
        
        # 타겟 어댑터 확인
        if not self._check_adapter(self.target_adapter):
            logger.error(f"타겟 블루투스 어댑터 {self.target_adapter}를 사용할 수 없습니다.")
            return False
        
        return True
    
    def _check_adapter(self, adapter_id):
        """블루투스 어댑터 상태 확인
        
        Args:
            adapter_id (str): 블루투스 어댑터 ID
            
        Returns:
            bool: 어댑터 상태 정상 여부
        """
        try:
            # 어댑터 상태 확인
            result = subprocess.run(
                ["hciconfig", adapter_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"블루투스 어댑터 {adapter_id} 상태 확인 실패: {result.stderr}")
                return False
            
            # 어댑터 활성화
            subprocess.run(
                ["hciconfig", adapter_id, "up"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return True
            
        except Exception as e:
            logger.error(f"블루투스 어댑터 {adapter_id} 확인 중 오류 발생: {e}")
            return False
    
    def _relay_process(self):
        """릴레이 프로세스 실행"""
        try:
            logger.info("릴레이 프로세스 시작 중...")
            
            # 여기에 실제 릴레이 로직 구현
            # 예시: gatttool, bluetoothctl 등을 사용하여 데이터 릴레이
            
            # 먼저 타겟 장치에 연결
            logger.info(f"타겟 장치 {self.target_device}에 연결 시도 중...")
            
            # 실제 구현에서는 여기에 hcitool, gatttool 등을 사용하여
            # 블루투스 장치 간 데이터를 중계하는 로직을 구현
            
            # 테스트를 위한 간단한
            while not self.stop_event.is_set():
                # 중계 작업 수행
                # 예시: 소스 어댑터로부터 데이터 수신 후 타겟 어댑터로 전송
                self._relay_data()
                
                # 일정 시간 대기
                time.sleep(1)
            
            logger.info("릴레이 프로세스 종료")
            
        except Exception as e:
            logger.error(f"릴레이 프로세스 실행 중 오류 발생: {e}")
            self.running = False
    
    def _relay_data(self):
        """데이터 릴레이 처리"""
        try:
            # 여기에 실제 데이터 릴레이 로직 구현
            # 예시: 소스 어댑터에서 데이터 읽기
            # data = self._read_from_source()
            
            # 타겟 어댑터로 데이터 쓰기
            # self._write_to_target(data)
            
            pass
            
        except Exception as e:
            logger.error(f"데이터 릴레이 중 오류 발생: {e}")
    
    def _read_from_source(self):
        """소스 어댑터에서 데이터 읽기
        
        Returns:
            bytes: 읽은 데이터
        """
        # 실제 구현에서는 소스 어댑터에서 데이터를 읽는 코드 구현
        return b''
    
    def _write_to_target(self, data):
        """타겟 어댑터로 데이터 쓰기
        
        Args:
            data (bytes): 쓸 데이터
            
        Returns:
            bool: 쓰기 성공 여부
        """
        # 실제 구현에서는 타겟 어댑터로 데이터를 쓰는 코드 구현
        return True

# 데몬 모드로 실행하기 위한 클래스
class BluetoothRelayDaemon:
    """블루투스 릴레이 데몬 클래스"""
    
    def __init__(self, config=None):
        """블루투스 릴레이 데몬 초기화
        
        Args:
            config (dict): 설정 정보
        """
        self.config = config or {}
        self.relay = None
        self.pid_file = Path("/tmp/blehub.pid")
        self.running = False
    
    def start(self):
        """데몬 시작"""
        if self._is_running():
            logger.warning("블루투스 릴레이 데몬이 이미 실행 중입니다.")
            return False
        
        # 설정 확인
        source_adapter = self.config.get("source_adapter", "hci0")
        target_adapter = self.config.get("target_adapter", "hci1")
        target_device = self.config.get("target_device")
        
        if not target_device:
            logger.error("타겟 장치가 설정되지 않았습니다.")
            return False
        
        # 릴레이 인스턴스 생성 및 시작
        self.relay = BluetoothRelay(
            source_adapter=source_adapter,
            target_adapter=target_adapter,
            target_device=target_device,
            config=self.config
        )
        
        # 릴레이 시작
        if not self.relay.start():
            logger.error("블루투스 릴레이 시작 실패")
            return False
        
        # PID 파일 생성
        try:
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.error(f"PID 파일 생성 실패: {e}")
            self.relay.stop()
            return False
        
        self.running = True
        logger.info("블루투스 릴레이 데몬 시작")
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        return True
    
    def stop(self):
        """데몬 중지"""
        if not self._is_running():
            logger.warning("블루투스 릴레이 데몬이 실행 중이 아닙니다.")
            return False
        
        # PID 파일 확인
        if not self.pid_file.exists():
            logger.warning("PID 파일을 찾을 수 없습니다.")
            return False
        
        try:
            # PID 파일에서 PID 읽기
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())
            
            # 프로세스 종료
            os.kill(pid, signal.SIGTERM)
            
            # PID 파일 삭제
            self.pid_file.unlink(missing_ok=True)
            
            logger.info("블루투스 릴레이 데몬 중지")
            return True
            
        except ProcessLookupError:
            logger.warning(f"PID {pid}의 프로세스를 찾을 수 없습니다.")
            self.pid_file.unlink(missing_ok=True)
            return False
            
        except Exception as e:
            logger.error(f"데몬 중지 중 오류 발생: {e}")
            return False
    
    def run(self):
        """데몬 실행"""
        if not self.start():
            return False
        
        try:
            # 메인 스레드는 계속 실행 상태 유지
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
            
        finally:
            # 종료 시 정리
            if self.relay and self.relay.running:
                self.relay.stop()
            
            # PID 파일 삭제
            self.pid_file.unlink(missing_ok=True)
            
            self.running = False
            logger.info("블루투스 릴레이 데몬 종료")
        
        return True
    
    def status(self):
        """데몬 상태 반환
        
        Returns:
            dict: 데몬 상태 정보
        """
        running = self._is_running()
        status_info = {
            'running': running,
            'pid_file': str(self.pid_file),
            'config': self.config
        }
        
        if running and self.relay:
            status_info.update(self.relay.status())
        
        return status_info
    
    def _is_running(self):
        """데몬 실행 중인지 확인
        
        Returns:
            bool: 실행 중 여부
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
            self.pid_file.unlink(missing_ok=True)
            return False
            
        except Exception as e:
            logger.error(f"데몬 상태 확인 중 오류 발생: {e}")
            return False
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러
        
        Args:
            signum (int): 시그널 번호
            frame: 프레임
        """
        if signum in (signal.SIGTERM, signal.SIGINT):
            logger.info(f"시그널 {signum} 수신, 종료 중...")
            self.running = False
            
            # 릴레이 중지
            if self.relay and self.relay.running:
                self.relay.stop()
            
            # PID 파일 삭제
            self.pid_file.unlink(missing_ok=True)
            
            # 프로세스 종료
            sys.exit(0) 