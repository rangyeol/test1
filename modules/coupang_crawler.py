# modules/coupang_crawler.py
"""
쿠팡 상품 개수 크롤링 모듈

FR-004: 쿠팡 상품 개수 크롤링
- FR-004-1: 검색 요청
- FR-004-2: 상품 개수 추출
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from loguru import logger
from tqdm import tqdm
import re
import time
from retry import retry
import config
from modules.utils import wait_with_delay


class CoupangCrawler:
    """쿠팡 상품 개수 크롤러"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    @retry(tries=3, delay=2, backoff=2)
    def get_product_count(self, keyword: str) -> int:
        """
        FR-004: 쿠팡 상품 개수 크롤링

        Args:
            keyword: 검색 키워드

        Returns:
            상품 개수
        """
        try:
            # FR-004-1: 검색 요청
            params = {
                'q': keyword,
                'channel': 'user'
            }

            response = self.session.get(
                config.COUPANG_SEARCH_URL,
                params=params,
                timeout=config.REQUEST_TIMEOUT
            )

            # 차단 감지
            if response.status_code == 403 or '차단' in response.text:
                logger.warning(f"쿠팡 차단 감지: {keyword}")
                return -1  # 차단 표시

            if response.status_code != 200:
                logger.warning(f"쿠팡 검색 실패: {keyword} (status: {response.status_code})")
                return 0

            # FR-004-2: 상품 개수 추출
            soup = BeautifulSoup(response.text, 'html.parser')

            # 방법 1: 검색 결과 개수 텍스트에서 추출
            count = self._extract_from_result_count(soup)
            if count is not None:
                logger.debug(f"{keyword}: 상품 {count}개 (방법1: 결과수)")
                return count

            # 방법 2: 상품 리스트에서 개수 계산
            count = self._extract_from_product_list(soup)
            if count is not None:
                logger.debug(f"{keyword}: 상품 {count}개 (방법2: 리스트)")
                return count

            # 방법 3: 페이지네이션에서 추정
            count = self._extract_from_pagination(soup)
            if count is not None:
                logger.debug(f"{keyword}: 상품 약 {count}개 (방법3: 페이지)")
                return count

            # 모두 실패하면 기본값
            logger.debug(f"{keyword}: 상품 개수 추출 실패 - 기본값 사용")
            return 10  # 기본값

        except Exception as e:
            logger.error(f"쿠팡 크롤링 오류 ({keyword}): {e}")
            return 0

    def _extract_from_result_count(self, soup: BeautifulSoup) -> int:
        """방법 1: 검색 결과 개수 텍스트에서 추출"""
        selectors = [
            '.search-product-count',
            '[class*="product-count"]',
            '[class*="result-count"]',
            '.search-result-count'
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                # "총 123개" 형식에서 숫자 추출
                numbers = re.findall(r'(\d+(?:,\d+)*)', text)
                if numbers:
                    count_str = numbers[0].replace(',', '')
                    try:
                        return int(count_str)
                    except:
                        continue

        return None

    def _extract_from_product_list(self, soup: BeautifulSoup) -> int:
        """방법 2: 상품 리스트에서 개수 계산"""
        selectors = [
            'li.search-product',
            '[class*="search-product"]',
            'li[data-product-id]',
            '.product-item'
        ]

        for selector in selectors:
            products = soup.select(selector)
            if products and len(products) > 0:
                # 1페이지 상품 수 * 추정 페이지 수
                # (보수적으로 1페이지 상품 수만 반환)
                return len(products)

        return None

    def _extract_from_pagination(self, soup: BeautifulSoup) -> int:
        """방법 3: 페이지네이션에서 추정"""
        try:
            # 페이지네이션 찾기
            pagination = soup.select('.pagination a, [class*="pagination"] a')

            if pagination:
                # 마지막 페이지 번호 찾기
                max_page = 1
                for link in pagination:
                    text = link.get_text(strip=True)
                    if text.isdigit():
                        page_num = int(text)
                        max_page = max(max_page, page_num)

                # 페이지당 평균 40개 상품으로 추정
                estimated_count = max_page * 40
                return estimated_count

        except:
            pass

        return None

    def analyze_keywords(self, keywords: List[str]) -> Dict[str, int]:
        """
        여러 키워드의 상품 개수 일괄 분석

        Args:
            keywords: 키워드 리스트

        Returns:
            {키워드: 상품개수} 딕셔너리
        """
        logger.info(f"쿠팡 상품 개수 분석 시작: {len(keywords)}개 키워드")

        results = {}
        blocked_count = 0

        # 진행바와 함께 처리
        for keyword in tqdm(keywords, desc="  쿠팡 상품수 확인", leave=False):
            try:
                count = self.get_product_count(keyword)

                if count == -1:
                    # 차단된 경우
                    blocked_count += 1
                    if blocked_count >= 3:
                        logger.error("쿠팡 차단 감지 - 크롤링 중단")
                        print("\n⚠️ 쿠팡에서 차단되었습니다.")
                        print("해결방법:")
                        print("  1. VPN 사용")
                        print("  2. 1시간 후 재시도")
                        print("  3. config.CRAWL_DELAY 증가 (현재: {}초)".format(config.CRAWL_DELAY))
                        # 나머지는 기본값으로
                        for remaining_kw in keywords[len(results):]:
                            results[remaining_kw] = 10
                        break
                    count = 10  # 차단되면 기본값

                results[keyword] = count

                # 크롤링 딜레이
                wait_with_delay()

            except Exception as e:
                logger.error(f"상품 개수 조회 실패 ({keyword}): {e}")
                results[keyword] = 0

        logger.info(f"쿠팡 상품 개수 분석 완료: {len(results)}개")

        return results


def main():
    """테스트용 메인 함수"""
    from modules.utils import setup_logger

    setup_logger()

    print("="*50)
    print("🛒 쿠팡 상품 개수 크롤링 테스트")
    print("="*50)

    crawler = CoupangCrawler()

    # 테스트 키워드
    test_keywords = [
        "주방용품",
        "밀폐용기",
        "김치냉장고",
    ]

    print(f"\n테스트 키워드: {len(test_keywords)}개")
    print("-" * 50)

    results = crawler.analyze_keywords(test_keywords)

    print("\n📊 쿠팡 상품 개수:")
    print("-" * 50)

    for keyword, count in results.items():
        print(f"{keyword:20s}: {count:>6}개")


if __name__ == '__main__':
    main()
