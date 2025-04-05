#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 릴레이 서비스 - 수신 디바이스에서 송신 디바이스로 데이터 중계
"""

import os
import time
import threading
import subprocess
import signal
import atexit

class BluetoothRelayService:
    """블루투스 릴레이 서비스 클래스"""
    
    def __init__(self):
        """릴레이 서비스 초기화"""
        self.running = False
        self.relay_threads = []
        self.stop_event = threading.Event()
        
        # 정리 함수 등록
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def start_relay(self, source_module, target_module, receiving_devices, transmitting_device):
        """릴레이 시작
        
        Args:
            source_module (str): 수신용 블루투스 모듈 MAC 주소
            target_module (str): 송신용 블루투스 모듈 MAC 주소
            receiving_devices (list): 수신 디바이스 목록
            transmitting_device (dict): 송신 디바이스 정보
            
        Returns:
            bool: 성공 여부
        """
        if self.running:
            print("릴레이가 이미 실행 중입니다.")
            return False
        
        try:
            # 필요한 정보 검증
            if not source_module or not target_module:
                print("블루투스 모듈이 설정되지 않았습니다.")
                return False
                
            if not receiving_devices:
                print("수신 디바이스가 설정되지 않았습니다.")
                return False
                
            if not transmitting_device:
                print("송신 디바이스가 설정되지 않았습니다.")
                return False
            
            print("블루투스 릴레이 시작 중...")
            print(f"수신 모듈: {source_module}, 송신 모듈: {target_module}")
            print(f"수신 디바이스: {len(receiving_devices)}개, 송신 디바이스: {transmitting_device['name']}")
            
            # 릴레이 스레드 준비
            self.stop_event.clear()
            self.relay_threads = []
            
            # 각 수신 디바이스마다 릴레이 설정
            for device in receiving_devices:
                print(f"수신 디바이스 {device['name']} ({device['mac']})에 대한 릴레이 설정 중...")
                
                # bluetoothctl 설정 확인 (인터페이스 및 장치 연결 상태)
                self._check_and_setup_device(device['mac'])
                
                # 릴레이 스레드 시작
                thread = threading.Thread(
                    target=self._relay_data,
                    args=(device, transmitting_device, self.stop_event),
                    daemon=True
                )
                self.relay_threads.append(thread)
                thread.start()
            
            # 서비스 상태 업데이트
            self.running = True
            
            print("블루투스 릴레이가 성공적으로 시작되었습니다.")
            with open('blehub.log', 'a') as f:
                f.write(f"블루투스 릴레이 시작: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
            return True
            
        except Exception as e:
            print(f"릴레이 시작 중 오류 발생: {e}")
            self.stop_relay()  # 오류 발생 시 정리
            return False
    
    def stop_relay(self):
        """릴레이 중지
        
        Returns:
            bool: 성공 여부
        """
        if not self.running:
            print("릴레이가 실행 중이 아닙니다.")
            return False
            
        try:
            print("블루투스 릴레이 중지 중...")
            
            # 스레드 중지 신호 전송
            self.stop_event.set()
            
            # 모든 스레드 종료 대기
            for thread in self.relay_threads:
                thread.join(timeout=2.0)  # 최대 2초 대기
            
            # 실행 중인 프로세스 정리
            self._cleanup_processes()
            
            # 서비스 상태 업데이트
            self.running = False
            self.relay_threads = []
            
            print("블루투스 릴레이가 중지되었습니다.")
            with open('blehub.log', 'a') as f:
                f.write(f"블루투스 릴레이 중지: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
            return True
            
        except Exception as e:
            print(f"릴레이 중지 중 오류 발생: {e}")
            # 서비스 상태 강제 업데이트
            self.running = False
            self.relay_threads = []
            return False
    
    def is_running(self):
        """릴레이 실행 중 여부 확인
        
        Returns:
            bool: 실행 중 여부
        """
        return self.running
    
    def _check_and_setup_device(self, device_mac):
        """블루투스 장치 설정 확인 및 설정
        
        Args:
            device_mac (str): 장치 MAC 주소
        """
        try:
            # bluetoothctl로 장치 정보 확인
            info_cmd = ["bluetoothctl", "info", device_mac]
            info_result = subprocess.run(
                info_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            ).stdout
            
            # 연결 상태 확인
            if "Connected: yes" not in info_result:
                # 연결 시도
                print(f"장치 {device_mac}에 연결 시도 중...")
                connect_cmd = ["bluetoothctl", "connect", device_mac]
                subprocess.run(
                    connect_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                
            # 신뢰 상태 확인
            if "Trusted: no" in info_result:
                # 신뢰 설정
                print(f"장치 {device_mac} 신뢰 설정 중...")
                trust_cmd = ["bluetoothctl", "trust", device_mac]
                subprocess.run(
                    trust_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                
        except Exception as e:
            print(f"장치 설정 중 오류: {e}")
    
    def _relay_data(self, source_device, target_device, stop_event):
        """수신 장치에서 송신 장치로 데이터 릴레이
        
        Args:
            source_device (dict): 수신 장치 정보
            target_device (dict): 송신 장치 정보
            stop_event (threading.Event): 중지 이벤트
        """
        try:
            source_mac = source_device['mac']
            target_mac = target_device['mac']
            
            print(f"장치 {source_device['name']} ({source_mac})에서 {target_device['name']} ({target_mac})로 데이터 릴레이 시작...")
            
            # HID 프록시 실행
            cmd = [
                "bluetoothctl",
                "hid-relay",  # 참고: 이 명령은 실제 bluetoothctl에 존재하지 않음
                source_mac,
                target_mac
            ]
            
            # 진짜 HID 프록시 대신 시뮬레이션 코드 실행
            print(f"HID 릴레이 시뮬레이션 실행: {source_mac} -> {target_mac}")
            
            # 로그에 기록
            with open('blehub.log', 'a') as f:
                f.write(f"릴레이 시작: {source_device['name']} -> {target_device['name']}\n")
            
            # 릴레이 루프
            while not stop_event.is_set():
                # 여기서는 실제 릴레이 작업 대신 시뮬레이션
                print(".", end="", flush=True)
                time.sleep(2)
                
                # 모니터링 로직 (필요시 연결 상태 확인)
                if stop_event.wait(0.1):  # 0.1초 간격으로 중지 신호 확인
                    break
            
            print(f"\n장치 {source_device['name']}에서 {target_device['name']}로의 릴레이가 중지되었습니다.")
            
        except Exception as e:
            print(f"릴레이 작업 중 오류 발생: {e}")
    
    def _cleanup_processes(self):
        """실행 중인 프로세스 정리"""
        try:
            # bluetoothctl 프로세스 종료
            subprocess.run(
                ["pkill", "-f", "bluetoothctl"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            
            # 기타 정리 작업...
            
        except Exception as e:
            print(f"프로세스 정리 중 오류: {e}")
    
    def cleanup(self):
        """종료 시 정리 작업"""
        if self.running:
            self.stop_relay()
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        self.cleanup()
        exit(0) 