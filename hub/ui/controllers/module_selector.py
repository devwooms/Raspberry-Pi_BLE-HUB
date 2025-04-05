#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 모듈 선택 UI 컨트롤러
"""

class ModuleSelector:
    """블루투스 모듈 선택을 담당하는 UI 컨트롤러"""
    
    def __init__(self, module_manager, menu_view):
        """초기화
        
        Args:
            module_manager: 블루투스 모듈 관리자 인스턴스
            menu_view: 메뉴 뷰 인스턴스
        """
        self.module_manager = module_manager
        self.menu_view = menu_view
    
    def display_module_list(self, clear_screen=True):
        """블루투스 모듈 목록 표시
        
        Args:
            clear_screen (bool): 화면 지우기 여부
            
        Returns:
            list: 표시된 인터페이스 목록 또는 빈 리스트
        """
        if clear_screen:
            self.menu_view.clear_screen()
            
        self.menu_view.show_header("블루투스 모듈 목록")
        
        # 블루투스 인터페이스 가져오기
        interfaces = self.module_manager.get_interfaces()
        
        if not interfaces:
            self.menu_view.show_message("\n블루투스 모듈을 찾을 수 없습니다.")
            return []
            
        # 현재 설정된 모듈 표시
        source_module = self.module_manager.get_current_source_module()
        target_module = self.module_manager.get_current_target_module()
        
        print("\n발견된 블루투스 모듈:")
        print("\n{:<5} {:<10} {:<20}".format("번호", "인터페이스", "MAC 주소"))
        print("-" * 40)
        
        for idx, interface in enumerate(interfaces, 1):
            print("{:<5} {:<10} {:<20}".format(
                idx, 
                interface['name'], 
                interface['mac']
            ))
            
        print("\n현재 선택된 모듈:")
        print(f"수신용: {source_module if source_module else '없음'}")
        print(f"송신용: {target_module if target_module else '없음'}")
        
        return interfaces
        
    def select_source_module(self):
        """수신 블루투스 모듈 선택 UI"""
        self.menu_view.clear_screen()
        self.menu_view.show_header("수신 블루투스 모듈 선택")
        
        # 블루투스 인터페이스 가져오기
        interfaces = self.module_manager.get_interfaces()
        
        if not interfaces:
            self.menu_view.show_message("\n블루투스 모듈을 찾을 수 없습니다.")
            self.menu_view.wait_for_input()
            return
            
        # 현재 선택된 모듈 표시
        current_module = self.module_manager.get_current_source_module()
        print(f"\n현재 선택된 수신용 모듈: {current_module if current_module else '없음'}")
        
        # 사용 가능한 모듈 목록 표시
        print("\n사용 가능한 블루투스 모듈:")
        print("\n{:<5} {:<10} {:<20}".format("번호", "인터페이스", "MAC 주소"))
        print("-" * 40)
        
        for idx, interface in enumerate(interfaces, 1):
            print("{:<5} {:<10} {:<20}".format(
                idx, 
                interface['name'], 
                interface['mac']
            ))
            
        # 모듈 선택
        print("\n0. 이전 메뉴로 돌아가기")
        choice = input("\n선택할 수신용 블루투스 모듈 번호: ")
        
        try:
            choice_num = int(choice)
            
            if choice_num == 0:
                return
                
            selected_interface = self.module_manager.get_interface_by_index(choice_num)
            if selected_interface:
                if self.module_manager.set_source_module(selected_interface):
                    self.menu_view.show_message(f"\n수신용 블루투스 모듈이 {selected_interface['name']} ({selected_interface['mac']})로 설정되었습니다.")
                else:
                    self.menu_view.show_error("모듈 설정 중 오류가 발생했습니다.")
            else:
                self.menu_view.show_error("잘못된 번호입니다.")
        except ValueError:
            self.menu_view.show_error("숫자를 입력해주세요.")
            
        self.menu_view.wait_for_input()
        
    def select_target_module(self):
        """송신 블루투스 모듈 선택 UI"""
        self.menu_view.clear_screen()
        self.menu_view.show_header("송신 블루투스 모듈 선택")
        
        # 블루투스 인터페이스 가져오기
        interfaces = self.module_manager.get_interfaces()
        
        if not interfaces:
            self.menu_view.show_message("\n블루투스 모듈을 찾을 수 없습니다.")
            self.menu_view.wait_for_input()
            return
            
        # 현재 선택된 모듈 표시
        current_module = self.module_manager.get_current_target_module()
        print(f"\n현재 선택된 송신용 모듈: {current_module if current_module else '없음'}")
        
        # 사용 가능한 모듈 목록 표시
        print("\n사용 가능한 블루투스 모듈:")
        print("\n{:<5} {:<10} {:<20}".format("번호", "인터페이스", "MAC 주소"))
        print("-" * 40)
        
        for idx, interface in enumerate(interfaces, 1):
            print("{:<5} {:<10} {:<20}".format(
                idx, 
                interface['name'], 
                interface['mac']
            ))
            
        # 모듈 선택
        print("\n0. 이전 메뉴로 돌아가기")
        choice = input("\n선택할 송신용 블루투스 모듈 번호: ")
        
        try:
            choice_num = int(choice)
            
            if choice_num == 0:
                return
                
            selected_interface = self.module_manager.get_interface_by_index(choice_num)
            if selected_interface:
                if self.module_manager.set_target_module(selected_interface):
                    self.menu_view.show_message(f"\n송신용 블루투스 모듈이 {selected_interface['name']} ({selected_interface['mac']})로 설정되었습니다.")
                else:
                    self.menu_view.show_error("모듈 설정 중 오류가 발생했습니다.")
            else:
                self.menu_view.show_error("잘못된 번호입니다.")
        except ValueError:
            self.menu_view.show_error("숫자를 입력해주세요.")
            
        self.menu_view.wait_for_input() 