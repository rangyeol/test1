#!/bin/bash

# setup.sh
# 쿠팡 블루오션 자동 발굴 시스템 설치 스크립트

echo "======================================================================"
echo "🎯 쿠팡 블루오션 자동 발굴 시스템 설치"
echo "======================================================================"
echo ""

# 1. Python 버전 확인
echo "📌 [1/5] Python 버전 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3가 설치되어 있지 않습니다."
    echo "   Python 3.9 이상을 설치해주세요."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Python ${PYTHON_VERSION} 확인됨"
echo ""

# 2. 가상환경 생성
echo "📌 [2/5] 가상환경 생성 중..."
if [ -d "venv" ]; then
    echo "⚠️  venv 폴더가 이미 존재합니다."
    read -p "   삭제하고 다시 만들까요? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo "✅ 가상환경 재생성 완료"
    else
        echo "✅ 기존 가상환경 사용"
    fi
else
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
fi
echo ""

# 3. 가상환경 활성화
echo "📌 [3/5] 가상환경 활성화 중..."
source venv/bin/activate
if [ $? -eq 0 ]; then
    echo "✅ 가상환경 활성화 완료"
else
    echo "❌ 가상환경 활성화 실패"
    exit 1
fi
echo ""

# 4. 라이브러리 설치
echo "📌 [4/5] 라이브러리 설치 중..."
pip install --upgrade pip -q
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ 라이브러리 설치 완료"
else
    echo "❌ 라이브러리 설치 실패"
    exit 1
fi
echo ""

# 5. 환경변수 파일 생성
echo "📌 [5/5] 환경변수 파일 설정..."
if [ ! -f ".env" ]; then
    cp .env.template .env
    echo "✅ .env 파일 생성 완료"
    echo ""
    echo "📝 다음 단계:"
    echo "   1. .env 파일을 열어주세요"
    echo "   2. 네이버 API 키를 입력하세요 (선택사항)"
    echo "      - https://developers.naver.com/ 에서 발급"
    echo "      - API 키가 없어도 실행 가능 (대안 방법 사용)"
else
    echo "✅ .env 파일이 이미 존재합니다"
fi
echo ""

# 완료
echo "======================================================================"
echo "✨ 설치 완료!"
echo "======================================================================"
echo ""
echo "🚀 실행 방법:"
echo "   1. 가상환경 활성화: source venv/bin/activate"
echo "   2. 프로그램 실행: python main.py"
echo ""
echo "📚 도움말:"
echo "   - README.md 파일을 참고하세요"
echo "   - 문제 발생 시: 이슈 등록"
echo ""
echo "======================================================================"
