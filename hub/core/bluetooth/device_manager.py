#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 디바이스 관리 클래스
"""

import os
import re
import time
import subprocess

class BluetoothDeviceManager:
    """블루투스 디바이스 관리 클래스"""
    
    def __init__(self, scanner):
        """초기화
        
        Args:
            scanner: 블루투스 스캐너 인스턴스
        """
        self.scanner = scanner
    
    def pair_device(self, adapter, device_mac):
        """블루투스 디바이스 페어링
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치 페어링 시도 중...")
            
            # bluetoothctl 명령으로 페어링
            cmd = [
                "bluetoothctl",
                "pair",
                device_mac
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15  # 페어링은 시간이 걸릴 수 있음
            )
            
            if "Pairing successful" in process.stdout:
                print(f"페어링 성공: {device_mac}")
                return True
            else:
                print(f"페어링 실패: {process.stdout}")
                # 이미 페어링되어 있는 경우도 성공으로 처리
                if "Already paired" in process.stdout:
                    print("이미 페어링되어 있습니다.")
                    return True
                return False
                
        except subprocess.TimeoutExpired:
            print("페어링 시간 초과. 장치가 응답하지 않습니다.")
            return False
        except Exception as e:
            print(f"페어링 중 오류: {e}")
            return False
    
    def trust_device(self, adapter, device_mac):
        """블루투스 디바이스 신뢰 설정
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치 신뢰 설정 중...")
            
            # bluetoothctl 명령으로 신뢰 설정
            cmd = [
                "bluetoothctl",
                "trust",
                device_mac
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if "trusted: yes" in process.stdout:
                print(f"신뢰 설정 성공: {device_mac}")
                return True
            else:
                print(f"신뢰 설정 실패: {process.stdout}")
                return False
                
        except Exception as e:
            print(f"신뢰 설정 중 오류: {e}")
            return False
    
    def connect_device(self, adapter, device_mac):
        """블루투스 디바이스 연결
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치에 연결 시도 중...")
            
            # bluetoothctl 명령으로 연결
            cmd = [
                "bluetoothctl",
                "connect",
                device_mac
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15  # 연결에는 시간이 걸릴 수 있음
            )
            
            if "Connection successful" in process.stdout:
                print(f"연결 성공: {device_mac}")
                return True
            else:
                print(f"연결 실패: {process.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            print("연결 시간 초과. 장치가 응답하지 않습니다.")
            return False
        except Exception as e:
            print(f"연결 중 오류: {e}")
            return False
    
    def disconnect_device(self, adapter, device_mac):
        """블루투스 디바이스 연결 해제
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치 연결 해제 중...")
            
            # bluetoothctl 명령으로 연결 해제
            cmd = [
                "bluetoothctl",
                "disconnect",
                device_mac
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if "Successful disconnected" in process.stdout or "Device has been disconnected" in process.stdout:
                print(f"연결 해제 성공: {device_mac}")
                return True
            else:
                print(f"연결 해제 실패: {process.stdout}")
                return False
                
        except Exception as e:
            print(f"연결 해제 중 오류: {e}")
            return False
    
    def remove_device(self, adapter, device_mac):
        """블루투스 디바이스 제거 (페어링 삭제)
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            
        Returns:
            bool: 성공 여부
        """
        try:
            print(f"{adapter}에서 {device_mac} 장치 제거 중...")
            
            # bluetoothctl 명령으로 장치 제거
            cmd = [
                "bluetoothctl",
                "remove",
                device_mac
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if "Device has been removed" in process.stdout or "was removed" in process.stdout:
                print(f"장치 제거 성공: {device_mac}")
                return True
            else:
                print(f"장치 제거 실패: {process.stdout}")
                return False
                
        except Exception as e:
            print(f"장치 제거 중 오류: {e}")
            return False
    
    def setup_device(self, adapter, device_mac, device_name):
        """블루투스 디바이스 설정 (페어링, 신뢰, 연결 순서로 진행)
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            device_name (str): 장치 이름
            
        Returns:
            bool: 성공 여부
        """
        print(f"\n== {device_name} ({device_mac}) 장치 설정 ==")
        
        # 페어링 진행
        if not self.pair_device(adapter, device_mac):
            print("페어링 실패로 설정을 중단합니다.")
            return False
            
        # 신뢰 설정
        if not self.trust_device(adapter, device_mac):
            print("신뢰 설정 실패. 연결을 시도합니다.")
            
        # 연결 진행
        if not self.connect_device(adapter, device_mac):
            print("연결 실패. 장치가 가까이 있는지 확인하세요.")
            return False
            
        print(f"{device_name} ({device_mac}) 장치 설정 완료!")
        return True
        
    def remove_device_completely(self, adapter, device_mac, device_name):
        """블루투스 디바이스 완전 제거 (연결 해제 후 장치 제거)
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            device_mac (str): 장치 MAC 주소
            device_name (str): 장치 이름
            
        Returns:
            bool: 성공 여부
        """
        print(f"\n== {device_name} ({device_mac}) 장치 제거 ==")
        
        # 연결 해제
        self.disconnect_device(adapter, device_mac)
        
        # 잠시 대기
        time.sleep(1)
        
        # 장치 제거
        if self.remove_device(adapter, device_mac):
            print(f"{device_name} ({device_mac}) 장치가 완전히 제거되었습니다.")
            return True
        else:
            print(f"{device_name} ({device_mac}) 장치 제거에 실패했습니다.")
            return False
            
    def get_adapter_name_from_mac(self, mac_address):
        """MAC 주소로 어댑터 이름 찾기
        
        Args:
            mac_address (str): 어댑터 MAC 주소
            
        Returns:
            str: 어댑터 이름 (hci0, hci1 등) 또는 None
        """
        interfaces = self.scanner.get_bluetooth_interfaces()
        
        for interface in interfaces:
            if interface['mac'].lower() == mac_address.lower():
                return interface['name']
                
        return None
    
    def scan_with_progress(self, adapter, timeout=30):
        """진행 상황을 표시하며 블루투스 디바이스 스캔
        
        Args:
            adapter (str): 블루투스 어댑터 (hci0, hci1 등)
            timeout (int): 스캔 제한 시간(초)
            
        Returns:
            list: 발견된 디바이스 목록
        """
        try:
            print(f"{adapter} 어댑터를 이용하여 주변 디바이스 스캔을 시작합니다...")
            print(f"스캔 시간: {timeout}초")
            
            # 스캔 시작 명령
            scan_process = subprocess.Popen(
                ["bluetoothctl", "scan", "on"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True
            )
            
            # 초기 장치 리스트
            devices = []
            
            # 시간 경과와 함께 진행 상황 표시
            for current_time in range(timeout):
                time_left = timeout - current_time
                print(f"\r스캔 중... {current_time+1}/{timeout}초 경과 (남은 시간: {time_left}초)", end="")
                
                # 1초마다 발견된 장치 가져오기
                found_devices = self.scanner.get_discovered_devices(adapter)
                
                # 새로운 장치가 있으면 추가
                for device in found_devices:
                    if not any(d['mac'] == device['mac'] for d in devices):
                        devices.append(device)
                        # 진행 막대 아래에 찾은 장치 실시간으로 표시
                        print(f"\n발견: {device['name']} ({device['mac']})")
                
                time.sleep(1)
            
            # 스캔 종료
            print("\n\n스캔 완료!")
            
            # 스캔 중지 명령
            subprocess.run(
                ["bluetoothctl", "scan", "off"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 스캔 프로세스 종료
            try:
                scan_process.terminate()
            except:
                pass
                
            return devices
                
        except Exception as e:
            print(f"\n스캔 중 오류 발생: {e}")
            return [] 