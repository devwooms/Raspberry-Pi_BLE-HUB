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
from ui.controllers.module_selector import ModuleSelector

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
                "0": "종료"
            }
            self.menu_view.show_menu_options(options)
            
            choice = input("\n선택: ")
            
            if choice == "2":
                self.daemon_menu()
            elif choice == "1":
                self.bluetooth_menu()
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
            
            # 메뉴 옵션 표시 - 그룹으로 나누고 헤더 추가
            print("\n[ 블루투스 모듈 ]")
            print("1. 블루투스 모듈 목록 표시")
            
            print("\n[ 수신 블루투스 설정 ]")
            print("2. 수신 블루투스 모듈 선택")
            print("3. 수신 블루투스 디바이스 추가")
            print("4. 수신 블루투스 디바이스 삭제")
            
            print("\n[ 송신 블루투스 설정 ]")
            print("5. 송신 블루투스 모듈 선택")
            print("6. 송신 블루투스 디바이스 선택")
            
            print("\n0. 이전 메뉴로 돌아가기")
            
            choice = input("\n선택: ")
            
            if choice == "1":
                self.show_bluetooth_modules()
            elif choice == "2":
                self.module_selector.select_source_module()
            elif choice == "5":
                self.module_selector.select_target_module()
            elif choice in ["3", "4", "6"]:
                self.menu_view.show_message("기능이 준비 중입니다.")
                self.menu_view.wait_for_input()
            elif choice == "0":
                break
            else:
                self.menu_view.show_error("잘못된 선택입니다. 다시 시도하세요.")
                self.menu_view.wait_for_input()
    
    def show_bluetooth_modules(self):
        """블루투스 모듈 목록 표시"""
        interfaces = self.module_selector.display_module_list()
        self.menu_view.wait_for_input() 