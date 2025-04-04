#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
터미널 기반 메뉴 시스템 모듈
"""

import os
from ui.views.menu_view import MenuView
from ui.models.device_model import DeviceModel
from core.daemon.daemon_controller import DaemonController
from core.bluetooth.scanner import BluetoothScanner
from core.bluetooth.module_manager import BluetoothModuleManager
from core.bluetooth.device_manager import BluetoothDeviceManager
from core.bluetooth.relay_service import BluetoothRelayService
from ui.controllers.module_selector import ModuleSelector
from ui.controllers.device_controller import DeviceController

class TerminalMenu:
    """터미널 메뉴 클래스"""
    
    def __init__(self):
        """터미널 메뉴 초기화"""
        # 모델 및 컨트롤러 초기화
        self.device_model = DeviceModel()
        self.daemon_controller = DaemonController()
        self.menu_view = MenuView()
        self.bluetooth_scanner = BluetoothScanner()
        
        # 모듈화된 컴포넌트 초기화
        self.module_manager = BluetoothModuleManager(self.bluetooth_scanner, self.device_model)
        self.module_selector = ModuleSelector(self.module_manager, self.menu_view)
        
        # 블루투스 디바이스 관련 컴포넌트 초기화
        self.device_manager = BluetoothDeviceManager(self.bluetooth_scanner)
        self.device_controller = DeviceController(self.device_manager, self.device_model, self.menu_view)
        
        # 릴레이 서비스 초기화
        self.relay_service = BluetoothRelayService()
        
        # 프로그램 시작 시 설정 파일에서 블루투스 설정 로드
        self.load_config()
    
    def load_config(self):
        """설정 파일에서 설정 로드"""
        # 데몬 컨트롤러의 설정 파일 경로
        config_file = self.daemon_controller.config_file
        
        # 항상 설정 파일 로드 시도 (데몬 상태와 관계없이)
        if os.path.exists(config_file):
            print(f"설정 파일 발견: {config_file}")
            print("블루투스 설정 로드 중...")
            
            # 설정 로드
            if self.daemon_controller._load_config(self.device_model):
                print("블루투스 설정 로드 성공!")
            else:
                print("블루투스 설정 로드 실패!")
        else:
            print(f"설정 파일이 없습니다: {config_file}")
            
        # 데몬 상태 업데이트
        self.daemon_controller.get_status(self.device_model)
    
    def main_menu(self):
        """메인 메뉴 표시"""
        while True:
            self.menu_view.clear_screen()
            
            # 상태 정보 가져오기
            daemon_status = self.daemon_controller.get_status(self.device_model)
            source_module = self.device_model.get_source_module()
            target_module = self.device_model.get_target_module()
            receiving_devices = self.device_model.get_receiving_devices()
            transmitting_device = self.device_model.get_transmitting_device()
            
            # 메인 메뉴 표시
            self.menu_view.show_header("BLE-HUB")
            self.menu_view.show_status_info(daemon_status, source_module, target_module, 
                                         receiving_devices, transmitting_device)
            
            # 메뉴 옵션 표시
            options = {
                "1": "블루투스 관리",
                "2": "데몬 관리",
                "3": "수신-송신 연결",
                "0": "종료"
            }
            self.menu_view.show_menu_options(options)
            
            choice = input("\n선택: ")
            
            if choice == "2":
                self.daemon_menu()
            elif choice == "1":
                self.bluetooth_menu()
            elif choice == "3":
                self.connection_menu()
            elif choice == "0":
                print("프로그램을 종료합니다.")
                break
            else:
                self.menu_view.show_error("잘못된 선택입니다. 다시 시도하세요.")
                self.menu_view.wait_for_input()
    
    def daemon_menu(self):
        """데몬 관리 메뉴"""
        while True:
            self.menu_view.clear_screen()
            self.menu_view.show_header("데몬 관리")
            
            # 데몬 상태 표시
            daemon_status = self.daemon_controller.get_status(self.device_model)
            print(f"\n현재 데몬 상태: {daemon_status}")
            
            # 메뉴 옵션 표시
            options = {
                "1": "데몬 시작",
                "2": "데몬 중지",
                "3": "데몬 재시작",
                "4": "데몬 상태 확인",
                "0": "이전 메뉴로 돌아가기"
            }
            self.menu_view.show_menu_options(options)
            
            choice = input("\n선택: ")
            
            if choice == "1":
                self.daemon_controller.start(self.device_model)
                self.menu_view.show_message("데몬이 시작되었습니다.")
                self.menu_view.wait_for_input()
            elif choice == "2":
                self.daemon_controller.stop(self.device_model)
                self.menu_view.show_message("데몬이 중지되었습니다.")
                self.menu_view.wait_for_input()
            elif choice == "3":
                self.daemon_controller.restart(self.device_model)
                self.menu_view.show_message("데몬이 재시작되었습니다.")
                self.menu_view.wait_for_input()
            elif choice == "4":
                daemon_status = self.daemon_controller.get_status(self.device_model)
                self.menu_view.show_message(f"\n데몬 상태: {daemon_status}")
                self.menu_view.wait_for_input()
            elif choice == "0":
                break
            else:
                self.menu_view.show_error("잘못된 선택입니다. 다시 시도하세요.")
                self.menu_view.wait_for_input()
    
    def bluetooth_menu(self):
        """블루투스 관리 메뉴"""
        while True:
            self.menu_view.clear_screen()
            self.menu_view.show_header("블루투스 관리")
            
            # 메뉴 옵션 표시
            options = {
                "1": "수신용 블루투스 모듈 선택",
                "2": "송신용 블루투스 모듈 선택",
                "3": "수신 블루투스 디바이스 추가",
                "4": "수신 블루투스 디바이스 삭제",
                "5": "수신 블루투스 디바이스 목록",
                "6": "송신 블루투스 디바이스 선택",
                "7": "송신 블루투스 디바이스 삭제",
                "0": "이전 메뉴로 돌아가기"
            }
            self.menu_view.show_menu_options(options)
            
            choice = input("\n선택: ")
            
            if choice == "1":
                self.module_selector.select_source_module()
            elif choice == "2":
                self.module_selector.select_target_module()
            elif choice == "3":
                self.device_controller.add_receiving_device()
            elif choice == "4":
                self.device_controller.remove_receiving_device()
            elif choice == "5":
                self.show_receiving_devices()
            elif choice == "6":
                self.device_controller.select_transmitting_device()
            elif choice == "7":
                self.device_controller.remove_transmitting_device()
            elif choice == "0":
                break
            else:
                self.menu_view.show_error("잘못된 선택입니다. 다시 시도하세요.")
                self.menu_view.wait_for_input()
                
    def show_receiving_devices(self):
        """수신 블루투스 디바이스 목록 표시"""
        self.menu_view.clear_screen()
        self.menu_view.show_header("수신 블루투스 디바이스 목록")
        
        receiving_devices = self.device_model.get_receiving_devices()
        
        if not receiving_devices:
            self.menu_view.show_message("\n등록된 수신 디바이스가 없습니다.")
        else:
            self.menu_view.show_message("\n== 등록된 수신 디바이스 ==")
            for i, device in enumerate(receiving_devices):
                self.menu_view.show_message(f"{i+1}. {device['name']} - {device['mac']}")
        
        self.menu_view.wait_for_input()
    
    def connection_menu(self):
        """수신-송신 연결 메뉴"""
        while True:
            self.menu_view.clear_screen()
            self.menu_view.show_header("수신-송신 연결")
            
            # 현재 상태 정보 표시
            source_module = self.device_model.get_source_module()
            target_module = self.device_model.get_target_module()
            receiving_devices = self.device_model.get_receiving_devices()
            transmitting_device = self.device_model.get_transmitting_device()
            
            # 연결 상태 정보 표시
            self.menu_view.show_message("\n== 연결 상태 ==")
            source_info = f"{source_module}" if source_module else "설정되지 않음"
            target_info = f"{target_module}" if target_module else "설정되지 않음"
            self.menu_view.show_message(f"수신용 블루투스 모듈: {source_info}")
            self.menu_view.show_message(f"송신용 블루투스 모듈: {target_info}")
            
            # 연결된 디바이스 정보
            if receiving_devices:
                self.menu_view.show_message("\n== 수신 디바이스 ==")
                for i, device in enumerate(receiving_devices):
                    self.menu_view.show_message(f"{i+1}. {device['name']} ({device['mac']})")
            else:
                self.menu_view.show_message("\n수신 디바이스 없음")
                
            self.menu_view.show_message("\n== 송신 디바이스 ==")
            if transmitting_device:
                self.menu_view.show_message(f"{transmitting_device['name']} ({transmitting_device['mac']})")
            else:
                self.menu_view.show_message("설정되지 않음")
            
            # 릴레이 상태 표시
            relay_status = "실행 중" if self.relay_service.is_running() else "중지됨"
            self.menu_view.show_message(f"\n== 릴레이 상태: {relay_status} ==")
            
            # 메뉴 옵션 표시
            options = {
                "1": "수신-송신 연결 시작",
                "2": "수신-송신 연결 해제",
                "0": "이전 메뉴로 돌아가기"
            }
            self.menu_view.show_menu_options(options)
            
            choice = input("\n선택: ")
            
            if choice == "1":
                self.start_connection()
            elif choice == "2":
                self.stop_connection()
            elif choice == "0":
                break
            else:
                self.menu_view.show_error("잘못된 선택입니다. 다시 시도하세요.")
                self.menu_view.wait_for_input()
    
    def start_connection(self):
        """수신-송신 연결 시작"""
        self.menu_view.clear_screen()
        self.menu_view.show_header("수신-송신 연결 시작")
        
        # 기본 검증
        if not self._validate_connection_requirements():
            return
            
        # 릴레이가 이미 실행 중인지 확인
        if self.relay_service.is_running():
            self.menu_view.show_error("릴레이가 이미 실행 중입니다.")
            self.menu_view.wait_for_input()
            return
            
        # 릴레이 시작
        source_module = self.device_model.get_source_module()
        target_module = self.device_model.get_target_module()
        receiving_devices = self.device_model.get_receiving_devices()
        transmitting_device = self.device_model.get_transmitting_device()
        
        self.menu_view.show_message("\n블루투스 릴레이 설정 중...")
        self.menu_view.show_message(f"수신 디바이스 {len(receiving_devices)}개를 {transmitting_device['name']}로 릴레이합니다.")
        
        # 데몬 상태 확인
        daemon_status = self.daemon_controller.get_status(self.device_model)
        if daemon_status != "실행 중":
            confirm = input("\n데몬이 실행 중이 아닙니다. 데몬을 시작하시겠습니까? (y/n): ")
            if confirm.lower() == 'y':
                self.daemon_controller.start(self.device_model)
            else:
                self.menu_view.show_message("데몬 시작 없이 릴레이를 시도합니다.")
        
        # 릴레이 시작
        if self.relay_service.start_relay(
            source_module, 
            target_module, 
            receiving_devices, 
            transmitting_device
        ):
            self.menu_view.show_message("\n릴레이가 성공적으로 시작되었습니다!")
            self.menu_view.show_message("이제 수신 디바이스의 입력이 송신 디바이스로 전달됩니다.")
        else:
            self.menu_view.show_error("\n릴레이 시작에 실패했습니다.")
        
        self.menu_view.wait_for_input()
    
    def stop_connection(self):
        """수신-송신 연결 해제"""
        self.menu_view.clear_screen()
        self.menu_view.show_header("수신-송신 연결 해제")
        
        # 릴레이가 실행 중인지 확인
        if not self.relay_service.is_running():
            self.menu_view.show_error("릴레이가 실행 중이 아닙니다.")
            self.menu_view.wait_for_input()
            return
            
        # 릴레이 중지
        self.menu_view.show_message("\n릴레이를 중지 중...")
        
        if self.relay_service.stop_relay():
            self.menu_view.show_message("\n릴레이가 성공적으로 중지되었습니다.")
            
            # 데몬 중지 여부 확인
            confirm = input("데몬도 함께 중지하시겠습니까? (y/n): ")
            if confirm.lower() == 'y':
                self.daemon_controller.stop(self.device_model)
                self.menu_view.show_message("데몬이 중지되었습니다.")
        else:
            self.menu_view.show_error("\n릴레이 중지에 실패했습니다.")
        
        self.menu_view.wait_for_input()
    
    def _validate_connection_requirements(self):
        """연결에 필요한 요구사항 검증
        
        Returns:
            bool: 검증 성공 여부
        """
        # 모듈 확인
        source_module = self.device_model.get_source_module()
        target_module = self.device_model.get_target_module()
        receiving_devices = self.device_model.get_receiving_devices()
        transmitting_device = self.device_model.get_transmitting_device()
        
        if not source_module:
            self.menu_view.show_error("수신용 블루투스 모듈이 설정되지 않았습니다.")
            self.menu_view.show_message("블루투스 관리 메뉴에서 수신용 모듈을 먼저 설정하세요.")
            self.menu_view.wait_for_input()
            return False
            
        if not target_module:
            self.menu_view.show_error("송신용 블루투스 모듈이 설정되지 않았습니다.")
            self.menu_view.show_message("블루투스 관리 메뉴에서 송신용 모듈을 먼저 설정하세요.")
            self.menu_view.wait_for_input()
            return False
            
        if not receiving_devices:
            self.menu_view.show_error("수신 디바이스가 설정되지 않았습니다.")
            self.menu_view.show_message("블루투스 관리 메뉴에서 수신 디바이스를 먼저 추가하세요.")
            self.menu_view.wait_for_input()
            return False
            
        if not transmitting_device:
            self.menu_view.show_error("송신 디바이스가 설정되지 않았습니다.")
            self.menu_view.show_message("블루투스 관리 메뉴에서 송신 디바이스를 먼저 선택하세요.")
            self.menu_view.wait_for_input()
            return False
            
        return True 