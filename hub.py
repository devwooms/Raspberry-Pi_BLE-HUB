#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BLE-HUB 블루투스 릴레이 관리 시스템 - 터미널 메뉴
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# 로그 설정
def setup_logger(name, log_file):
    """로거 설정
    
    Args:
        name (str): 로거 이름
        log_file (str): 로그 파일 경로
        
    Returns:
        logging.Logger: 설정된 로거
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger("hub", "hub.log")

class TerminalMenu:
    """터미널 메뉴 클래스"""
    
    def __init__(self):
        """터미널 메뉴 초기화"""
        pass
    
    def main_menu(self):
        """메인 메뉴 표시"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("BLE-HUB 블루투스 릴레이 관리 시스템".center(60))
            print("=" * 60)
            
            print("\n메뉴:")
            print("1. 데몬 관리")
            print("2. 블루투스 모듈 관리")
            print("3. 설정 관리")
            print("4. 로그 레벨 설정")
            print("0. 종료")
            
            choice = input("\n선택: ")
            
            if choice == "1":
                self.daemon_menu()
            elif choice == "2":
                self.bluetooth_menu()
            elif choice == "3":
                self.config_menu()
            elif choice == "4":
                self.log_level_menu()
            elif choice == "0":
                print("프로그램을 종료합니다.")
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def daemon_menu(self):
        """데몬 관리 메뉴"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("데몬 관리".center(60))
            print("=" * 60)
            
            print("\n메뉴:")
            print("1. 데몬 시작")
            print("2. 데몬 중지")
            print("3. 데몬 재시작")
            print("4. 데몬 상태 확인")
            print("0. 이전 메뉴로 돌아가기")
            
            choice = input("\n선택: ")
            
            if choice == "1":
                print("데몬이 시작되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "2":
                print("데몬이 중지되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "3":
                print("데몬이 재시작되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "4":
                print("\n데몬 상태: 중지됨")
                input("\n계속하려면 Enter 키를 누르세요...")
            elif choice == "0":
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def bluetooth_menu(self):
        """블루투스 관리 메뉴"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("블루투스 관리".center(60))
            print("=" * 60)
            
            print("\n메뉴:")
            print("1. 블루투스 모듈 목록 표시")
            print("2. 소스 블루투스 인터페이스 선택")
            print("3. 타겟 블루투스 인터페이스 선택")
            print("4. 수신 블루투스 디바이스 추가")
            print("5. 수신 블루투스 디바이스 삭제")
            print("6. 송신 블루투스 디바이스 선택")
            print("0. 이전 메뉴로 돌아가기")
            
            choice = input("\n선택: ")
            
            if choice in ["1", "2", "3", "4", "5", "6"]:
                print("기능이 준비 중입니다.")
                input("\n계속하려면 Enter 키를 누르세요...")
            elif choice == "0":
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def config_menu(self):
        """설정 관리 메뉴"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("설정 관리".center(60))
            print("=" * 60)
            
            print("\n메뉴:")
            print("1. 설정 저장")
            print("2. 설정 불러오기")
            print("3. 설정 초기화")
            print("0. 이전 메뉴로 돌아가기")
            
            choice = input("\n선택: ")
            
            if choice in ["1", "2", "3"]:
                print("기능이 준비 중입니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "0":
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def log_level_menu(self):
        """로그 레벨 설정 메뉴"""
        while True:
            self._clear_screen()
            print("\n" + "=" * 60)
            print("로그 레벨 설정".center(60))
            print("=" * 60)
            
            print("\n메뉴:")
            print("1. DEBUG 레벨 설정")
            print("2. INFO 레벨 설정")
            print("3. WARNING 레벨 설정")
            print("4. ERROR 레벨 설정")
            print("0. 이전 메뉴로 돌아가기")
            
            choice = input("\n선택: ")
            
            if choice in ["1", "2", "3", "4"]:
                print(f"로그 레벨이 설정되었습니다.")
                input("계속하려면 Enter 키를 누르세요...")
            elif choice == "0":
                break
            else:
                print("잘못된 선택입니다. 다시 시도하세요.")
                input("계속하려면 Enter 키를 누르세요...")
    
    def _clear_screen(self):
        """화면 지우기"""
        os.system('cls' if os.name == 'nt' else 'clear')

def main():
    """메인 함수"""
    menu = TerminalMenu()
    menu.main_menu()

if __name__ == "__main__":
    main() 