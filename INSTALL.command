#!/bin/bash

# NeuroFlow - 자동 설치 스크립트
# 이 파일을 더블클릭하면 자동으로 설치됩니다

echo "🧠 NeuroFlow - CT Perfusion Analyzer"
echo "===================================="
echo ""
echo "📦 자동 설치를 시작합니다..."
echo ""

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# Python 버전 확인
echo "🔍 Python 버전 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3가 설치되어 있지 않습니다."
    echo ""
    echo "다음 링크에서 Python을 설치해주세요:"
    echo "https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION 발견"
echo ""

# pip 업그레이드
echo "📦 pip 업그레이드 중..."
python3 -m pip install --upgrade pip --quiet

# 의존성 설치
echo "📦 필요한 패키지 설치 중..."
echo "   (이 작업은 몇 분 소요될 수 있습니다)"
echo ""

if pip3 install -r requirements.txt; then
    echo ""
    echo "✅ 설치 완료!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 NeuroFlow를 실행하려면:"
    echo ""
    echo "   NeuroFlow_Launcher.command 더블클릭"
    echo ""
    echo "   또는 터미널에서:"
    echo "   ./NeuroFlow_Launcher.command"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
else
    echo ""
    echo "❌ 설치 중 오류가 발생했습니다."
    echo ""
    echo "다음 명령어를 터미널에서 직접 실행해보세요:"
    echo "pip3 install -r requirements.txt"
    echo ""
fi

read -p "Press Enter to close..."
