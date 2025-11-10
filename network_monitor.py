"""
네트워크 모니터링 모듈
쿠팡 API 엔드포인트 자동 발견 및 분석
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class NetworkMonitor:
    """
    Selenium WebDriver의 네트워크 요청을 모니터링하는 클래스
    Chrome DevTools Protocol (CDP)을 사용하여 API 엔드포인트를 자동으로 발견
    """

    def __init__(self, driver, enabled: bool = True):
        """
        Args:
            driver: Selenium WebDriver 인스턴스
            enabled: 모니터링 활성화 여부
        """
        self.driver = driver
        self.enabled = enabled
        self.requests = []
        self.script_injected = False

        if self.enabled:
            self.setup_monitoring()

    def setup_monitoring(self):
        """네트워크 모니터링 설정"""
        try:
            # CDP로 네트워크 활성화
            self.driver.execute_cdp_cmd('Network.enable', {})

            # JavaScript를 통한 XHR/Fetch 인터셉션 스크립트 주입
            self.inject_monitoring_script()

            print("   ✅ 네트워크 모니터링 활성화")
        except Exception as e:
            print(f"   ⚠️ 네트워크 모니터링 설정 실패: {e}")
            self.enabled = False

    def inject_monitoring_script(self):
        """XHR/Fetch 요청을 추적하는 JavaScript 주입"""
        try:
            script = """
            (function() {
                if (window.__networkMonitorInstalled) return;
                window.__networkMonitorInstalled = true;
                window.__networkRequests = [];

                // XMLHttpRequest 인터셉션
                const originalXHROpen = XMLHttpRequest.prototype.open;
                const originalXHRSend = XMLHttpRequest.prototype.send;

                XMLHttpRequest.prototype.open = function(method, url) {
                    this._networkMonitor = {
                        method: method,
                        url: url,
                        timestamp: new Date().toISOString()
                    };
                    return originalXHROpen.apply(this, arguments);
                };

                XMLHttpRequest.prototype.send = function() {
                    if (this._networkMonitor) {
                        const monitor = this._networkMonitor;
                        this.addEventListener('load', function() {
                            window.__networkRequests.push({
                                type: 'XHR',
                                method: monitor.method,
                                url: monitor.url,
                                status: this.status,
                                timestamp: monitor.timestamp
                            });
                        });
                    }
                    return originalXHRSend.apply(this, arguments);
                };

                // Fetch 인터셉션
                const originalFetch = window.fetch;
                window.fetch = function() {
                    const url = arguments[0];
                    const options = arguments[1] || {};
                    const method = options.method || 'GET';
                    const timestamp = new Date().toISOString();

                    return originalFetch.apply(this, arguments).then(response => {
                        window.__networkRequests.push({
                            type: 'Fetch',
                            method: method,
                            url: url,
                            status: response.status,
                            timestamp: timestamp
                        });
                        return response;
                    });
                };
            })();
            """

            self.driver.execute_script(script)
            self.script_injected = True

        except Exception as e:
            print(f"   ⚠️ 모니터링 스크립트 주입 실패: {e}")

    def ensure_script_injected(self):
        """스크립트가 주입되어 있는지 확인하고, 없으면 재주입"""
        try:
            is_installed = self.driver.execute_script("return window.__networkMonitorInstalled === true;")
            if not is_installed:
                print("   🔄 네트워크 모니터링 스크립트 재주입...")
                self.inject_monitoring_script()
        except Exception as e:
            print(f"   ⚠️ 스크립트 확인 실패: {e}")

    def collect_network_requests(self):
        """JavaScript에서 수집한 네트워크 요청 가져오기"""
        if not self.enabled:
            return

        try:
            # JavaScript에서 수집한 요청 가져오기
            js_requests = self.driver.execute_script("return window.__networkRequests || [];")

            if js_requests:
                self.requests.extend(js_requests)
                # 수집한 요청 초기화 (중복 방지)
                self.driver.execute_script("window.__networkRequests = [];")

                # API 요청 필터링 (쿠팡 API만)
                api_count = sum(1 for req in js_requests if self._is_api_request(req.get('url', '')))
                if api_count > 0:
                    print(f"   📡 API 요청 {api_count}개 수집 (총 {len(self.requests)}개)")

        except Exception as e:
            print(f"   ⚠️ 네트워크 요청 수집 실패: {e}")

    def _is_api_request(self, url: str) -> bool:
        """API 요청인지 판별"""
        api_patterns = [
            '/api/',
            '/graphql',
            '/v1/',
            '/v2/',
            'coupangcdn.com',
            'json',
            'ajax'
        ]

        url_lower = url.lower()
        return any(pattern in url_lower for pattern in api_patterns)

    def get_api_endpoints(self) -> List[Dict]:
        """수집된 API 엔드포인트 목록 반환"""
        api_requests = []

        for req in self.requests:
            url = req.get('url', '')
            if self._is_api_request(url):
                api_requests.append({
                    'method': req.get('method', 'UNKNOWN'),
                    'url': url,
                    'type': req.get('type', 'UNKNOWN'),
                    'status': req.get('status', 0),
                    'timestamp': req.get('timestamp', '')
                })

        return api_requests

    def stop_monitoring(self):
        """네트워크 모니터링 중지"""
        if self.enabled:
            try:
                self.driver.execute_cdp_cmd('Network.disable', {})
                print("   ⏹️ 네트워크 모니터링 중지")
            except:
                pass

    def save_logs(self, filename: Optional[str] = None) -> Optional[str]:
        """수집된 로그를 파일로 저장"""
        if not self.requests:
            print("   ℹ️ 저장할 네트워크 로그 없음")
            return None

        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"network_logs_{timestamp}.json"

            # logs 디렉토리 생성
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            filepath = log_dir / filename

            # JSON으로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_requests': len(self.requests),
                    'api_requests': len(self.get_api_endpoints()),
                    'collected_at': datetime.now().isoformat(),
                    'requests': self.requests
                }, f, ensure_ascii=False, indent=2)

            print(f"   💾 네트워크 로그 저장: {filepath}")
            return str(filepath)

        except Exception as e:
            print(f"   ⚠️ 로그 저장 실패: {e}")
            return None

    def generate_report(self) -> Dict:
        """API 엔드포인트 분석 리포트 생성"""
        api_requests = self.get_api_endpoints()

        # 엔드포인트별 통계
        endpoint_stats = {}
        for req in api_requests:
            url = req['url']
            # 쿼리 파라미터 제거 (엔드포인트 그룹핑)
            base_url = url.split('?')[0]

            if base_url not in endpoint_stats:
                endpoint_stats[base_url] = {
                    'count': 0,
                    'methods': set(),
                    'statuses': []
                }

            endpoint_stats[base_url]['count'] += 1
            endpoint_stats[base_url]['methods'].add(req['method'])
            endpoint_stats[base_url]['statuses'].append(req['status'])

        # Set을 리스트로 변환
        for stats in endpoint_stats.values():
            stats['methods'] = list(stats['methods'])

        report = {
            'total_requests': len(self.requests),
            'api_requests': len(api_requests),
            'unique_endpoints': len(endpoint_stats),
            'endpoints': endpoint_stats
        }

        return report


def setup_network_monitoring(driver, enabled: bool = True) -> Optional[NetworkMonitor]:
    """
    네트워크 모니터링 설정 헬퍼 함수

    Args:
        driver: Selenium WebDriver 인스턴스
        enabled: 모니터링 활성화 여부

    Returns:
        NetworkMonitor 인스턴스 또는 None
    """
    if not enabled:
        return None

    try:
        monitor = NetworkMonitor(driver, enabled=True)
        return monitor
    except Exception as e:
        print(f"⚠️ 네트워크 모니터링 초기화 실패: {e}")
        return None


def main():
    """테스트용 메인 함수"""
    print("NetworkMonitor 모듈 - 직접 실행 불가")
    print("Selenium WebDriver와 함께 사용하세요")
    print("\n사용 예시:")
    print("  from network_monitor import setup_network_monitoring")
    print("  monitor = setup_network_monitoring(driver, enabled=True)")
    print("  # ... 크롤링 작업 ...")
    print("  monitor.collect_network_requests()")
    print("  monitor.save_logs()")


if __name__ == '__main__':
    main()
