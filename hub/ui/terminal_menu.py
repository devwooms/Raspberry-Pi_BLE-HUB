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

class TerminalMenu:
    """터미널 메뉴 클래스"""
    
    def __init__(self):
        """터미널 메뉴 초기화"""
        # 모델 및 컨트롤러 초기화
        self.device_model = DeviceModel()
        self.daemon_controller = DaemonController()
        self.menu_view = MenuView()
        self.bluetooth_scanner = BluetoothScanner()
    
    def main_menu(self):
        """메인 메뉴 표시"""
        while True:
            self._clear_screen()
            
            # 상태 정보 가져오기
            daemon_status = self.daemon_controller.get_status()
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
            self._clear_screen()
            self.menu_view.show_header("데몬 관리")
            
            # 데몬 상태 표시
            daemon_status = self.daemon_controller.get_status()
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
                self.daemon_controller.start()
                self.menu_view.show_message("데몬이 시작되었습니다.")
                self.menu_view.wait_for_input()
            elif choice == "2":
                self.daemon_controller.stop()
                self.menu_view.show_message("데몬이 중지되었습니다.")
                self.menu_view.wait_for_input()
            elif choice == "3":
                self.daemon_controller.restart()
                self.menu_view.show_message("데몬이 재시작되었습니다.")
                self.menu_view.wait_for_input()
            elif choice == "4":
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
            self._clear_screen()
            self.menu_view.show_header("블루투스 관리")
            
            # 메뉴 옵션 표시
            options = {
                "1": "블루투스 모듈 목록 표시",
                "2": "소스 블루투스 인터페이스 선택",
                "3": "타겟 블루투스 인터페이스 선택",
                "4": "수신 블루투스 디바이스 추가",
                "5": "수신 블루투스 디바이스 삭제",
                "6": "송신 블루투스 디바이스 선택",
                "0": "이전 메뉴로 돌아가기"
            }
            self.menu_view.show_menu_options(options)
            
            choice = input("\n선택: ")
            
            if choice == "1":
                self.show_bluetooth_modules()
            elif choice in ["2", "3", "4", "5", "6"]:
                self.menu_view.show_message("기능이 준비 중입니다.")
                self.menu_view.wait_for_input()
            elif choice == "0":
                break
            else:
                self.menu_view.show_error("잘못된 선택입니다. 다시 시도하세요.")
                self.menu_view.wait_for_input()
    
    def show_bluetooth_modules(self):
        """블루투스 모듈 목록 표시"""
        self._clear_screen()
        self.menu_view.show_header("블루투스 모듈 목록")
        
        # 블루투스 인터페이스 스캔
        interfaces = self.bluetooth_scanner.get_bluetooth_interfaces()
        
        if not interfaces:
            self.menu_view.show_message("\n블루투스 모듈을 찾을 수 없습니다.")
        else:
            print("\n발견된 블루투스 모듈:")
            print("\n{:<5} {:<10} {:<20} {:<20}".format("번호", "인터페이스", "MAC 주소", "설명"))
            print("-" * 60)
            
            for idx, interface in enumerate(interfaces, 1):
                print("{:<5} {:<10} {:<20} {:<20}".format(
                    idx, 
                    interface['name'], 
                    interface['mac'], 
                    interface['type']
                ))
                
            # 현재 설정된 모듈 표시
            source_module = self.device_model.get_source_module()
            target_module = self.device_model.get_target_module()
            
            print("\n현재 선택된 모듈:")
            print(f"수신용: {source_module}")
            print(f"송신용: {target_module}")
            
        self.menu_view.wait_for_input()
    
    def _clear_screen(self):
        """화면 지우기"""
        os.system('cls' if os.name == 'nt' else 'clear') 