#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 모듈 선택 컨트롤러
"""

import os
import json

class ModuleSelector:
    """블루투스 모듈 선택 컨트롤러"""
    
    def __init__(self, module_manager, menu_view):
        """모듈 선택기 초기화
        
        Args:
            module_manager: 블루투스 모듈 관리자
            menu_view: 메뉴 뷰
        """
        self.module_manager = module_manager
        self.menu_view = menu_view
        self.config_file = os.path.abspath("blehub_config.json")
    
    def display_module_list(self):
        """블루투스 모듈 목록 표시
        
        Returns:
            list: 검색된 인터페이스 목록
        """
        # 블루투스 인터페이스 검색
        self.menu_view.show_message("\n블루투스 인터페이스 검색 중...")
        interfaces = self.module_manager.get_interfaces()
        
        if not interfaces:
            self.menu_view.show_error("블루투스 인터페이스를 찾을 수 없습니다.")
            return []
        
        # 인터페이스 목록 표시
        self.menu_view.show_message("\n== 블루투스 인터페이스 목록 ==")
        for i, interface in enumerate(interfaces):
            self.menu_view.show_message(f"{i+1}. {interface['name']} - {interface['mac']}")
        
        return interfaces
    
    def select_source_module(self):
        """수신용 블루투스 모듈 선택"""
        interfaces = self.display_module_list()
        
        if not interfaces:
            return
        
        # 사용자 선택
        while True:
            choice = input("\n수신용으로 사용할 모듈 번호를 선택하세요 (0: 취소): ")
            
            if choice == "0":
                return
                
            try:
                index = int(choice) - 1
                if 0 <= index < len(interfaces):
                    # 모델에 선택한 모듈 설정
                    selected = interfaces[index]
                    self.module_manager.set_source_module(selected['mac'])
                    self.menu_view.show_message(f"\n수신용 모듈로 {selected['name']} ({selected['mac']})를 선택했습니다.")
                    
                    # 설정 변경 시 설정 파일 저장
                    self._save_config()
                    
                    self.menu_view.wait_for_input()
                    return
                else:
                    self.menu_view.show_error("잘못된 번호입니다. 다시 시도하세요.")
            except ValueError:
                self.menu_view.show_error("숫자를 입력하세요.")
    
    def select_target_module(self):
        """송신용 블루투스 모듈 선택"""
        interfaces = self.display_module_list()
        
        if not interfaces:
            return
        
        # 사용자 선택
        while True:
            choice = input("\n송신용으로 사용할 모듈 번호를 선택하세요 (0: 취소): ")
            
            if choice == "0":
                return
                
            try:
                index = int(choice) - 1
                if 0 <= index < len(interfaces):
                    # 모델에 선택한 모듈 설정
                    selected = interfaces[index]
                    self.module_manager.set_target_module(selected['mac'])
                    self.menu_view.show_message(f"\n송신용 모듈로 {selected['name']} ({selected['mac']})를 선택했습니다.")
                    
                    # 설정 변경 시 설정 파일 저장
                    self._save_config()
                    
                    self.menu_view.wait_for_input()
                    return
                else:
                    self.menu_view.show_error("잘못된 번호입니다. 다시 시도하세요.")
            except ValueError:
                self.menu_view.show_error("숫자를 입력하세요.")
    
    def _save_config(self):
        """현재 설정을 파일에 저장"""
        try:
            # 현재 설정 가져오기
            device_model = self.module_manager.device_model
            
            config = {
                'source_module': device_model.get_source_module(),
                'target_module': device_model.get_target_module(),
                'receiving_devices': device_model.get_receiving_devices(),
                'transmitting_device': device_model.get_transmitting_device()
            }
            
            # 설정 파일에 저장
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            print(f"설정이 파일에 저장되었습니다: {self.config_file}")
                
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {e}")