#!/bin/bash

# NeuroFlow macOS - GitHub Push Script
# 이 스크립트는 NeuroFlow macOS 버전을 GitHub에 push합니다.

echo "🧠 NeuroFlow macOS - GitHub Push Script"
echo "========================================"
echo ""

# 현재 디렉토리 확인
if [ ! -f "ct_perfusion_viewer.py" ]; then
    echo "❌ Error: ct_perfusion_viewer.py not found"
    echo "Please run this script from the Neuroflow_mac directory"
    exit 1
fi

# Git 상태 확인
echo "📊 Checking git status..."
git status

echo ""
echo "⚠️  WARNING: This will push to GitHub repository"
echo "Repository: https://github.com/HyukJang1/ct-perfusion-auto"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

# 커밋
echo ""
echo "📝 Creating commit..."
git commit -m "feat: NeuroFlow macOS version

Features:
- One-click CT Perfusion analysis with Apple design UI
- Interactive web viewer with overlay controls
- Advanced stroke metrics (HIR, PRR, CBV Index, Collateral Grade)
- Smart brain masking with RGB background removal
- PENUMBRA series overlay exclusion
- Siemens RGB to scalar conversion
- Beautiful color-coded metrics table

Technical improvements:
- Background removal: RGB sum <10 → Scalar = 0
- Brain mask: OR operation for robust tissue detection
- Slice-by-slice overlay matching with z-position validation
- Apple design guidelines for UI/UX

Documentation:
- Comprehensive README_MAC.md
- GitHub setup guide
- Quick start guide
- Validation documentation
"

if [ $? -ne 0 ]; then
    echo "❌ Commit failed"
    exit 1
fi

# 원격 저장소 추가 (이미 있으면 무시)
echo ""
echo "🌐 Adding remote repository..."
git remote add origin https://github.com/HyukJang1/ct-perfusion-auto.git 2>/dev/null || true

# 브랜치 확인/생성
echo ""
echo "🌿 Setting up branch..."
git branch -M main

# Push
echo ""
echo "🚀 Pushing to GitHub..."
echo "⚠️  This will FORCE PUSH and overwrite existing content"
read -p "Are you sure? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

git push -f origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "📍 Repository: https://github.com/HyukJang1/ct-perfusion-auto"
    echo ""
    echo "Next steps:"
    echo "1. Visit the repository on GitHub"
    echo "2. Create a release (v1.0.0-macos)"
    echo "3. Update repository description"
    echo "4. Add topics: macos, ct-perfusion, stroke, medical-imaging"
else
    echo ""
    echo "❌ Push failed"
    echo "Please check your GitHub credentials and try again"
    exit 1
fi
