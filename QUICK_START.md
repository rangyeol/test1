# ⚡ 빠른 시작 가이드

## 🎯 1분 안에 시작하기

### Step 1: 저장소 다운로드
```bash
git clone <repository-url>
cd test1
```

### Step 2: 패키지 설치 (Windows)
```cmd
pip install requests beautifulsoup4 pandas openpyxl selenium websockets

# undetected-chromedriver는 pip로 설치 시도
pip install undetected-chromedriver

# 실패 시, 아래 명령 사용
pip install --upgrade pip setuptools wheel
pip install undetected-chromedriver --no-cache-dir
```

### Step 3: GUI 실행
```bash
python coupang_gui.py
```

![GUI 스크린샷 예시]
```
┌─────────────────────────────────────┐
│  쿠팡 상품 수집기                      │
├─────────────────────────────────────┤
│  검색어: [무선마우스          ] [추가] │
│                                      │
│  페이지수: [3]  병렬처리: [✓]          │
│                                      │
│  [수집 시작]  [중지]  [로그 지우기]    │
├─────────────────────────────────────┤
│  진행률: ████████░░ 80%               │
│                                      │
│  [로그]                               │
│  [OK] 검색 완료                       │
│  [OK] 36개 상품 수집                  │
│  [OK] Excel 저장 완료                 │
└─────────────────────────────────────┘
```

---

## 🚀 가장 간단한 사용법

### 방법 1: GUI로 실행 (추천)
```bash
python coupang_gui.py
```
1. "무선마우스" 입력 → "추가" 클릭
2. 페이지수 "3" 설정
3. "수집 시작" 클릭
4. Excel 파일 자동 생성!

### 방법 2: Python 코드 3줄
```python
from coupang_scraper_integrated import *

driver = initialize_driver(headless=False)  # 브라우저 시작
driver = setup_coupang_main(driver)         # 쿠팡 접속
run_full_pipeline(driver, '무선마우스', 3)  # 데이터 수집
```

### 방법 3: 명령줄 (가장 빠름)
```python
# run.py 생성
from coupang_scraper_integrated import *
driver = initialize_driver()
setup_coupang_main(driver)
run_full_pipeline(driver, '무선마우스', 3)
driver.quit()
```

```bash
python run.py
```

---

## 🎯 실전 예제

### 예제 1: 로켓배송 상품만 수집
```python
# 쿠팡에서 검색 후 URL 복사
url = "https://www.coupang.com/np/search?q=무선마우스&filter=로켓배송"

driver = initialize_driver()
setup_coupang_main(driver)
run_full_pipeline(driver, url, max_pages=5)
driver.quit()
```

### 예제 2: 여러 키워드 자동 수집
```python
keywords = ['무선마우스', '무선키보드', '모니터']

driver = initialize_driver()
setup_coupang_main(driver)

for keyword in keywords:
    print(f"\n수집 중: {keyword}")
    run_full_pipeline(driver, keyword, max_pages=3)

driver.quit()
```

### 예제 3: 안전 모드 (느리지만 확실)
```python
driver = initialize_driver(headless=False)
setup_coupang_main(driver)
run_full_pipeline(
    driver,
    '무선마우스',
    max_pages=5,
    is_parallel=False  # 느린 속도로 안전하게
)
driver.quit()
```

---

## 📁 결과 파일

수집 완료 후 자동으로 생성됩니다:

```
test1/
├── coupang_무선마우스_3페이지_108개_20251110.xlsx  ✅ 수집 결과!
├── progress_search_무선마우스_20251110.json       (진행 상황)
└── logs/
    └── network_logs_20251110_123456.json         (네트워크 로그)
```

---

## ⚠️ 자주 묻는 질문

### Q1: "undetected_chromedriver" 에러
```
ModuleNotFoundError: No module named 'undetected_chromedriver'
```
**A:**
```bash
pip install undetected-chromedriver --upgrade
# 실패 시
pip install git+https://github.com/ultrafunkamsterdam/undetected-chromedriver.git
```

### Q2: Chrome 버전 에러
```
ChromeDriver version mismatch
```
**A:** Chrome 브라우저를 최신 버전으로 업데이트

### Q3: 봇 차단
```
[SKIP] 봇 차단 의심
```
**A:**
```python
run_full_pipeline(driver, keyword, max_pages=3, is_parallel=False)
```

### Q4: Headless 모드 실패
**A:** `headless=False`로 변경 (브라우저 창 표시)

---

## 🎓 더 알아보기

- **상세 가이드**: `TEST_GUIDE.md`
- **기술 문서**: `README.md`
- **코드 예제**: `test_simple.py`

---

## ✅ 체크리스트

실행 전 확인사항:

- [ ] Python 3.8+ 설치됨
- [ ] Chrome 브라우저 최신 버전
- [ ] pip로 패키지 설치 완료
- [ ] 인터넷 연결 안정적

**모두 체크했다면 실행!**
```bash
python coupang_gui.py
```

---

**즐거운 데이터 수집 되세요! 🎉**
