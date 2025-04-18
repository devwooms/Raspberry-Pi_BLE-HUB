#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
라즈베리파이 블루투스 이름 설정 (test2)
블루투스 이름을 'test2'로 설정하고 검색 가능하게 합니다.

사용방법: sudo python3 test2.py
"""

import os
import sys
import subprocess
import time
import signal

# 블루투스 이름
BLUETOOTH_NAME = "test2"

def set_bluetooth_name():
    """블루투스 이름을 test2로 설정"""
    print(f"🔄 블루투스 이름을 '{BLUETOOTH_NAME}'로 설정 중...")
    
    try:
        # 블루투스 서비스 다시 시작
        print("🔄 블루투스 서비스 재시작 중...")
        subprocess.run(["sudo", "systemctl", "restart", "bluetooth"], check=True)
        time.sleep(2)  # 서비스가 완전히 시작될 때까지 기다림
        
        # 블루투스 활성화
        print("🔄 블루투스 활성화 중...")
        subprocess.run(["bluetoothctl", "power", "on"], check=True)
        time.sleep(1)
        
        # 블루투스 이름 설정
        print(f"🔄 블루투스 이름을 '{BLUETOOTH_NAME}'로 변경 중...")
        subprocess.run(["bluetoothctl", "system-alias", BLUETOOTH_NAME], check=True)
        subprocess.run(["sudo", "hciconfig", "hci0", "name", BLUETOOTH_NAME], check=True)
        
        # 검색 가능 및 페어링 가능 설정
        print("🔄 블루투스 검색 가능 설정 중...")
        subprocess.run(["bluetoothctl", "discoverable", "on"], check=True)
        subprocess.run(["bluetoothctl", "pairable", "on"], check=True)
        
        # 검증: 현재 설정 확인
        print("🔍 현재 블루투스 설정 확인 중...")
        subprocess.run(["hciconfig", "hci0", "name"], check=True)
        
        print(f"✅ 블루투스 이름이 '{BLUETOOTH_NAME}'로 성공적으로 설정되었습니다.")
        print("✅ 이제 다른 장치에서 검색할 수 있습니다.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 오류 발생: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def signal_handler(signum, frame):
    """시그널 핸들러"""
    print("\n🛑 프로그램 종료 중...")
    sys.exit(0)

if __name__ == "__main__":
    # 루트 권한 확인
    if os.geteuid() != 0:
        print("❌ 이 스크립트는 루트 권한으로 실행해야 합니다.")
        print("다음 명령으로 다시 실행하세요: sudo python3 test2.py")
        sys.exit(1)
    
    # 시그널 핸들러 설정
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 블루투스 이름 설정 스크립트 시작")
    print("====================================")
    
    # 블루투스 이름 설정
    if set_bluetooth_name():
        print("\n📱 스마트폰이나 컴퓨터에서 블루투스 장치 검색을 시도해보세요.")
        print(f"📡 '{BLUETOOTH_NAME}' 이름으로 라즈베리파이가 표시될 것입니다.")
        print("⏳ 프로그램은 계속 실행 중입니다. Ctrl+C를 눌러 종료할 수 있습니다.")
        
        try:
            # 프로그램을 계속 실행 상태로 유지
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 프로그램을 종료합니다.")
    else:
        print("❌ 블루투스 이름 설정에 실패했습니다.")
        sys.exit(1) 