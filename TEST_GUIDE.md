# 쿠팡 스크래핑 시스템 테스트 가이드

## 🚀 시스템 요구사항

### 필수 소프트웨어
- **Python 3.8 이상**
- **Google Chrome 브라우저** (최신 버전 권장)
- **Windows, macOS, 또는 Linux (GUI 지원)**

### 설치 방법

#### 1. 저장소 클론
```bash
git clone <repository-url>
cd test1
```

#### 2. 가상환경 생성 (권장)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. 패키지 설치

**주의**: GUI를 사용하지 않을 경우 ttkthemes 제외하고 설치
```bash
# GUI 포함 (권장)
pip install -r requirements.txt

# GUI 없이 (CLI만)
pip install requests beautifulsoup4 pandas openpyxl python-dotenv tqdm retry loguru lxml selenium undetected-chromedriver
```

## 📋 테스트 방법

### 방법 1: GUI로 실행 (가장 쉬움) ⭐ 권장

```bash
python coupang_gui.py
```

**GUI 사용법:**
1. **검색어 입력**: "무선마우스" 같은 키워드 입력
2. **검색어 추가**: "추가" 버튼 클릭
3. **설정 조정**:
   - 페이지 수: 1~20 (테스트는 1~3 권장)
   - 병렬 처리: 빠른 수집 (체크)
   - Headless: 백그라운드 실행 (선택)
4. **수집 시작**: "수집 시작" 버튼 클릭
5. **진행 상황**: 하단 로그에서 실시간 확인
6. **결과 확인**: Excel 파일 자동 생성 (coupang_*.xlsx)

### 방법 2: Python 스크립트로 직접 실행

```python
from coupang_scraper_integrated import initialize_driver, setup_coupang_main, run_full_pipeline

# 1. 드라이버 초기화 (브라우저 표시)
driver = initialize_driver(headless=False)

# 2. 쿠팡 메인 페이지 설정
driver = setup_coupang_main(driver)

# 3. 키워드로 검색하고 데이터 수집
result = run_full_pipeline(
    driver,
    '무선마우스',      # 검색 키워드
    max_pages=3,      # 최대 페이지 수
    is_parallel=True  # 병렬 처리 여부
)

# 4. 결과 확인
print(result)

# 5. 드라이버 종료
driver.quit()
```

### 방법 3: 간단한 테스트 스크립트

```python
# test_simple.py
import sys
from coupang_scraper_integrated import initialize_driver, search_coupang

try:
    print("=" * 60)
    print("쿠팡 스크래핑 간단 테스트")
    print("=" * 60)

    # 드라이버 초기화
    print("\n[1] 드라이버 초기화 중...")
    driver = initialize_driver(headless=False)
    print("[OK] 드라이버 초기화 완료!")

    # 쿠팡 접속
    print("\n[2] 쿠팡 접속 중...")
    driver.get("https://www.coupang.com")
    print("[OK] 쿠팡 접속 완료!")

    # 간단한 검색 테스트
    print("\n[3] '무선마우스' 검색 테스트...")
    success = search_coupang(driver, "무선마우스", is_parallel=False)

    if success:
        print("\n" + "=" * 60)
        print("[성공] 쿠팡 스크래핑 시스템이 정상 작동합니다!")
        print("=" * 60)
    else:
        print("\n[실패] 검색 실패")

    # 10초 대기 (결과 확인용)
    import time
    print("\n10초 후 브라우저를 닫습니다...")
    time.sleep(10)

    driver.quit()

except Exception as e:
    print(f"\n[오류] {e}")
    import traceback
    traceback.print_exc()
```

```bash
python test_simple.py
```

## 🎯 테스트 시나리오

### 시나리오 1: 키워드 검색 (기본)
```python
result = run_full_pipeline(driver, '무선마우스', max_pages=2)
```
- 예상 결과: `coupang_무선마우스_2페이지_XX개_20251110.xlsx`

