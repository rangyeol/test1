# config.py
"""
쿠팡 블루오션 자동 발굴 시스템 - 설정 파일
"""

# ============================================
# 블루오션 기준
# ============================================
MIN_SEARCH_VOLUME = 5000    # 최소 검색량
MAX_SEARCH_VOLUME = 20000   # 최대 검색량
MIN_PRODUCT_COUNT = 5       # 최소 상품 수
MAX_PRODUCT_COUNT = 15      # 최대 상품 수

# ============================================
# 크롤링 설정
# ============================================
CRAWL_DELAY = 2             # 요청 간 대기 (초)
MAX_RETRIES = 3             # 최대 재시도 횟수
REQUEST_TIMEOUT = 10        # 타임아웃 (초)

# ============================================
# User-Agent
# ============================================
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)

# ============================================
# 불용어 리스트
# ============================================
STOPWORDS = [
    '무료배송', '최저가', '할인', '이벤트',
    '세일', '특가', '추천', '인기', '베스트',
    '쿠폰', '타임특가', '핫딜', '오늘만',
    '빠른배송', '로켓배송', '당일배송'
]

# ============================================
# 키워드 생성 설정
# ============================================
KEYWORD_EXPANSION_DEPTH = 2  # 확장 깊이
MAX_KEYWORDS_PER_SEED = 20   # seed당 최대 키워드
TARGET_KEYWORD_COUNT = 150   # 목표 키워드 수

# ============================================
# 출력 설정
# ============================================
OUTPUT_DIR = 'output'
LOG_DIR = 'logs'
DATA_DIR = 'data'
TOP_N_RESULTS = 10          # TOP N 출력

# ============================================
# 네이버 설정
# ============================================
NAVER_SHOPPING_URL = 'https://search.shopping.naver.com/search/all'
NAVER_AUTOCOMPLETE_URL = 'https://ac.shopping.naver.com/ac'
NAVER_DATALAB_URL = 'https://openapi.naver.com/v1/datalab/search'

# ============================================
# 쿠팡 설정
# ============================================
COUPANG_SEARCH_URL = 'https://www.coupang.com/np/search'
