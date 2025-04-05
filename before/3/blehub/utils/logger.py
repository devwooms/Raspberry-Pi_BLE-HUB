#!/usr/bin/env python3
import os
import logging
from pathlib import Path

"""
BLE-HUB 로깅 모듈

애플리케이션 전체에서 사용하는 로깅 기능을 제공합니다.
"""

def setup_logger(log_file=None, log_level=logging.INFO):
    """로깅 설정을 초기화합니다
    
    Args:
        log_file (str): 로그 파일 경로. None인 경우 기본 경로 사용
        log_level (int): 로깅 레벨
        
    Returns:
        Logger: 설정된 로거 인스턴스
    """
    # 스크립트 위치 기준으로 경로 계산
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 로그 파일 경로 설정
    if log_file is None:
        log_file = os.path.join(script_dir, "blehub.log")
    
    # 로깅 설정
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("BLE-HUB")

# 로거 인스턴스 생성
logger = setup_logger()

# 로그 레벨 설정 헬퍼 함수
def set_log_level(level):
    """로그 레벨을 설정합니다
    
    Args:
        level (str): 로그 레벨 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    numeric_level = getattr(logging, level.upper(), None)
    if isinstance(numeric_level, int):
        logger.setLevel(numeric_level)
        for handler in logger.handlers:
            handler.setLevel(numeric_level)
    else:
        raise ValueError(f"유효하지 않은 로그 레벨: {level}") 