#!/usr/bin/env python3
import os
import logging
from pathlib import Path

# 스크립트의 경로
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logger():
    """로깅 설정을 초기화합니다"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(SCRIPT_DIR, "blehub.log")),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("BLE-HUB")

# 로거 인스턴스 생성
logger = setup_logger() 