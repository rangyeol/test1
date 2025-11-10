#!/usr/bin/env python3
"""
전체 모듈 테스트 스크립트
"""

import sys


def test_imports():
    """모든 모듈 import 테스트"""
    print("\n" + "="*60)
    print("[ 테스트 1 ] 모듈 Import 확인")
    print("="*60)

    modules_to_test = [
        ("config", "설정 파일"),
        ("modules.utils", "유틸리티"),
        ("modules.naver_search", "네이버 검색량"),
        ("modules.keyword_generator", "키워드 생성"),
        ("modules.coupang_crawler", "쿠팡 크롤러"),
        ("modules.analyzer", "블루오션 분석"),
    ]

    results = []

    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✅ {description:15s} ({module_name})")
            results.append(True)
        except ImportError as e:
            print(f"  ❌ {description:15s} ({module_name}): {e}")
            results.append(False)
        except Exception as e:
            print(f"  ⚠️  {description:15s} ({module_name}): {e}")
            results.append(False)

    success_rate = sum(results) / len(results) * 100
    print(f"\n결과: {sum(results)}/{len(results)} 성공 ({success_rate:.0f}%)")

    return all(results)


def test_config():
    """설정 파일 테스트"""
    print("\n" + "="*60)
    print("[ 테스트 2 ] 설정 파일 확인")
    print("="*60)

    try:
        import config

        checks = [
            ("MIN_SEARCH_VOLUME", config.MIN_SEARCH_VOLUME),
            ("MAX_SEARCH_VOLUME", config.MAX_SEARCH_VOLUME),
            ("NAVER_SHOPPING_URL", config.NAVER_SHOPPING_URL),
            ("COUPANG_SEARCH_URL", config.COUPANG_SEARCH_URL),
            ("USER_AGENT", config.USER_AGENT[:50] + "..."),
        ]

        for key, value in checks:
            print(f"  ✅ {key:25s}: {value}")

        return True

    except Exception as e:
        print(f"  ❌ 설정 파일 오류: {e}")
        return False


