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
import json

class DaemonController:
    """데몬 제어 클래스"""
    
    def __init__(self):
        """데몬 컨트롤러 초기화"""
        # PID 파일과 설정 파일 경로를 절대 경로로 변경
        self.pid_file = os.path.abspath("blehub.pid")
        self.config_file = os.path.abspath("blehub_config.json")
        self.daemon_status = "중지됨"
        
        print(f"PID 파일 경로: {self.pid_file}")
        print(f"설정 파일 경로: {self.config_file}")
        
        # 시작 시 PID 파일 확인으로 상태 초기화
        if self._is_running():
            self.daemon_status = "실행 중"
            print(f"기존 데몬 감지됨 - 상태: {self.daemon_status}")
    
    def start(self, device_model=None):
        """데몬 시작
        
        Args:
            device_model: 디바이스 모델 인스턴스 (설정 저장용)
            
        Returns:
            bool: 성공 여부
        """
        if self._is_running():
            print("데몬이 이미 실행 중입니다.")
            return False
        
        # 설정 저장 (디바이스 모델이 제공된 경우)
        if device_model:
            self._save_config(device_model)
        
        # 실제 데몬 프로세스 시작
        try:
            # 현재 경로 확인
            current_dir = os.getcwd()
            print(f"현재 작업 디렉토리: {current_dir}")
            print(f"데몬 시작 시도 중...")
            
            # 데몬 프로세스 스크립트 파일 경로
            daemon_script_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "daemon_process.py"
            )
            
            print(f"데몬 스크립트 경로: {daemon_script_path}")
            
            # 데몬 프로세스 시작
            daemon_process = subprocess.Popen(
                [sys.executable, daemon_script_path, '--pid-file', self.pid_file],
                stdout=open('blehub.log', 'a'),
                stderr=subprocess.STDOUT,
                # 프로세스를 부모로부터 분리 (nohup 효과)
                start_new_session=True
            )
            
            # 데몬이 PID 파일을 생성할 시간을 줌
            time.sleep(1)
            
            # PID 파일 확인
            if not os.path.exists(self.pid_file):
                print("데몬 시작 실패: PID 파일이 생성되지 않았습니다.")
                return False
            
            self.daemon_status = "실행 중"
            
            # 로그에 기록
            with open('blehub.log', 'a') as f:
                f.write(f"데몬 컨트롤러에서 데몬 시작됨\n")
                
            print(f"데몬 시작됨")
            return True
        except Exception as e:
            print(f"데몬 시작 중 오류 발생: {e}")
            return False
    
    def stop(self, device_model=None):
        """데몬 중지
        
        Args:
            device_model: 디바이스 모델 인스턴스 (설정 초기화용)
            
        Returns:
            bool: 성공 여부
        """
        if not self._is_running():
            print("데몬이 실행 중이 아닙니다.")
            return False
        
        try:
            # PID 파일에서 PID 읽기
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            print(f"데몬 중지 시도 중 (PID: {pid})...")
            
            # 프로세스에 종료 신호 보내기
            os.kill(pid, signal.SIGTERM)
            
            # 종료 대기
            for _ in range(10):
                if not self._is_running():
                    break
                time.sleep(0.1)
            
            # 강제 종료
            if self._is_running():
                print(f"강제 종료 시도 중 (PID: {pid})...")
                os.kill(pid, signal.SIGKILL)
            
            # PID 파일 삭제
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                print("PID 파일 삭제됨")
            
            # 설정 파일은 삭제하지 않고 유지 (블루투스 설정 보존)
            # if os.path.exists(self.config_file):
            #     os.remove(self.config_file)
            #     print("설정 파일 삭제됨")
                
            # 디바이스 모델 초기화는 하지 않음 (설정 유지)
            # if device_model:
            #     self._clear_config(device_model)
            #     print("디바이스 모델 초기화됨")
                
            self.daemon_status = "중지됨"
            print("데몬이 중지되었습니다.")
            
            # 로그에 기록
            with open('blehub.log', 'a') as f:
                f.write(f"데몬 중지됨 (PID: {pid})\n")
                
            return True
            
        except (IOError, OSError):
            # PID 파일 삭제
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            # 설정 파일은 삭제하지 않고 유지 (블루투스 설정 보존)
            # if os.path.exists(self.config_file):
            #     os.remove(self.config_file)
                
            # 디바이스 모델 초기화는 하지 않음 (설정 유지)
            # if device_model:
            #     self._clear_config(device_model)
                
            self.daemon_status = "중지됨"
            return False
    
    def restart(self, device_model=None):
        """데몬 재시작
        
        Args:
            device_model: 디바이스 모델 인스턴스
            
        Returns:
            bool: 성공 여부
        """
        # 재시작 시 설정 유지를 위해 설정 저장
        if device_model and self._is_running():
            self._save_config(device_model)
            
        self.stop(None)  # 설정 초기화 없이 중지
        time.sleep(1)
        
        # 재시작 시 설정 복원
        if device_model:
            self._load_config(device_model)
            
        return self.start(None)  # 설정 저장 없이 시작
    
    def get_status(self, device_model=None):
        """데몬 상태 확인
        
        Args:
            device_model: 디바이스 모델 인스턴스
            
        Returns:
            str: 데몬 상태 ("실행 중" 또는 "중지됨")
        """
        is_running = self._is_running()
        
        if is_running:
            self.daemon_status = "실행 중"
            # 데몬이 실행 중이면 설정 로드 시도
            if device_model and os.path.exists(self.config_file):
                self._load_config(device_model)
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
                pid_str = f.read().strip()
                
            if not pid_str:
                print("PID 파일이 비어 있습니다.")
                if os.path.exists(self.pid_file):
                    os.remove(self.pid_file)
                return False
                
            pid = int(pid_str)
            print(f"PID 파일에서 읽은 PID: {pid}")
            
            # 프로세스 존재 확인 - ps 명령으로 이중 확인
            try:
                # 먼저 os.kill로 확인
                os.kill(pid, 0)
                
                # ps 명령으로 프로세스 확인
                process_check = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "pid="],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # ps 명령 결과 분석
                if process_check.returncode == 0 and process_check.stdout.strip():
                    print(f"프로세스 {pid}가 실행 중입니다.")
                    return True
                else:
                    print(f"프로세스 {pid}가 ps 명령으로 확인되지 않습니다.")
                    if os.path.exists(self.pid_file):
                        os.remove(self.pid_file)
                    return False
                    
            except OSError as e:
                # 프로세스가 존재하지 않음
                print(f"프로세스 {pid}가 존재하지 않습니다: {e}")
                # PID 파일 삭제
                if os.path.exists(self.pid_file):
                    os.remove(self.pid_file)
                return False
                
        except (IOError, OSError, ValueError) as e:
            # 로그 기록
            print(f"PID 파일 읽기 중 오류: {e}")
            with open('blehub.log', 'a') as f:
                f.write(f"PID 파일 읽기 중 오류: {e}\n")
            return False
            
    def _save_config(self, device_model):
        """현재 설정을 파일에 저장
        
        Args:
            device_model: 디바이스 모델 인스턴스
        """
        try:
            config = {
                'source_module': device_model.get_source_module(),
                'target_module': device_model.get_target_module(),
                'receiving_devices': device_model.get_receiving_devices(),
                'transmitting_device': device_model.get_transmitting_device()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {e}")
            
    def _load_config(self, device_model):
        """설정 파일에서 설정 불러오기
        
        Args:
            device_model: 디바이스 모델 인스턴스
            
        Returns:
            bool: 성공 여부
        """
        if not os.path.exists(self.config_file):
            return False
            
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            if 'source_module' in config and config['source_module']:
                device_model.set_source_module(config['source_module'])
                
            if 'target_module' in config and config['target_module']:
                device_model.set_target_module(config['target_module'])
                
            if 'receiving_devices' in config:
                # 기존 장치 초기화
                device_model._receiving_devices = []
                
                # 저장된 장치 추가
                for device in config['receiving_devices']:
                    if 'name' in device and 'mac' in device:
                        device_model.add_receiving_device(device['name'], device['mac'])
                
            if 'transmitting_device' in config and config['transmitting_device']:
                if 'name' in config['transmitting_device'] and 'mac' in config['transmitting_device']:
                    device_model.set_transmitting_device(
                        config['transmitting_device']['name'],
                        config['transmitting_device']['mac']
                    )
                    
            return True
                
        except Exception as e:
            print(f"설정 불러오기 중 오류 발생: {e}")
            return False
            
    def _clear_config(self, device_model):
        """디바이스 모델 설정 초기화
        
        Args:
            device_model: 디바이스 모델 인스턴스
        """
        device_model._source_module = None
        device_model._target_module = None
        device_model._receiving_devices = []
        device_model._transmitting_device = None

    def initialize_with_model(self, device_model):
        """초기화 시 디바이스 모델에 설정 로드
        
        Args:
            device_model: 디바이스 모델 인스턴스
        """
        # 데몬이 실행 중이고 설정 파일이 있으면 설정 로드
        if self._is_running() and os.path.exists(self.config_file):
            print("데몬 실행 중 - 설정 파일에서 블루투스 설정 로드 중...")
            if self._load_config(device_model):
                print("블루투스 설정 로드 완료")
            else:
                print("블루투스 설정 로드 실패") 