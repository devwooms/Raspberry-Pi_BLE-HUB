#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 모듈 관리 클래스
"""

class BluetoothModuleManager:
    """블루투스 모듈(인터페이스) 관리 클래스"""
    
    def __init__(self, scanner, device_model):
        """초기화
        
        Args:
            scanner: 블루투스 스캐너 인스턴스
            device_model: 디바이스 모델 인스턴스
        """
        self.scanner = scanner
        self.device_model = device_model
    
    def get_interfaces(self):
        """사용 가능한 블루투스 인터페이스 목록 반환
        
        Returns:
            list: 블루투스 인터페이스 목록
        """
        return self.scanner.get_bluetooth_interfaces()
    
    def get_current_source_module(self):
        """현재 설정된 수신용 모듈 반환
        
        Returns:
            str: 수신용 모듈 MAC 주소 또는 None
        """
        return self.device_model.get_source_module()
    
    def get_current_target_module(self):
        """현재 설정된 송신용 모듈 반환
        
        Returns:
            str: 송신용 모듈 MAC 주소 또는 None
        """
        return self.device_model.get_target_module()
    
    def set_source_module(self, interface_info):
        """수신용 블루투스 모듈 설정
        
        Args:
            interface_info (dict): 인터페이스 정보 {'name': 'hciX', 'mac': 'XX:XX:XX:XX:XX:XX'}
            
        Returns:
            bool: 설정 성공 여부
        """
        try:
            self.device_model.set_source_module(interface_info['mac'])
            return True
        except Exception as e:
            print(f"수신용 모듈 설정 중 오류: {e}")
            return False
    
    def set_target_module(self, interface_info):
        """송신용 블루투스 모듈 설정
        
        Args:
            interface_info (dict): 인터페이스 정보 {'name': 'hciX', 'mac': 'XX:XX:XX:XX:XX:XX'}
            
        Returns:
            bool: 설정 성공 여부
        """
        try:
            self.device_model.set_target_module(interface_info['mac'])
            return True
        except Exception as e:
            print(f"송신용 모듈 설정 중 오류: {e}")
            return False
    
    def get_interface_by_index(self, index):
        """인덱스로 인터페이스 정보 가져오기
        
        Args:
            index (int): 인터페이스 인덱스 (1부터 시작)
            
        Returns:
            dict: 인터페이스 정보 또는 None (인덱스가 유효하지 않은 경우)
        """
        interfaces = self.get_interfaces()
        if 1 <= index <= len(interfaces):
            return interfaces[index - 1]
        return None 