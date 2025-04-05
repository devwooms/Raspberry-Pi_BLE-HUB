#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메뉴 화면 표시 관련 클래스
"""

class MenuView:
    """메뉴 화면 표시 클래스"""
    
    def show_header(self, title):
        """헤더 표시
        
        Args:
            title (str): 표시할 제목
        """
        print("\n" + "=" * 60)
        print(title.center(60))
        print("=" * 60)
    
    def show_status_info(self, daemon_status, source_module, target_module, 
                      receiving_devices, transmitting_device):
        """상태 정보 표시
        
        Args:
            daemon_status (str): 데몬 상태
            source_module (str): 수신용 블루투스 모듈 정보
            target_module (str): 송신용 블루투스 모듈 정보
            receiving_devices (list): 수신 디바이스 목록
            transmitting_device (dict): 송신 디바이스 정보
        """
        print(f"\n데몬 상태 : {daemon_status}")
        print(f"수신용 블루투스 모듈 : {source_module}")
        print(f"송신용 블루투스 모듈 : {target_module}")
        
        print("\n수신 블루투스 디바이스 :")
        for i, device in enumerate(receiving_devices, 1):
            print(f"{i}. {device['name']} - {device['mac']}")
        
        print("\n송신 블루투스 디바이스 :")
        print(f"{transmitting_device['name']} - {transmitting_device['mac']}")
    
    def show_menu_options(self, options):
        """메뉴 옵션 표시
        
        Args:
            options (dict): 메뉴 옵션 (키: 선택번호, 값: 옵션 설명)
        """
        print("\n메뉴:")
        for key, value in options.items():
            print(f"{key}. {value}")
    
    def show_message(self, message):
        """메시지 표시
        
        Args:
            message (str): 표시할 메시지
        """
        print(message)
    
    def show_error(self, error_message):
        """오류 메시지 표시
        
        Args:
            error_message (str): 표시할 오류 메시지
        """
        print(error_message)
    
    def wait_for_input(self):
        """사용자 입력 대기"""
        input("\n계속하려면 Enter 키를 누르세요...") 