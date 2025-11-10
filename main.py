#!/usr/bin/env python3
# main.py
"""
쿠팡 블루오션 자동 발굴 시스템

카테고리만 입력하면 블루오션 키워드를 자동으로 찾아주는 도구

사용법:
    python main.py

작성자: Claude Code
버전: 1.0.0
"""

import sys
import time
from loguru import logger

import config
from modules.utils import (
    setup_logger,
    validate_category,
    calculate_elapsed_time
)
from modules.keyword_generator import KeywordGenerator
from modules.naver_search import NaverSearchAnalyzer
from modules.coupang_crawler import CoupangCrawler
from modules.analyzer import BlueOceanAnalyzer


def print_header():
    """헤더 출력"""
    print("\n" + "="*70)
    print("🎯 쿠팡 블루오션 자동 발굴 시스템")
    print("="*70)
    print("\n✨ 특징:")
    print("  • ⚡ 15분 만에 블루오션 발굴")
    print("  • 🤖 완전 자동화 (키워드 몰라도 됨)")
    print("  • 📊 데이터 기반 객관적 분석")
    print("  • 📁 엑셀 리포트 자동 생성")
    print("\n" + "="*70)


def get_category_input() -> str:
    """
    카테고리 입력 받기

    Returns:
        검증된 카테고리명
    """
    print("\n[1단계] 카테고리 입력")
    print("-"*70)

    while True:
        category = input("카테고리를 입력하세요 (예: 주방, 반려동물, 디지털): ").strip()

        if not category:
            print("❌ 카테고리를 입력해주세요.")
            continue

        if not validate_category(category):
            print("❌ 올바르지 않은 카테고리명입니다.")
            print("   (한글, 영문, 숫자, 공백, -, _, / 만 사용 가능)")
            continue

        # 확인
        print(f"\n✅ '{category}' 카테고리 선택됨")
        confirm = input("계속하시겠습니까? (y/n): ").strip().lower()

        if confirm in ['y', 'yes', '예', '']:
            return category
        else:
            print("다시 입력해주세요.\n")


def main():
    """메인 실행 함수"""
    # 로거 설정
    setup_logger()
    logger.info("쿠팡 블루오션 자동 발굴 시스템 시작")

    # 헤더 출력
    print_header()

    # 시작 시간
    start_time = time.time()

    try:
        # 1. 카테고리 입력
        category = get_category_input()
        logger.info(f"카테고리 선택: {category}")

        # 2. 키워드 생성
        print("\n" + "="*70)
        print("[2단계] 키워드 생성")
        print("="*70)

        generator = KeywordGenerator()
        keywords = generator.generate_keywords(
            category=category,
            target_count=config.TARGET_KEYWORD_COUNT
        )

        if not keywords:
            print("❌ 키워드 생성 실패")
            logger.error("키워드 생성 실패")
            return

        print(f"\n✅ 총 {len(keywords)}개 키워드 생성 완료")
        logger.info(f"키워드 생성 완료: {len(keywords)}개")

        # 3. 네이버 검색량 분석
        print("\n" + "="*70)
        print("[3단계] 네이버 검색량 분석")
        print("="*70)

        naver_analyzer = NaverSearchAnalyzer()
        search_volumes = naver_analyzer.analyze_keywords(keywords)

        print(f"\n✅ 검색량 분석 완료: {len(search_volumes)}개")
        logger.info(f"검색량 분석 완료: {len(search_volumes)}개")

        # 4. 쿠팡 상품 개수 확인
        print("\n" + "="*70)
        print("[4단계] 쿠팡 상품 개수 확인")
        print("="*70)

        coupang_crawler = CoupangCrawler()
        product_counts = coupang_crawler.analyze_keywords(keywords)

        print(f"\n✅ 상품 개수 확인 완료: {len(product_counts)}개")
        logger.info(f"쿠팡 크롤링 완료: {len(product_counts)}개")

        # 5. 블루오션 분석
        print("\n" + "="*70)
        print("[5단계] 블루오션 분석")
        print("="*70)
        print("\n🔄 분석 중...")

        analyzer = BlueOceanAnalyzer()
        results = analyzer.analyze(
            keywords=keywords,
            search_volumes=search_volumes,
            product_counts=product_counts
        )

        print("✅ 분석 완료!")

        # 6. 결과 출력
        analyzer.print_results(
            results=results,
            category=category,
            top_n=config.TOP_N_RESULTS
        )

        # 7. 엑셀 저장
        print("\n📁 엑셀 파일 저장 중...")
        excel_path = analyzer.export_to_excel(
            results=results,
            category=category
        )
        print(f"✅ 저장 완료: {excel_path}")

        # 8. 완료
        elapsed = calculate_elapsed_time(start_time)
        print(f"\n✨ 총 소요시간: {elapsed}")

        logger.info(f"분석 완료: {category}, 소요시간: {elapsed}")

        # 9. 재실행 여부
        print("\n" + "="*70)
        retry = input("다시 분석하시겠습니까? (y/n): ").strip().lower()

        if retry in ['y', 'yes', '예']:
            print("\n" * 2)
            main()  # 재귀 호출
        else:
            print("\n👋 프로그램을 종료합니다.")
            print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자가 중단했습니다.")
        logger.warning("사용자 중단")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        logger.error(f"실행 오류: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