### 시나리오 2: 검색 URL 사용 (필터 적용)
```python
url = "https://www.coupang.com/np/search?q=무선마우스&filter=로켓배송"
result = run_full_pipeline(driver, url, max_pages=3)
```
- URL에 필터, 정렬 등 모든 옵션 포함 가능

### 시나리오 3: 단일 상품 상세 정보
```python
url = "https://www.coupang.com/vp/products/123456789"
result = run_full_pipeline(driver, url)
```
- 예상 결과: `coupang_단일상품_20251110.xlsx`

## 🔧 문제 해결

### 1. Chrome 버전 에러
```
undetected-chromedriver 버전과 Chrome 버전 불일치
```
**해결**: Chrome을 최신 버전으로 업데이트

### 2. 봇 차단 감지
```
[SKIP] 봇 차단 의심 - 페이지에 차단 관련 키워드 발견
```
**해결**:
- `is_parallel=False` 설정 (느리지만 안전)
- 대기 시간 증가
- VPN 사용 고려

### 3. Headless 모드에서 실패
```
페이지 로딩 실패 또는 상품 없음
```
**해결**: `headless=False`로 변경 (브라우저 표시)

### 4. 패키지 설치 실패
```
ModuleNotFoundError: No module named 'tkinter'
```
**해결 (Ubuntu/Debian)**:
```bash
sudo apt-get install python3-tk
```

## 📊 수집 데이터 구조

### 상품 목록 (11개 컬럼)
| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| 번호 | 순번 | 1 |
| 상품ID | 쿠팡 상품 ID | 7654321 |
| 상품명 | 제품명 | 로지텍 무선마우스 M331 |
| 가격_할인전 | 정가 | 49,900원 |
| 할인율 | 할인율 | 40% |
| 판매가 | 최종 가격 | 29,900원 |
| 판매구분 | 배송 타입 | 로켓배송 |
| 배송정보 | 배송 상세 | 오늘 도착 |
| 별점 | 평점 | 4.5 |
| 리뷰수 | 리뷰 개수 | (1,234) |
| 링크 | 상품 URL | https://www.coupang.com/vp/... |

## 🎮 고급 기능

### 1. 네트워크 모니터링 활성화
```python
from network_monitor import setup_network_monitoring

driver = initialize_driver()
monitor = setup_network_monitoring(driver, enabled=True)

# 수집 작업...

# API 엔드포인트 확인
api_endpoints = monitor.get_api_endpoints()
print(f"발견된 API: {len(api_endpoints)}개")

# 로그 저장
monitor.save_logs()
```

### 2. 이미지 다운로드
```python
result = run_full_pipeline(
    driver,
    '무선마우스',
    download_images=True  # 이미지 다운로드 활성화
)
```
- 이미지는 `images/` 폴더에 저장

### 3. 중단 후 재개
```python
result = run_full_pipeline(
    driver,
    '무선마우스',
    max_pages=10,
    resume=True  # 이전 진행 상황에서 재개
)
```

## 📝 주의사항

1. **쿠팡 이용약관 준수**: 과도한 크롤링 금지
2. **봇 차단**: 너무 빠른 속도는 차단될 수 있음
3. **데이터 사용**: 개인 학습/연구 목적으로만 사용
4. **대기 시간**: `is_parallel=False` 설정으로 안전하게 수집
5. **로그 확인**: 문제 발생 시 콘솔 로그 확인

## 🆘 지원

문제가 발생하면 다음을 확인하세요:
1. Chrome 브라우저가 최신 버전인가?
2. Python 버전이 3.8 이상인가?
3. 모든 패키지가 정상 설치되었는가?
4. 인터넷 연결이 안정적인가?

## 📦 생성되는 파일

```
test1/
├── coupang_무선마우스_3페이지_108개_20251110.xlsx  # 수집 결과
├── progress_search_무선마우스_20251110.json        # 진행 상황
├── logs/
│   └── network_logs_20251110_123456.json         # 네트워크 로그
└── images/                                        # 이미지 (옵션)
    ├── product_123456_thumb.jpg
    └── product_123456_detail_1.jpg
```

---

**Happy Scraping! 🚀**
