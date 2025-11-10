# modules/naver_search.py
"""
네이버 검색량 분석 모듈

FR-003: 검색량 분석
- FR-003-1: 네이버 API 연동
- FR-003-2: 대안: 검색 결과 수로 추정
"""

import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from tqdm import tqdm
import time
from dotenv import load_dotenv
import config
from modules.utils import wait_with_delay


# 환경변수 로드
load_dotenv()


class NaverSearchAnalyzer:
    """네이버 검색량 분석기"""

    def __init__(self):
        self.client_id = os.getenv('NAVER_CLIENT_ID')
        self.client_secret = os.getenv('NAVER_CLIENT_SECRET')

        # API 사용 가능 여부
        self.api_available = bool(self.client_id and self.client_secret
                                   and self.client_id != 'your_client_id_here'
                                   and self.client_secret != 'your_client_secret_here')

        if self.api_available:
            logger.info("네이버 API 사용 가능")
        else:
            logger.info("네이버 API 미설정 - 대안 방법 사용")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT
        })

    def get_search_volume_api(self, keyword: str) -> Optional[int]:
        """
        FR-003-1: 네이버 데이터랩 API로 검색량 조회

        Args:
            keyword: 검색 키워드

        Returns:
            월 검색량 (추정치) 또는 None
        """
        try:
            # 날짜 설정 (최근 1개월)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            headers = {
                'X-Naver-Client-Id': self.client_id,
                'X-Naver-Client-Secret': self.client_secret,
                'Content-Type': 'application/json'
            }

            body = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "timeUnit": "month",
                "keywordGroups": [
                    {
                        "groupName": keyword,
                        "keywords": [keyword]
                    }
                ]
            }

            response = requests.post(
                config.NAVER_DATALAB_URL,
                headers=headers,
                json=body,
                timeout=config.REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()

                if 'results' in data and data['results']:
                    # ratio 값 추출 (0-100)
                    ratio = data['results'][0]['data'][0]['ratio']

                    # 절대값으로 변환 (ratio * 1000을 기준으로 추정)
                    estimated_volume = int(ratio * 1000)

                    logger.debug(f"{keyword}: API 검색량 = {estimated_volume}")
                    return estimated_volume

            elif response.status_code == 429:
                logger.warning("API 할당량 초과 - 대안 방법으로 전환")
                return None

            elif response.status_code == 401:
                logger.error("API 인증 실패 - API 키 확인 필요")
                return None

            else:
                logger.warning(f"API 오류: {response.status_code}")
                return None

        except Exception as e:
            logger.debug(f"API 검색량 조회 실패 ({keyword}): {e}")
            return None

    def get_search_volume_estimate(self, keyword: str) -> int:
        """
        FR-003-2: 네이버 쇼핑 검색 결과 수로 검색량 추정

        Args:
            keyword: 검색 키워드

        Returns:
            추정 월 검색량
        """
        try:
            params = {
                'query': keyword,
                'cat_id': '',
                'frm': 'NVSHATC'
            }

            response = self.session.get(
                config.NAVER_SHOPPING_URL,
                params=params,
                timeout=config.REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # 검색 결과 개수 추출
                result_count = 0

                # 여러 선택자 시도
                selectors = [
                    '.subFilter_filter__2Z3aR .subFilter_count__35J_c',
                    '.subFilter_count__35J_c',
                    '[class*="count"]',
                    '.basicList_num__13y6C'
                ]

                for selector in selectors:
                    count_elem = soup.select_one(selector)
                    if count_elem:
                        try:
                            # 숫자만 추출
                            import re
                            text = count_elem.get_text(strip=True)
                            numbers = re.findall(r'\d+', text.replace(',', ''))
                            if numbers:
                                result_count = int(numbers[0])
                                break
                        except:
                            continue

                # 검색량 추정 공식
                # 검색 결과수가 많을수록 검색량도 높다고 가정
                # 결과수 * 5를 기본 검색량으로 추정
                if result_count > 0:
                    estimated_volume = min(result_count * 5, 100000)
                else:
                    # 결과가 없으면 최소값
                    estimated_volume = 1000

                logger.debug(f"{keyword}: 추정 검색량 = {estimated_volume} (결과수: {result_count})")
                return estimated_volume

            else:
                # 기본값 반환
                return 5000

        except Exception as e:
            logger.debug(f"검색량 추정 실패 ({keyword}): {e}")
            # 기본값 반환
            return 5000

    def get_search_volume(self, keyword: str) -> int:
        """
        검색량 조회 (API 우선, 실패 시 추정)

        Args:
            keyword: 검색 키워드

        Returns:
            월 검색량
        """
        # API 사용 가능하면 먼저 시도
        if self.api_available:
            volume = self.get_search_volume_api(keyword)
            if volume is not None:
                return volume

        # API 실패 or 미사용 시 추정 방법 사용
        return self.get_search_volume_estimate(keyword)

    def analyze_keywords(self, keywords: List[str]) -> Dict[str, int]:
        """
        여러 키워드의 검색량 일괄 분석

        Args:
            keywords: 키워드 리스트

        Returns:
            {키워드: 검색량} 딕셔너리
        """
        logger.info(f"검색량 분석 시작: {len(keywords)}개 키워드")

        results = {}

        # 진행바와 함께 처리
        for keyword in tqdm(keywords, desc="  검색량 조회", leave=False):
            try:
                volume = self.get_search_volume(keyword)
                results[keyword] = volume

                # API 과부하 방지
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"검색량 조회 실패 ({keyword}): {e}")
                results[keyword] = 0

        logger.info(f"검색량 분석 완료: {len(results)}개")

        return results


def main():
    """테스트용 메인 함수"""
    from modules.utils import setup_logger

    setup_logger()

    print("="*50)
    print("🔍 네이버 검색량 분석 테스트")
    print("="*50)

    analyzer = NaverSearchAnalyzer()

    # 테스트 키워드
    test_keywords = [
        "주방용품",
        "밀폐용기",
        "김치냉장고",
        "에어프라이어",
    ]

    print(f"\n테스트 키워드: {len(test_keywords)}개")
    print("-" * 50)

    results = analyzer.analyze_keywords(test_keywords)

    print("\n📊 검색량 분석 결과:")
    print("-" * 50)

    for keyword, volume in results.items():
        print(f"{keyword:20s}: {volume:>8,}회/월")


if __name__ == '__main__':
    main()
