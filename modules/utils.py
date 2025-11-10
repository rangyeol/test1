# modules/utils.py
"""
공통 유틸리티 함수
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Optional
from loguru import logger
import config


def setup_logger():
    """로거 설정"""
    log_file = os.path.join(
        config.LOG_DIR,
        f"app_{datetime.now().strftime('%Y%m%d')}.log"
    )

    logger.add(
        log_file,
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        encoding="utf-8"
    )

    return logger


def load_stopwords(file_path: Optional[str] = None) -> List[str]:
    """
    불용어 리스트 로드

    Args:
        file_path: 불용어 파일 경로 (기본값: data/stopwords.txt)

    Returns:
        불용어 리스트
    """
    if file_path is None:
        file_path = os.path.join(config.DATA_DIR, 'stopwords.txt')

    stopwords = config.STOPWORDS.copy()

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_stopwords = [line.strip() for line in f if line.strip()]
                stopwords.extend(file_stopwords)
        except Exception as e:
            logger.warning(f"불용어 파일 로드 실패: {e}")

    return list(set(stopwords))


def filter_stopwords(keywords: List[str], stopwords: Optional[List[str]] = None) -> List[str]:
    """
    불용어 필터링

    Args:
        keywords: 키워드 리스트
        stopwords: 불용어 리스트 (기본값: config.STOPWORDS)

    Returns:
        필터링된 키워드 리스트
    """
    if stopwords is None:
        stopwords = load_stopwords()

    filtered = []
    for keyword in keywords:
        # 불용어가 포함된 키워드 제외
        if not any(stopword in keyword for stopword in stopwords):
            filtered.append(keyword)

    return filtered


def remove_duplicates(keywords: List[str]) -> List[str]:
    """
    중복 제거 (순서 유지)

    Args:
        keywords: 키워드 리스트

    Returns:
        중복 제거된 키워드 리스트
    """
    seen = set()
    result = []
    for keyword in keywords:
        keyword_lower = keyword.lower().strip()
        if keyword_lower and keyword_lower not in seen:
            seen.add(keyword_lower)
            result.append(keyword.strip())

    return result


def sanitize_keyword(keyword: str) -> str:
    """
    키워드 정제 (특수문자 제거, 공백 정리)

    Args:
        keyword: 원본 키워드

    Returns:
        정제된 키워드
    """
    # 앞뒤 공백 제거
    keyword = keyword.strip()

    # 연속된 공백을 하나로
    keyword = ' '.join(keyword.split())

    # 제거할 특수문자
    remove_chars = ['[', ']', '{', '}', '<', '>', '|', '\\', '^', '~']
    for char in remove_chars:
        keyword = keyword.replace(char, '')

    return keyword


def create_output_filename(category: str, suffix: str = '') -> str:
    """
    출력 파일명 생성

    Args:
        category: 카테고리명
        suffix: 파일명 접미사

    Returns:
        파일명 (예: "주방_블루오션_20251110_143052.xlsx")
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    category_clean = category.replace('/', '_').replace('\\', '_')

    if suffix:
        filename = f"{category_clean}_{suffix}_{timestamp}.xlsx"
    else:
        filename = f"{category_clean}_블루오션_{timestamp}.xlsx"

    return os.path.join(config.OUTPUT_DIR, filename)


def wait_with_delay(seconds: Optional[float] = None):
    """
    지연 시간 대기

    Args:
        seconds: 대기 시간 (기본값: config.CRAWL_DELAY)
    """
    if seconds is None:
        seconds = config.CRAWL_DELAY

    time.sleep(seconds)


def validate_category(category: str) -> bool:
    """
    카테고리 입력 검증

    Args:
        category: 카테고리명

    Returns:
        유효성 여부
    """
    if not category or not category.strip():
        return False

    # 너무 긴 입력 제한
    if len(category) > 50:
        return False

    # 허용할 문자: 한글, 영문, 숫자, 공백, 일부 특수문자
    import re
    pattern = r'^[가-힣a-zA-Z0-9\s\-_/]+$'

    return bool(re.match(pattern, category.strip()))


def format_number(num: int) -> str:
    """
    숫자 포맷팅 (천 단위 콤마)

    Args:
        num: 숫자

    Returns:
        포맷팅된 문자열 (예: "1,234")
    """
    return f"{num:,}"


def calculate_elapsed_time(start_time: float) -> str:
    """
    경과 시간 계산

    Args:
        start_time: 시작 시간 (time.time())

    Returns:
        경과 시간 문자열 (예: "14분 32초")
    """
    elapsed = int(time.time() - start_time)
    minutes = elapsed // 60
    seconds = elapsed % 60

    if minutes > 0:
        return f"{minutes}분 {seconds}초"
    else:
        return f"{seconds}초"
