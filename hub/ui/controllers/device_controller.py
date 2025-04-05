#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 디바이스 컨트롤러
"""

class DeviceController:
    """블루투스 디바이스 관리 UI 컨트롤러"""
    
    def __init__(self, device_manager, device_model, menu_view):
        """초기화
        
        Args:
            device_manager: 블루투스 디바이스 관리자
            device_model: 디바이스 모델
            menu_view: 메뉴 뷰
        """
        self.device_manager = device_manager
        self.device_model = device_model
        self.menu_view = menu_view
    
    def add_receiving_device(self):
        """수신 블루투스 디바이스 추가"""
        self.menu_view.clear_screen()
        self.menu_view.show_header("수신 블루투스 디바이스 추가")
        
        # 소스 블루투스 모듈 확인
        source_module = self.device_model.get_source_module()
        if not source_module:
            self.menu_view.show_error("수신용 블루투스 모듈이 설정되지 않았습니다.")
            self.menu_view.show_message("먼저 '1. 수신용 블루투스 모듈 선택'에서 모듈을 설정하세요.")
            self.menu_view.wait_for_input()
            return
        
        # 어댑터 이름 찾기
        adapter = self.device_manager.get_adapter_name_from_mac(source_module)
        if not adapter:
            self.menu_view.show_error(f"MAC 주소 {source_module}에 해당하는 어댑터를 찾을 수 없습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 스캔 시간 입력 받기
        scan_timeout = self._get_scan_timeout()
        if scan_timeout is None:
            return
        
        # 디바이스 스캔
        self.menu_view.show_message(f"\n{adapter} ({source_module}) 어댑터에서 디바이스를 스캔합니다.")
        devices = self.device_manager.scan_with_progress(adapter, scan_timeout)
        
        if not devices:
            self.menu_view.show_error("블루투스 디바이스를 찾을 수 없습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 디바이스 목록 표시
        self.menu_view.show_message("\n== 발견된 블루투스 디바이스 ==")
        for i, device in enumerate(devices):
            rssi_info = f" (RSSI: {device['rssi']})" if device['rssi'] else ""
            self.menu_view.show_message(f"{i+1}. {device['name']} - {device['mac']}{rssi_info}")
        
        # 사용자 선택
        self.menu_view.show_message("\n0. 이전 메뉴로 돌아가기")
        
        while True:
            choice = input("\n추가할 디바이스 번호를 선택하세요: ")
            
            if choice == "0":
                return
                
            try:
                index = int(choice) - 1
                if 0 <= index < len(devices):
                    selected_device = devices[index]
                    
                    # 중복 확인
                    receiving_devices = self.device_model.get_receiving_devices()
                    for existing in receiving_devices:
                        if existing['mac'] == selected_device['mac']:
                            self.menu_view.show_error(f"{selected_device['name']} ({selected_device['mac']})는 이미 추가된 디바이스입니다.")
                            self.menu_view.wait_for_input()
                            return
                    
                    # 장치 설정 진행 (페어링, 신뢰, 연결)
                    if self.device_manager.setup_device(adapter, selected_device['mac'], selected_device['name']):
                        # 디바이스 모델에 추가
                        self.device_model.add_receiving_device(selected_device['name'], selected_device['mac'])
                        self.menu_view.show_message(f"\n{selected_device['name']} ({selected_device['mac']})가 수신 디바이스로 추가되었습니다.")
                        
                        # 설정 저장
                        self._save_config()
                    else:
                        self.menu_view.show_error("디바이스 설정에 실패했습니다.")
                    
                    self.menu_view.wait_for_input()
                    return
                else:
                    self.menu_view.show_error("잘못된 번호입니다. 다시 시도하세요.")
            except ValueError:
                self.menu_view.show_error("숫자를 입력하세요.")
    
    def remove_receiving_device(self):
        """수신 블루투스 디바이스 삭제"""
        self.menu_view.clear_screen()
        self.menu_view.show_header("수신 블루투스 디바이스 삭제")
        
        # 소스 블루투스 모듈 확인
        source_module = self.device_model.get_source_module()
        if not source_module:
            self.menu_view.show_error("수신용 블루투스 모듈이 설정되지 않았습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 어댑터 이름 찾기
        adapter = self.device_manager.get_adapter_name_from_mac(source_module)
        if not adapter:
            self.menu_view.show_error(f"MAC 주소 {source_module}에 해당하는 어댑터를 찾을 수 없습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 등록된 디바이스 목록 확인
        receiving_devices = self.device_model.get_receiving_devices()
        
        if not receiving_devices:
            self.menu_view.show_error("등록된 수신 디바이스가 없습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 디바이스 목록 표시
        self.menu_view.show_message("\n== 등록된 수신 디바이스 ==")
        for i, device in enumerate(receiving_devices):
            self.menu_view.show_message(f"{i+1}. {device['name']} - {device['mac']}")
        
        # 사용자 선택
        self.menu_view.show_message("\n0. 이전 메뉴로 돌아가기")
        
        while True:
            choice = input("\n삭제할 디바이스 번호를 선택하세요: ")
            
            if choice == "0":
                return
                
            try:
                index = int(choice) - 1
                if 0 <= index < len(receiving_devices):
                    selected_device = receiving_devices[index]
                    
                    # 확인 질문
                    confirm = input(f"{selected_device['name']} ({selected_device['mac']})를 삭제하시겠습니까? (y/n): ")
                    
                    if confirm.lower() == 'y':
                        # 장치 완전 제거 (연결 해제 및 페어링 삭제)
                        if self.device_manager.remove_device_completely(adapter, selected_device['mac'], selected_device['name']):
                            # 디바이스 모델에서 제거
                            self.device_model.remove_receiving_device(index)
                            self.menu_view.show_message(f"\n{selected_device['name']} ({selected_device['mac']})가 삭제되었습니다.")
                            
                            # 설정 저장
                            self._save_config()
                        else:
                            self.menu_view.show_message(f"\n주의: 디바이스가 물리적으로 제거되지 않았지만, 목록에서는 삭제합니다.")
                            
                            # 디바이스 모델에서 제거
                            self.device_model.remove_receiving_device(index)
                            
                            # 설정 저장
                            self._save_config()
                    
                    self.menu_view.wait_for_input()
                    return
                else:
                    self.menu_view.show_error("잘못된 번호입니다. 다시 시도하세요.")
            except ValueError:
                self.menu_view.show_error("숫자를 입력하세요.")
    
    def select_transmitting_device(self):
        """송신 블루투스 디바이스 선택"""
        self.menu_view.clear_screen()
        self.menu_view.show_header("송신 블루투스 디바이스 선택")
        
        # 타겟 블루투스 모듈 확인
        target_module = self.device_model.get_target_module()
        if not target_module:
            self.menu_view.show_error("송신용 블루투스 모듈이 설정되지 않았습니다.")
            self.menu_view.show_message("먼저 '2. 송신용 블루투스 모듈 선택'에서 모듈을 설정하세요.")
            self.menu_view.wait_for_input()
            return
        
        # 어댑터 이름 찾기
        adapter = self.device_manager.get_adapter_name_from_mac(target_module)
        if not adapter:
            self.menu_view.show_error(f"MAC 주소 {target_module}에 해당하는 어댑터를 찾을 수 없습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 현재 선택된 송신 디바이스 표시
        transmitting_device = self.device_model.get_transmitting_device()
        if transmitting_device:
            self.menu_view.show_message(f"\n현재 송신 디바이스: {transmitting_device['name']} ({transmitting_device['mac']})")
        
        # 스캔 시간 입력 받기
        scan_timeout = self._get_scan_timeout()
        if scan_timeout is None:
            return
        
        # 디바이스 스캔
        self.menu_view.show_message(f"\n{adapter} ({target_module}) 어댑터에서 디바이스를 스캔합니다.")
        devices = self.device_manager.scan_with_progress(adapter, scan_timeout)
        
        if not devices:
            self.menu_view.show_error("블루투스 디바이스를 찾을 수 없습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 디바이스 목록 표시
        self.menu_view.show_message("\n== 발견된 블루투스 디바이스 ==")
        for i, device in enumerate(devices):
            rssi_info = f" (RSSI: {device['rssi']})" if device['rssi'] else ""
            self.menu_view.show_message(f"{i+1}. {device['name']} - {device['mac']}{rssi_info}")
        
        # 사용자 선택
        self.menu_view.show_message("\n0. 이전 메뉴로 돌아가기")
        
        while True:
            choice = input("\n선택할 디바이스 번호를 선택하세요: ")
            
            if choice == "0":
                return
                
            try:
                index = int(choice) - 1
                if 0 <= index < len(devices):
                    selected_device = devices[index]
                    
                    # 장치 설정 진행 (페어링, 신뢰, 연결)
                    if self.device_manager.setup_device(adapter, selected_device['mac'], selected_device['name']):
                        # 디바이스 모델에 설정
                        self.device_model.set_transmitting_device(selected_device['name'], selected_device['mac'])
                        self.menu_view.show_message(f"\n{selected_device['name']} ({selected_device['mac']})가 송신 디바이스로 설정되었습니다.")
                        
                        # 설정 저장
                        self._save_config()
                    else:
                        self.menu_view.show_error("디바이스 설정에 실패했습니다.")
                    
                    self.menu_view.wait_for_input()
                    return
                else:
                    self.menu_view.show_error("잘못된 번호입니다. 다시 시도하세요.")
            except ValueError:
                self.menu_view.show_error("숫자를 입력하세요.")
                
    def remove_transmitting_device(self):
        """송신 블루투스 디바이스 삭제"""
        self.menu_view.clear_screen()
        self.menu_view.show_header("송신 블루투스 디바이스 삭제")
        
        # 타겟 블루투스 모듈 확인
        target_module = self.device_model.get_target_module()
        if not target_module:
            self.menu_view.show_error("송신용 블루투스 모듈이 설정되지 않았습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 어댑터 이름 찾기
        adapter = self.device_manager.get_adapter_name_from_mac(target_module)
        if not adapter:
            self.menu_view.show_error(f"MAC 주소 {target_module}에 해당하는 어댑터를 찾을 수 없습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 현재 송신 디바이스 확인
        transmitting_device = self.device_model.get_transmitting_device()
        
        if not transmitting_device:
            self.menu_view.show_error("설정된 송신 디바이스가 없습니다.")
            self.menu_view.wait_for_input()
            return
        
        # 송신 디바이스 정보 표시
        self.menu_view.show_message("\n== 현재 송신 디바이스 ==")
        self.menu_view.show_message(f"이름: {transmitting_device['name']}")
        self.menu_view.show_message(f"MAC: {transmitting_device['mac']}")
        
        # 확인 질문
        confirm = input("\n이 디바이스를 삭제하시겠습니까? (y/n): ")
        
        if confirm.lower() == 'y':
            # 장치 완전 제거 (연결 해제 및 페어링 삭제)
            if self.device_manager.remove_device_completely(adapter, transmitting_device['mac'], transmitting_device['name']):
                # 디바이스 모델에서 제거
                self.device_model.set_transmitting_device(None, None)
                self.menu_view.show_message(f"\n{transmitting_device['name']} ({transmitting_device['mac']})가 송신 디바이스에서 삭제되었습니다.")
                
                # 설정 저장
                self._save_config()
            else:
                self.menu_view.show_message(f"\n주의: 디바이스가 물리적으로 제거되지 않았지만, 송신 디바이스 설정은 초기화합니다.")
                
                # 디바이스 모델에서 제거
                self.device_model.set_transmitting_device(None, None)
                
                # 설정 저장
                self._save_config()
        
        self.menu_view.wait_for_input()
    
    def _save_config(self):
        """설정 파일에 저장 (설정 파일 경로는 데몬 컨트롤러에서 가져와야 함)"""
        try:
            import os
            import json
            
            config_file = os.path.abspath("blehub_config.json")
            
            config = {
                'source_module': self.device_model.get_source_module(),
                'target_module': self.device_model.get_target_module(),
                'receiving_devices': self.device_model.get_receiving_devices(),
                'transmitting_device': self.device_model.get_transmitting_device()
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            print(f"설정이 저장되었습니다: {config_file}")
            
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {e}")

    def _get_scan_timeout(self):
        """스캔 시간 입력 받기
        
        Returns:
            int: 스캔 시간(초) 또는 None (취소 시)
        """
        while True:
            try:
                self.menu_view.show_message("\n블루투스 스캔 시간을 설정합니다.")
                self.menu_view.show_message("권장: 10-60초 (0: 취소)")
                timeout = input("스캔 시간(초): ")
                
                if timeout == "0":
                    return None
                    
                timeout = int(timeout)
                
                if timeout < 5:
                    self.menu_view.show_error("스캔 시간은 최소 5초 이상이어야 합니다.")
                elif timeout > 120:
                    self.menu_view.show_error("스캔 시간은 최대 120초까지 설정 가능합니다.")
                else:
                    return timeout
                    
            except ValueError:
                self.menu_view.show_error("유효한 숫자를 입력하세요.") 