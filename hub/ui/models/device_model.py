#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
디바이스 정보 관련 모델 클래스
"""

class DeviceModel:
    """디바이스 정보 모델 클래스"""
    
    def __init__(self):
        """디바이스 모델 초기화"""
        # 샘플 데이터 (추후 실제 데이터로 교체 예정)
        self._source_module = "00:11:22:33:44:55"
        self._target_module = "AA:BB:CC:DD:EE:FF"
        self._receiving_devices = [
            {"name": "디바이스1", "mac": "12:34:56:78:90:AB"},
            {"name": "디바이스2", "mac": "CD:EF:12:34:56:78"}
        ]
        self._transmitting_device = {"name": "송신기", "mac": "98:76:54:32:10:FF"}
    
    def get_source_module(self):
        """소스 블루투스 모듈 정보 반환
        
        Returns:
            str: 소스 블루투스 모듈 MAC 주소
        """
        return self._source_module
    
    def set_source_module(self, mac_address):
        """소스 블루투스 모듈 설정
        
        Args:
            mac_address (str): 설정할 MAC 주소
        """
        self._source_module = mac_address
    
    def get_target_module(self):
        """타겟 블루투스 모듈 정보 반환
        
        Returns:
            str: 타겟 블루투스 모듈 MAC 주소
        """
        return self._target_module
    
    def set_target_module(self, mac_address):
        """타겟 블루투스 모듈 설정
        
        Args:
            mac_address (str): 설정할 MAC 주소
        """
        self._target_module = mac_address
    
    def get_receiving_devices(self):
        """수신 디바이스 목록 반환
        
        Returns:
            list: 수신 디바이스 정보 목록 (이름, MAC 주소)
        """
        return self._receiving_devices
    
    def add_receiving_device(self, name, mac_address):
        """수신 디바이스 추가
        
        Args:
            name (str): 디바이스 이름
            mac_address (str): 디바이스 MAC 주소
        """
        self._receiving_devices.append({"name": name, "mac": mac_address})
    
    def remove_receiving_device(self, index):
        """수신 디바이스 제거
        
        Args:
            index (int): 제거할 디바이스 인덱스
        
        Returns:
            bool: 제거 성공 여부
        """
        if 0 <= index < len(self._receiving_devices):
            self._receiving_devices.pop(index)
            return True
        return False
    
    def get_transmitting_device(self):
        """송신 디바이스 정보 반환
        
        Returns:
            dict: 송신 디바이스 정보 (이름, MAC 주소)
        """
        return self._transmitting_device
    
    def set_transmitting_device(self, name, mac_address):
        """송신 디바이스 설정
        
        Args:
            name (str): 디바이스 이름
            mac_address (str): 디바이스 MAC 주소
        """
        self._transmitting_device = {"name": name, "mac": mac_address} 