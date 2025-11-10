# modules/keyword_generator.py
"""
키워드 생성 엔진

FR-002: 키워드 자동 생성
- FR-002-1: Seed 키워드 생성
- FR-002-2: 네이버 연관검색어 크롤링
- FR-002-3: 자동완성 키워드 수집
- FR-002-4: 키워드 확장
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Set
from loguru import logger
from tqdm import tqdm
import time
import config
from modules.utils import (
    filter_stopwords,
    remove_duplicates,
    sanitize_keyword,
    wait_with_delay
)


class KeywordGenerator:
    """키워드 생성 엔진"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        })

    def generate_seeds(self, category: str) -> List[str]:
        """
        FR-002-1: Seed 키워드 생성

        Args:
            category: 카테고리명 (예: "주방")

        Returns:
            Seed 키워드 리스트 (5-10개)
        """
        logger.info(f"Seed 키워드 생성 시작: {category}")

        seeds = [category]

        # 기본 조합 패턴
        patterns = [
            f"{category}용품",
            f"{category}정리",
            f"{category}수납",
            f"{category}소품",
            f"{category}도구",
            f"{category}용",
            f"{category}꿀템",
        ]

        seeds.extend(patterns)

        # 중복 제거
        seeds = remove_duplicates(seeds)

        logger.info(f"Seed 키워드 {len(seeds)}개 생성 완료: {seeds[:5]}...")

        return seeds

    def get_naver_related_keywords(self, keyword: str) -> List[str]:
        """
        FR-002-2: 네이버 연관검색어 크롤링

        Args:
            keyword: 검색 키워드

        Returns:
            연관검색어 리스트
        """
        related_keywords = []

        try:
            # 네이버 쇼핑 검색
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

            if response.status_code != 200:
                logger.warning(f"네이버 검색 실패: {keyword} (status: {response.status_code})")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # 연관검색어 섹션 찾기
            # 여러 가능한 선택자 시도
            selectors = [
                '.related_search .keyword',
                '.relatedTags a',
                '[class*="related"] a',
                '.search_relation_keyword a',
            ]

            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for elem in elements:
                        text = elem.get_text(strip=True)
                        if text and len(text) < 50:  # 너무 긴 텍스트 제외
                            related_keywords.append(text)
                    break

            # 자동완성 키워드도 함께 수집
            autocomplete = self.get_autocomplete_keywords(keyword)
            related_keywords.extend(autocomplete)

            related_keywords = remove_duplicates(related_keywords)

            logger.debug(f"{keyword}: 연관검색어 {len(related_keywords)}개 수집")

        except Exception as e:
            logger.error(f"연관검색어 수집 실패 ({keyword}): {e}")

        return related_keywords

    def get_autocomplete_keywords(self, keyword: str) -> List[str]:
        """
        FR-002-3: 네이버 자동완성 키워드 수집

        Args:
            keyword: 검색 키워드

        Returns:
            자동완성 키워드 리스트
        """
        autocomplete_keywords = []

        try:
            params = {
                'q': keyword,
                'q_enc': 'UTF-8',
                'st': '100',
                'frm': 'nv.search',
                'r_format': 'json',
                'r_enc': 'UTF-8',
                'r_unicode': '0',
                't_koreng': '1',
                'ans': '2',
                'run': '2',
                'rev': '4',
                'con': '1',
            }

            response = self.session.get(
                config.NAVER_AUTOCOMPLETE_URL,
                params=params,
                timeout=config.REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                try:
                    data = response.json()

                    # 자동완성 결과 파싱
                    if 'items' in data and data['items']:
                        for item_group in data['items']:
                            if isinstance(item_group, list):
                                for item in item_group:
                                    if isinstance(item, list) and len(item) > 0:
                                        kw = item[0]
                                        if isinstance(kw, str) and kw.strip():
                                            autocomplete_keywords.append(kw.strip())

                except Exception as e:
                    logger.debug(f"자동완성 JSON 파싱 실패 ({keyword}): {e}")

        except Exception as e:
            logger.debug(f"자동완성 수집 실패 ({keyword}): {e}")

        return autocomplete_keywords

    def expand_keywords(
        self,
        seeds: List[str],
        max_depth: int = 2,
        max_total: int = 200
    ) -> List[str]:
        """
        FR-002-4: 키워드 확장

        Args:
            seeds: Seed 키워드 리스트
            max_depth: 최대 확장 깊이
            max_total: 최대 키워드 수

        Returns:
            확장된 키워드 리스트
        """
        logger.info(f"키워드 확장 시작 (depth: {max_depth}, max: {max_total})")

        all_keywords = set(seeds)
        current_level = seeds.copy()

        for depth in range(max_depth):
            logger.info(f"확장 레벨 {depth + 1}/{max_depth} 진행 중...")

            next_level = []

            # 진행바 표시
            for keyword in tqdm(current_level, desc=f"  레벨 {depth + 1} 키워드 수집", leave=False):
                # 최대 개수 도달 시 중단
                if len(all_keywords) >= max_total:
                    logger.info(f"목표 키워드 수 도달: {len(all_keywords)}개")
                    break

                # 연관검색어 수집
                related = self.get_naver_related_keywords(keyword)

                # 새로운 키워드만 추가
                for kw in related:
                    if kw not in all_keywords:
                        all_keywords.add(kw)
                        next_level.append(kw)

                        # 최대 개수 체크
                        if len(all_keywords) >= max_total:
                            break

                # 크롤링 딜레이
                wait_with_delay()

            # 다음 레벨이 없으면 중단
            if not next_level:
                logger.info(f"더 이상 확장할 키워드 없음 (레벨 {depth + 1})")
                break

            # 다음 레벨 준비 (일부만 선택)
            current_level = next_level[:min(10, len(next_level))]

            logger.info(f"레벨 {depth + 1} 완료: 총 {len(all_keywords)}개 키워드")

        logger.info(f"키워드 확장 완료: {len(all_keywords)}개")

        return list(all_keywords)

    def generate_keywords(
        self,
        category: str,
        target_count: int = None
    ) -> List[str]:
        """
        전체 키워드 생성 프로세스

        Args:
            category: 카테고리명
            target_count: 목표 키워드 수 (기본값: config.TARGET_KEYWORD_COUNT)

        Returns:
            최종 키워드 리스트
        """
        if target_count is None:
            target_count = config.TARGET_KEYWORD_COUNT

        logger.info(f"키워드 생성 시작: 카테고리='{category}', 목표={target_count}개")

        # 1. Seed 생성
        print("\n🔄 [1/4] Seed 키워드 생성 중...")
        seeds = self.generate_seeds(category)
        print(f"✅ Seed 키워드 {len(seeds)}개 생성 완료")

        # 2. 키워드 확장
        print(f"\n🔄 [2/4] 키워드 확장 중 (목표: {target_count}개)...")
        all_keywords = self.expand_keywords(
            seeds=seeds,
            max_depth=config.KEYWORD_EXPANSION_DEPTH,
            max_total=target_count
        )

        # 3. 정제 및 필터링
        print("\n🔄 [3/4] 키워드 정제 중...")

        # 3-1. 키워드 정제
        all_keywords = [sanitize_keyword(kw) for kw in all_keywords]

        # 3-2. 중복 제거
        all_keywords = remove_duplicates(all_keywords)

        # 3-3. 불용어 필터링
        before_count = len(all_keywords)
        all_keywords = filter_stopwords(all_keywords)
        removed_count = before_count - len(all_keywords)

        if removed_count > 0:
            logger.info(f"불용어 필터링: {removed_count}개 제거")

        # 3-4. 너무 짧거나 긴 키워드 제거
        all_keywords = [
            kw for kw in all_keywords
            if 2 <= len(kw) <= 30
        ]

        # 3-5. 정렬 (길이순 -> 가나다순)
        all_keywords.sort(key=lambda x: (len(x), x))

        print(f"✅ 정제 완료: {len(all_keywords)}개 키워드")

        # 4. 결과 반환
        logger.info(f"최종 키워드 {len(all_keywords)}개 생성 완료")
        logger.info(f"샘플: {all_keywords[:10]}")

        return all_keywords


def main():
    """테스트용 메인 함수"""
    from modules.utils import setup_logger

    setup_logger()

    print("="*50)
    print("🎯 키워드 생성 엔진 테스트")
    print("="*50)

    category = input("\n카테고리를 입력하세요: ").strip()

    if not category:
        print("❌ 카테고리를 입력해주세요")
        return

    generator = KeywordGenerator()
    keywords = generator.generate_keywords(category, target_count=50)

    print("\n" + "="*50)
    print(f"📊 생성된 키워드: {len(keywords)}개")
    print("="*50)

    for i, kw in enumerate(keywords[:20], 1):
        print(f"{i:2d}. {kw}")

    if len(keywords) > 20:
        print(f"\n... 외 {len(keywords) - 20}개")


if __name__ == '__main__':
    main()
