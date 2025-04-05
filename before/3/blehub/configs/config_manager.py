#!/usr/bin/env python3
import os
import json
from pathlib import Path

"""
BLE-HUB 설정 관리 모듈

설정 파일 읽기, 쓰기 및 업데이트 기능을 제공합니다.
"""

# 기본 설정 디렉토리 및 파일명
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.blehub")
DEFAULT_CONFIG_FILE = "config.json"

class ConfigManager:
    """설정 파일 관리자 클래스"""
    
    def __init__(self, config_path=None):
        """설정 관리자 초기화
        
        Args:
            config_path (str, optional): 설정 파일 경로. 
                None이면 스크립트 위치 기준으로 설정됨
        """
        if config_path is None:
            # 스크립트 위치 기준으로 경로 계산
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.config_path = os.path.join(script_dir, "ble_config.json")
        else:
            self.config_path = config_path
            
        # 기본 설정
        self.config = {
            'source_adapter': None,     # 수신용 블루투스 어댑터
            'target_adapter': None,     # 송신용 블루투스 어댑터
            'source_devices': [],       # 수신 디바이스 목록 (여러 개 가능)
            'target_device': None,      # 송신 대상 디바이스
            'device_cache': {},         # MAC 주소를 키로 하는 디바이스 이름 캐시
            'daemon_settings': {        # 데몬 관련 설정
                'pid_file': os.path.join(os.path.dirname(os.path.dirname(self.config_path)), "blehub.pid"),
                'log_level': 'INFO'
            }
        }
        
        # 파일이 있으면 읽어옴
        self.load()
    
    def load(self):
        """설정 파일을 읽어옵니다"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # 기존 설정에 로드된 설정을 업데이트
                    self.config.update(loaded_config)
                return True
            except Exception as e:
                print(f"설정 파일 읽기 오류: {e}")
        return False
    
    def save(self):
        """현재 설정을 파일에 저장합니다"""
        try:
            # 디렉토리 생성 (필요 시)
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # 파일 저장
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")
            return False
    
    def get(self, key, default=None):
        """특정 설정 값을 가져옵니다
        
        Args:
            key (str): 설정 키
            default: 키가 없을 경우 반환할 기본값
            
        Returns:
            설정 값 또는 기본값
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """특정 설정 값을 설정합니다
        
        Args:
            key (str): 설정 키
            value: 설정 값
            
        Returns:
            bool: 성공 여부
        """
        self.config[key] = value
        
        # 디바이스 MAC 주소가 설정되었고 캐시에 있으면 캐시에서 이름 가져오기
        if key == 'target_device' and value and 'device_cache' in self.config and value in self.config['device_cache']:
            # 해당 MAC 주소가 캐시에 있으면 캐시 정보 갱신
            pass
        
        return self.save()
    
    def update(self, new_config):
        """여러 설정을 한번에 업데이트합니다
        
        Args:
            new_config (dict): 새로운 설정 값들
            
        Returns:
            bool: 성공 여부
        """
        self.config.update(new_config)
        return self.save()
    
    def get_full_config(self):
        """전체 설정을 반환합니다
        
        Returns:
            dict: 현재 설정 전체
        """
        return self.config
        
    def add_source_device(self, device):
        """수신 디바이스를 추가합니다
        
        Args:
            device (dict): 블루투스 장치 정보 (name, mac 포함)
            
        Returns:
            bool: 성공 여부
        """
        # 이미 있는지 확인
        for existing_device in self.config.get('source_devices', []):
            if existing_device.get('mac') == device.get('mac'):
                return True  # 이미 존재함
        
        # 없으면 추가
        if 'source_devices' not in self.config:
            self.config['source_devices'] = []
        
        self.config['source_devices'].append(device)
        
        # 디바이스 캐시에 추가
        self.cache_device(device)
        
        return self.save()
    
    def cache_device(self, device):
        """디바이스 정보를 캐시에 저장합니다
        
        Args:
            device (dict): 블루투스 장치 정보 (name, mac 포함)
        """
        if 'mac' in device and 'name' in device:
            # 디바이스 캐시가 없으면 초기화
            if 'device_cache' not in self.config:
                self.config['device_cache'] = {}
            
            # 캐시에 추가
            self.config['device_cache'][device['mac']] = device['name']
    
    def remove_source_device(self, mac_address):
        """수신 디바이스를 제거합니다
        
        Args:
            mac_address (str): 제거할 블루투스 장치의 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        if 'source_devices' not in self.config:
            return True  # 없으므로 제거 필요 없음
        
        # 기존 목록에서 해당 MAC 주소를 가진 디바이스 제거
        self.config['source_devices'] = [
            device for device in self.config['source_devices']
            if device.get('mac') != mac_address
        ]
        
        return self.save()
    
    def reset_config(self):
        """설정을 초기화합니다
        
        Returns:
            bool: 성공 여부
        """
        # 설정 초기화
        self.config = {
            'source_adapter': None,     # 수신용 블루투스 어댑터
            'target_adapter': None,     # 송신용 블루투스 어댑터
            'source_devices': [],       # 수신 디바이스 목록 (여러 개 가능)
            'target_device': None,      # 송신 대상 디바이스
            'device_cache': {},         # MAC 주소를 키로 하는 디바이스 이름 캐시
            'daemon_settings': {        # 데몬 관련 설정
                'pid_file': os.path.join(os.path.dirname(os.path.dirname(self.config_path)), "blehub.pid"),
                'log_level': 'INFO'
            }
        }
        
        return self.save()

# 전역 설정 관리자 인스턴스
_config_manager = None

def get_config_manager(config_path=None):
    """전역 설정 관리자 인스턴스를 반환합니다
    
    Args:
        config_path (str, optional): 설정 파일 경로
        
    Returns:
        ConfigManager: 설정 관리자 인스턴스
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager 