#!/bin/bash

# NeuroFlow - CT Perfusion Analyzer Launcher
# macOS용 실행 스크립트

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# Python 가상환경 확인
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Python 실행
python3 ct_perfusion_viewer.py

# 종료 대기
read -p "Press Enter to close..."
