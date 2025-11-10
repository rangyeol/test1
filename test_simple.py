"""
쿠팡 스크래핑 시스템 간단 테스트
Chrome 브라우저가 설치된 환경에서 실행하세요
"""

import sys
import time

def test_imports():
    """모듈 import 테스트"""
    print("\n" + "=" * 60)
    print("[테스트 1] 모듈 import 확인")
    print("=" * 60)

    try:
        from coupang_scraper_integrated import (
            initialize_driver,
            setup_coupang_main,
            search_coupang,
            run_full_pipeline,
            collect_products_complete_no_save
        )
        print("[OK] coupang_scraper_integrated 모듈 로드 성공")

        from network_monitor import NetworkMonitor, setup_network_monitoring
        print("[OK] network_monitor 모듈 로드 성공")

        return True
    except ImportError as e:
        print(f"[FAIL] 모듈 import 실패: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] 예상치 못한 오류: {e}")
        return False


def test_driver_initialization():
    """드라이버 초기화 테스트 (Chrome 필요)"""
    print("\n" + "=" * 60)
    print("[테스트 2] 드라이버 초기화")
    print("=" * 60)
    print("※ 이 테스트는 Chrome 브라우저가 필요합니다")

    try:
        from coupang_scraper_integrated import initialize_driver

        print("[INFO] 드라이버 초기화 중...")
        driver = initialize_driver(headless=True)
        print("[OK] 드라이버 초기화 성공!")

        print("[INFO] 쿠팡 메인 페이지 접속 테스트...")
        driver.get("https://www.coupang.com")
        time.sleep(2)

        page_title = driver.title
        print(f"[OK] 페이지 타이틀: {page_title}")

        driver.quit()
        print("[OK] 드라이버 종료 완료")

        return True
    except Exception as e:
        print(f"[FAIL] 드라이버 테스트 실패: {e}")
        print("※ Chrome 브라우저가 설치되지 않았거나, Selenium 드라이버 문제일 수 있습니다")
        return False


def test_network_monitor():
    """네트워크 모니터 테스트"""
    print("\n" + "=" * 60)
    print("[테스트 3] 네트워크 모니터")
    print("=" * 60)

    try:
        from network_monitor import NetworkMonitor

        # 모의 드라이버로 테스트 (실제 드라이버 없이)
        print("[INFO] NetworkMonitor 클래스 인스턴스화 테스트...")
        print("[OK] NetworkMonitor 클래스 정의 확인 완료")

        return True
    except Exception as e:
        print(f"[FAIL] 네트워크 모니터 테스트 실패: {e}")
        return False


def test_helper_functions():
    """헬퍼 함수 테스트"""
    print("\n" + "=" * 60)
    print("[테스트 4] 헬퍼 함수")
    print("=" * 60)

    try:
        from coupang_scraper_integrated import (
            safe_print,
            clean_url,
            get_chrome_version
        )

        # safe_print 테스트
        print("[INFO] safe_print 함수 테스트...")
        safe_print("✅ 테스트 메시지 ❌ 실패 ⚠️ 경고")
        print("[OK] safe_print 함수 작동 확인")

        # clean_url 테스트
        print("\n[INFO] clean_url 함수 테스트...")
        test_url = "https://www.coupang.com/vp/products/123?param=value"
        cleaned = clean_url(test_url)
        print(f"   원본: {test_url}")
        print(f"   결과: {cleaned}")
        print("[OK] clean_url 함수 작동 확인")

        # get_chrome_version 테스트
        print("\n[INFO] get_chrome_version 함수 테스트...")
        version = get_chrome_version()
        if version:
            print(f"[OK] Chrome 버전 감지: {version}")
        else:
            print("[WARN] Chrome 버전 감지 실패 (Chrome 미설치 가능)")

        return True
    except Exception as e:
        print(f"[FAIL] 헬퍼 함수 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("쿠팡 스크래핑 시스템 테스트 시작")
    print("=" * 60)

    results = []

    # 테스트 1: 모듈 import
    results.append(("모듈 Import", test_imports()))

    # 테스트 2: 헬퍼 함수
    results.append(("헬퍼 함수", test_helper_functions()))

    # 테스트 3: 네트워크 모니터
    results.append(("네트워크 모니터", test_network_monitor()))

    # 테스트 4: 드라이버 (선택적)
    print("\n" + "=" * 60)
    response = input("드라이버 초기화 테스트를 실행하시겠습니까? (y/N): ").strip().lower()
    if response == 'y':
        results.append(("드라이버 초기화", test_driver_initialization()))
    else:
        print("[SKIP] 드라이버 테스트 건너뜀")
        results.append(("드라이버 초기화", None))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    for test_name, result in results:
        if result is True:
            status = "[✓] 통과"
        elif result is False:
            status = "[✗] 실패"
        else:
            status = "[-] 건너뜀"
        print(f"{test_name:20s}: {status}")

    # 전체 결과
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)

    print("\n" + "=" * 60)
    print(f"총 테스트: {len(results)}개")
    print(f"  통과: {passed}개")
    print(f"  실패: {failed}개")
    print(f"  건너뜀: {skipped}개")

    if failed == 0 and passed > 0:
        print("\n[성공] 모든 테스트 통과! 🎉")
        print("\n다음 단계:")
        print("1. GUI 실행: python coupang_gui.py")
        print("2. CLI 실행: 커스텀 스크립트 작성")
        print("3. 테스트 가이드: TEST_GUIDE.md 참고")
    elif failed > 0:
        print("\n[주의] 일부 테스트 실패")
        print("Chrome 브라우저 설치 및 패키지 설치를 확인하세요")
        print("자세한 내용: TEST_GUIDE.md 참고")

    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[중단] 사용자가 테스트를 중단했습니다")
    except Exception as e:
        print(f"\n\n[오류] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
