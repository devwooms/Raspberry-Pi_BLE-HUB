#!/usr/bin/env python3
import os
import sys

# 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 메인 함수 임포트
from blehub.blehub import main

if __name__ == "__main__":
    sys.exit(main()) 