def test_naver_search():
    """네이버 검색량 분석 테스트"""
    print("\n" + "="*60)
    print("[ 테스트 3 ] 네이버 검색량 분석")
    print("="*60)

    try:
        from modules.naver_search import NaverSearchAnalyzer

        analyzer = NaverSearchAnalyzer()

        # API 사용 가능 여부
        if analyzer.api_available:
            print("  ✅ 네이버 API 사용 가능")
        else:
            print("  ⚠️  네이버 API 미설정 (대안 방법 사용)")

        # 단일 키워드 테스트
        test_keyword = "테스트"
        print(f"\n  테스트 키워드: '{test_keyword}'")

        volume = analyzer.get_search_volume(test_keyword)
        print(f"  검색량: {volume:,}회/월")

        if volume > 0:
            print(f"  ✅ 검색량 조회 성공")
            return True
        else:
            print(f"  ❌ 검색량 조회 실패")
            return False

    except Exception as e:
        print(f"  ❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_keyword_generator():
    """키워드 생성 테스트"""
    print("\n" + "="*60)
    print("[ 테스트 4 ] 키워드 생성기")
    print("="*60)

    try:
        from modules.keyword_generator import KeywordGenerator

        generator = KeywordGenerator()
        print("  ✅ KeywordGenerator 인스턴스 생성 성공")

        # 간단한 키워드 생성 테스트 (실제 API 호출 없이)
        print("  ℹ️  실제 키워드 생성은 네트워크 필요 (스킵)")

        return True

    except Exception as e:
        print(f"  ❌ 테스트 실패: {e}")
        return False


def test_coupang_crawler():
    """쿠팡 크롤러 테스트"""
    print("\n" + "="*60)
    print("[ 테스트 5 ] 쿠팡 크롤러")
    print("="*60)

    try:
        from modules.coupang_crawler import CoupangCrawler

        crawler = CoupangCrawler()
        print("  ✅ CoupangCrawler 인스턴스 생성 성공")

        print("  ℹ️  실제 크롤링은 네트워크 필요 (스킵)")

        return True

    except Exception as e:
        print(f"  ❌ 테스트 실패: {e}")
        return False


def test_analyzer():
    """블루오션 분석기 테스트"""
    print("\n" + "="*60)
    print("[ 테스트 6 ] 블루오션 분석기")
    print("="*60)

    try:
        from modules.analyzer import BlueOceanAnalyzer

        analyzer = BlueOceanAnalyzer()
        print("  ✅ BlueOceanAnalyzer 인스턴스 생성 성공")

        # 샘플 데이터로 분석 테스트
        sample_keywords = ["키워드1", "키워드2", "키워드3"]
        sample_volumes = {"키워드1": 10000, "키워드2": 5000, "키워드3": 15000}
        sample_counts = {"키워드1": 100, "키워드2": 50, "키워드3": 200}

        results = analyzer.analyze(
            keywords=sample_keywords,
            search_volumes=sample_volumes,
            product_counts=sample_counts
        )

        if results and len(results) > 0:
            print(f"  ✅ 분석 성공: {len(results)}개 결과")
            print(f"\n  샘플 결과:")
            for i, result in enumerate(results[:3], 1):
                print(f"    {i}. {result['keyword']:10s} - 점수: {result['score']:.1f}")
            return True
        else:
            print("  ❌ 분석 결과 없음")
            return False

    except Exception as e:
        print(f"  ❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_file():
    """환경 파일 확인"""
    print("\n" + "="*60)
    print("[ 테스트 7 ] 환경 파일 확인")
    print("="*60)

    import os
    from pathlib import Path

    env_file = Path(".env")
    env_template = Path(".env.template")

    if env_file.exists():
        print(f"  ✅ .env 파일 존재")

        # API 키 확인
        from dotenv import load_dotenv
        load_dotenv()

        client_id = os.getenv('NAVER_CLIENT_ID', '')
        client_secret = os.getenv('NAVER_CLIENT_SECRET', '')

        if client_id and client_id != 'your_client_id_here':
            print(f"  ✅ NAVER_CLIENT_ID 설정됨")
        else:
            print(f"  ⚠️  NAVER_CLIENT_ID 미설정 (대안 방법 사용)")

        if client_secret and client_secret != 'your_client_secret_here':
            print(f"  ✅ NAVER_CLIENT_SECRET 설정됨")
        else:
            print(f"  ⚠️  NAVER_CLIENT_SECRET 미설정 (대안 방법 사용)")

        return True
    else:
        print(f"  ⚠️  .env 파일 없음")
        if env_template.exists():
            print(f"  ℹ️  .env.template 파일 발견")
            print(f"  💡 실행: cp .env.template .env")
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("🧪 쿠팡 블루오션 시스템 - 전체 모듈 테스트")
    print("="*60)

    # 모든 테스트 실행
    tests = [
        ("Import 테스트", test_imports),
        ("설정 파일", test_config),
        ("환경 파일", test_env_file),
        ("네이버 검색량", test_naver_search),
        ("키워드 생성", test_keyword_generator),
        ("쿠팡 크롤러", test_coupang_crawler),
        ("블루오션 분석", test_analyzer),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n  ❌ {test_name} 실패: {e}")
            results.append((test_name, False))

    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)

    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {status:10s} - {test_name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    success_rate = passed / total * 100 if total > 0 else 0

    print("\n" + "="*60)
    print(f"총 {total}개 테스트 중 {passed}개 통과 ({success_rate:.0f}%)")
    print("="*60)

    if passed == total:
        print("\n✨ 모든 테스트 통과! 시스템 정상 작동")
        print("\n다음 단계:")
        print("  1. 전체 시스템 실행: python main.py")
        print("  2. 쿠팡 스크래퍼 GUI: python coupang_gui.py")
        print("  3. 네이버 API 설정: .env 파일 편집")
    elif passed >= total * 0.7:
        print("\n⚠️  대부분의 테스트 통과 (일부 기능 제한)")
        print("  네트워크 연결 또는 API 키 설정 확인")
    else:
        print("\n❌ 여러 테스트 실패")
        print("  패키지 설치 및 환경 설정 확인 필요")

    print("\n자세한 내용:")
    print("  - 블루오션 시스템: TEST_BLUEOCEAN.md")
    print("  - 쿠팡 스크래퍼: TEST_GUIDE.md, QUICK_START.md")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  테스트 중단됨")
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
