"""
쿠팡 스크래퍼 GUI
ttkthemes를 사용한 깔끔한 인터페이스
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from ttkthemes import ThemedTk
import threading
import queue
from datetime import datetime
import sys
import os
import time
import random

# coupang_scraper_integrated 모듈 임포트
try:
    import coupang_scraper_integrated as scraper
except ImportError:
    messagebox.showerror("오류", "coupang_scraper_integrated.py 파일을 찾을 수 없습니다.\n같은 폴더에 파일이 있는지 확인해주세요.")
    sys.exit(1)


class TextRedirector:
    """stdout/stderr를 GUI 로그로 리다이렉트"""
    def __init__(self, log_callback, log_text_widget):
        self.log_callback = log_callback
        self.log_text_widget = log_text_widget
        self.current_line = ""

    def write(self, text):
        if not text:
            return

        # \r이 포함된 경우 (진행률 표시)
        if '\r' in text:
            parts = text.split('\r')
            text = parts[-1]

            if text.strip():
                self.current_line = text.rstrip()
                try:
                    self.log_text_widget.delete("end-2l", "end-1l")
                except:
                    pass
                self.log_callback(self.current_line, "info")
        else:
            if text.strip():
                self.current_line = ""
                self.log_callback(text.rstrip(), "info")

    def flush(self):
        pass


class CoupangScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("쿠팡 상품 수집기")
        self.root.geometry("750x750")
        self.root.resizable(False, False)

        # 변수 초기화
        self.search_list = []
        self.is_running = False
        self.stop_event = threading.Event()
        self.driver = None
        self.active_drivers = []
        self.log_queue = queue.Queue()
        self.error_occurred = False

        # stdout/stderr 리다이렉트 설정
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.redirector = None

        # GUI 구성
        self.setup_ui()

        # TextRedirector 초기화
        self.redirector = TextRedirector(self.log, self.log_text)

        # 로그 업데이트 스케줄링
        self.update_log()

        # 네트워크 모니터링 정보 업데이트 스케줄링
        self.update_network_info()

    def setup_ui(self):
        """GUI 구성"""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # ==================== 입력 섹션 ====================
        input_frame = ttk.LabelFrame(main_frame, text="검색어/URL 입력", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="검색어 또는 URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_input = ttk.Entry(input_frame, width=60)
        self.search_input.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.search_input.bind('<Return>', lambda e: self.add_search())

        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=0, column=2, padx=5)

        self.add_btn = ttk.Button(btn_frame, text="추가", command=self.add_search, width=8)
        self.add_btn.pack(side=tk.LEFT, padx=2)

        self.remove_btn = ttk.Button(btn_frame, text="제거", command=self.remove_search, width=8)
        self.remove_btn.pack(side=tk.LEFT, padx=2)

        ttk.Label(input_frame, text="수집 목록:").grid(row=1, column=0, sticky=tk.W, pady=(10, 5))

        list_frame = ttk.Frame(input_frame)
        list_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.search_listbox = tk.Listbox(list_frame, height=6, selectmode=tk.SINGLE,
                                         bg='white', fg='#2c3e50', font=('맑은 고딕', 9))
        self.search_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.search_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_listbox.config(yscrollcommand=scrollbar.set)

        # ==================== 설정 섹션 ====================
        settings_frame = ttk.LabelFrame(main_frame, text="수집 설정", padding="10")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        settings_frame.columnconfigure(0, weight=1)

        settings_inner = ttk.Frame(settings_frame)
        settings_inner.grid(row=0, column=0, sticky=(tk.W, tk.E))

        for i in range(6):
            settings_inner.columnconfigure(i, weight=1)

        # 수집 페이지 수
        page_frame = ttk.Frame(settings_inner)
        page_frame.grid(row=0, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(page_frame, text="수집 페이지 수:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.max_pages_var = tk.IntVar(value=50)
        max_pages_spin = ttk.Spinbox(page_frame, from_=1, to=100, textvariable=self.max_pages_var,
                                     width=12)
        max_pages_spin.grid(row=0, column=1, sticky=tk.W)

        # 병렬처리 개수
        parallel_frame = ttk.Frame(settings_inner)
        parallel_frame.grid(row=0, column=1, padx=10, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(parallel_frame, text="동시 수집 개수:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.parallel_var = tk.IntVar(value=1)
        parallel_spin = ttk.Spinbox(parallel_frame, from_=1, to=5, textvariable=self.parallel_var,
                                    width=12)
        parallel_spin.grid(row=0, column=1, sticky=tk.W)

        # 헤드리스 모드
        headless_frame = ttk.Frame(settings_inner)
        headless_frame.grid(row=0, column=2, padx=10, pady=5, sticky=(tk.W, tk.E))

        self.headless_var = tk.BooleanVar(value=False)
        headless_check = ttk.Checkbutton(headless_frame, text="헤드리스 모드",
                                         variable=self.headless_var)
        headless_check.grid(row=0, column=0, sticky=tk.W)

        # 이미지 다운로드 옵션
        download_img_frame = ttk.Frame(settings_inner)
        download_img_frame.grid(row=0, column=3, padx=10, pady=5, sticky=(tk.W, tk.E))

        self.download_images_var = tk.BooleanVar(value=False)
        download_img_check = ttk.Checkbutton(download_img_frame, text="이미지 다운로드",
                                            variable=self.download_images_var)
        download_img_check.grid(row=0, column=0, sticky=tk.W)

        # 이어하기 모드
        resume_frame = ttk.Frame(settings_inner)
        resume_frame.grid(row=0, column=4, padx=10, pady=5, sticky=(tk.W, tk.E))

        self.resume_var = tk.BooleanVar(value=True)
        resume_check = ttk.Checkbutton(resume_frame, text="이어하기 모드",
                                       variable=self.resume_var)
        resume_check.grid(row=0, column=0, sticky=tk.W)

        # 네트워크 모니터링 옵션
        monitor_frame = ttk.Frame(settings_inner)
        monitor_frame.grid(row=0, column=5, padx=10, pady=5, sticky=(tk.W, tk.E))

        self.network_monitor_var = tk.BooleanVar(value=False)
        monitor_check = ttk.Checkbutton(monitor_frame, text="네트워크 모니터링",
                                        variable=self.network_monitor_var)
        monitor_check.grid(row=0, column=0, sticky=tk.W)

        # 설명 텍스트
        ttk.Label(settings_inner, text="※ 동시 수집 개수: 리스트의 여러 검색어를 동시에 처리 (권장: 1-2개)",
                 foreground='#7f8c8d', font=('맑은 고딕', 8)).grid(
            row=1, column=0, columnspan=2, pady=(10, 0), padx=10, sticky=tk.W)
        ttk.Label(settings_inner, text="※ 이미지 다운로드: 상품 이미지를 로컬에 저장 (용량 주의)",
                 foreground='#7f8c8d', font=('맑은 고딕', 8)).grid(
            row=1, column=2, columnspan=2, pady=(10, 0), padx=10, sticky=tk.W)
        ttk.Label(settings_inner, text="※ 이어하기 모드: 프로그램 중단 시 마지막 저장 시점부터 다시 시작",
                 foreground='#7f8c8d', font=('맑은 고딕', 8)).grid(
            row=2, column=0, columnspan=3, pady=(5, 0), padx=10, sticky=tk.W)
        ttk.Label(settings_inner, text="※ 네트워크 모니터링: API 요청을 자동 캡처하여 분석 (로그 파일 저장)",
                 foreground='#7f8c8d', font=('맑은 고딕', 8)).grid(
            row=2, column=3, columnspan=3, pady=(5, 0), padx=10, sticky=tk.W)

        # ==================== 제어 버튼 ====================
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=0)
        control_frame.columnconfigure(2, weight=0)
        control_frame.columnconfigure(3, weight=0)
        control_frame.columnconfigure(4, weight=1)

        self.start_btn = ttk.Button(control_frame, text="수집 시작", command=self.start_collection,
                                    width=20)
        self.start_btn.grid(row=0, column=1, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="중지", command=self.stop_collection,
                                   width=20, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=5)

        self.clear_btn = ttk.Button(control_frame, text="로그 지우기", command=self.clear_log,
                                    width=20)
        self.clear_btn.grid(row=0, column=3, padx=5)

        # ==================== 진행 상황 ====================
        progress_frame = ttk.LabelFrame(main_frame, text="진행 상황", padding="10")
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.progress_label = ttk.Label(progress_frame, text="대기 중...",
                                       foreground='#7f8c8d', font=('맑은 고딕', 9))
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))

        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.network_info_label = ttk.Label(progress_frame, text="",
                                           foreground='#3498db', font=('맑은 고딕', 8))
        self.network_info_label.pack(anchor=tk.W, pady=(5, 0))

        # ==================== 로그 ====================
        log_frame = ttk.LabelFrame(main_frame, text="실행 로그", padding="10")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=100,
                                                  bg='#f8f9fa', fg='#2c3e50',
                                                  font=('맑은 고딕', 9), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 로그 태그 설정
        self.log_text.tag_config("info", foreground="#2c3e50")
        self.log_text.tag_config("success", foreground="#27ae60")
        self.log_text.tag_config("warning", foreground="#f39c12")
        self.log_text.tag_config("error", foreground="#e74c3c")

        # 초기 메시지
        self.log("프로그램이 시작되었습니다.", "info")
        self.log("검색어 또는 URL을 입력하고 '추가' 버튼을 클릭하세요.", "info")

    def log(self, message, level="info"):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_queue.put((formatted_message, level))

    def update_log(self):
        """로그 업데이트 (큐에서 읽기)"""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message, level)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass

        self.root.after(100, self.update_log)

    def update_network_info(self):
        """네트워크 모니터링 실시간 정보 업데이트"""
        try:
            if hasattr(self, 'network_monitor') and self.network_monitor and self.is_running:
                try:
                    request_count = len(self.network_monitor.requests)
                    api_endpoints = self.network_monitor.get_api_endpoints()
                    api_count = len(api_endpoints)

                    info_text = f"네트워크 요청: {request_count}개 | API 엔드포인트: {api_count}개"
                    self.network_info_label.config(text=info_text)
                except:
                    self.network_info_label.config(text="")
            else:
                self.network_info_label.config(text="")
        except:
            pass

        self.root.after(2000, self.update_network_info)

    def clear_log(self):
        """로그 지우기"""
        self.log_text.delete(1.0, tk.END)
        self.log("로그가 지워졌습니다.", "info")

    def add_search(self):
        """검색어/URL 추가"""
        search_value = self.search_input.get().strip()

        if not search_value:
            messagebox.showwarning("경고", "검색어 또는 URL을 입력하세요.")
            return

        if search_value in self.search_list:
            messagebox.showwarning("경고", "이미 추가된 항목입니다.")
            return

        self.search_list.append(search_value)
        self.search_listbox.insert(tk.END, search_value)
        self.search_input.delete(0, tk.END)

        self.log(f"항목 추가됨: {search_value}", "success")

    def remove_search(self):
        """선택된 검색어/URL 제거"""
        selection = self.search_listbox.curselection()

        if not selection:
            messagebox.showwarning("경고", "제거할 항목을 선택하세요.")
            return

        index = selection[0]
        removed_item = self.search_list[index]

        del self.search_list[index]
        self.search_listbox.delete(index)

        self.log(f"항목 제거됨: {removed_item}", "warning")

    def start_collection(self):
        """수집 시작"""
        if not self.search_list:
            messagebox.showwarning("경고", "수집할 항목을 추가하세요.")
            return

        if self.is_running:
            messagebox.showwarning("경고", "이미 수집이 진행 중입니다.")
            return

        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.add_btn.config(state=tk.DISABLED)
        self.remove_btn.config(state=tk.DISABLED)
        self.progress_bar.start(10)

        max_pages = self.max_pages_var.get()
        parallel_count = self.parallel_var.get()
        headless = self.headless_var.get()
        download_images = self.download_images_var.get()
        network_monitoring = self.network_monitor_var.get()

        self.log("="*50, "info")
        self.log(f"수집 시작 - 항목: {len(self.search_list)}개, 페이지: {max_pages}개", "success")
        self.log(f"동시 수집: {parallel_count}개", "info")
        self.log(f"헤드리스 모드: {'활성화' if headless else '비활성화'}", "info")
        self.log(f"이미지 다운로드: {'활성화' if download_images else '비활성화'}", "info")
        self.log(f"네트워크 모니터링: {'활성화' if network_monitoring else '비활성화'}", "info")
        self.log("="*50, "info")

        thread = threading.Thread(target=self.run_collection,
                                 args=(max_pages, parallel_count, headless, download_images, network_monitoring),
                                 daemon=True)
        thread.start()

    def run_collection(self, max_pages, parallel_count, headless, download_images, network_monitoring=False):
        """실제 수집 실행 (백그라운드)"""
        drivers = []
        network_monitor = None

        self.stop_event.clear()
        self.error_occurred = False

        # stdout을 GUI 로그로 리다이렉트
        sys.stdout = self.redirector
        sys.stderr = self.redirector

        try:
            total_items = len(self.search_list)

            if parallel_count == 1:
                self.log("순차 처리 모드로 실행합니다.", "info")

                if self.stop_event.is_set():
                    self.log("중지 요청됨 - 초기화 중단", "warning")
                    return

                self.log("브라우저 초기화 중...", "info")
                self.progress_label.config(text="브라우저 초기화 중...")

                try:
                    self.driver = scraper.initialize_driver(headless=headless)
                    if not self.driver:
                        raise Exception("드라이버 초기화 실패")

                    try:
                        _ = self.driver.current_url
                    except Exception as check_error:
                        error_msg = str(check_error)
                        if "no such window" in error_msg.lower() or "target window already closed" in error_msg.lower():
                            self.log("브라우저 창이 닫혔습니다. 재초기화 시도...", "warning")
                            try:
                                scraper.close_browser(self.driver)
                            except:
                                pass
                            self.driver = scraper.initialize_driver(headless=headless)
                            if not self.driver:
                                raise Exception("드라이버 재초기화 실패")
                        else:
                            raise Exception(f"드라이버 상태 확인 실패: {check_error}")

                    try:
                        self.driver = scraper.setup_coupang_main(self.driver, is_parallel=False)
                    except Exception as setup_error:
                        error_msg = str(setup_error)
                        if "no such window" in error_msg.lower() or "target window already closed" in error_msg.lower():
                            self.log("브라우저가 닫혔습니다. 재초기화 시도...", "warning")
                            try:
                                scraper.close_browser(self.driver)
                            except:
                                pass
                            self.driver = scraper.initialize_driver(headless=headless)
                            if not self.driver:
                                raise Exception("드라이버 재초기화 실패")
                            self.driver = scraper.setup_coupang_main(self.driver, is_parallel=False)
                        else:
                            raise

                    drivers.append(self.driver)

                    try:
                        current_url = self.driver.current_url
                        self.log(f"현재 페이지: {current_url}", "info")
                    except Exception as url_error:
                        error_msg = str(url_error)
                        if "no such window" in error_msg.lower() or "target window already closed" in error_msg.lower():
                            raise Exception("브라우저가 닫혔습니다. 재초기화가 필요합니다.")
                        else:
                            self.log(f"페이지 접속 확인 실패 (계속 진행): {url_error}", "warning")

                    self.log("브라우저 초기화 완료!", "success")

                    # 네트워크 모니터링 설정
                    if network_monitoring:
                        try:
                            from network_monitor import setup_network_monitoring
                            network_monitor = setup_network_monitoring(self.driver, enabled=True)
                            if network_monitor:
                                self.log("네트워크 모니터링이 활성화되었습니다.", "info")
                                self.network_monitor = network_monitor
                            else:
                                self.network_monitor = None
                        except Exception as e:
                            self.log(f"네트워크 모니터링 설정 실패: {e}", "warning")
                            self.network_monitor = None
                    else:
                        self.network_monitor = None
                except Exception as e:
                    self.log(f"브라우저 초기화 실패: {str(e)}", "error")
                    import traceback
                    self.log(f"상세 오류:\n{traceback.format_exc()}", "error")

                    if self.driver:
                        try:
                            scraper.close_browser(self.driver)
                        except:
                            pass
                        self.driver = None

                    return

                # 순차 처리
                for idx, search_value in enumerate(self.search_list, 1):
                    if not self.is_running or self.stop_event.is_set():
                        self.log("사용자에 의해 중지되었습니다.", "warning")
                        break

                    self.progress_label.config(text=f"수집 중... ({idx}/{total_items})")
                    self.log(f"\n[{idx}/{total_items}] 처리 시작: {search_value}", "info")

                    try:
                        resume = self.resume_var.get()
                        network_monitor = getattr(self, 'network_monitor', None)
                        result = scraper.run_full_pipeline(self.driver, search_value, max_pages,
                                                          resume=resume, stop_event=self.stop_event,
                                                          is_parallel=False, download_images=download_images,
                                                          network_monitor=network_monitor)

                        if result is not None:
                            self.log(f"[{idx}/{total_items}] 완료! 수집된 상품: {len(result)}개", "success")
                        else:
                            self.log(f"[{idx}/{total_items}] 실패", "error")

                    except Exception as e:
                        self.log(f"[{idx}/{total_items}] 오류 발생: {str(e)}", "error")
                        if self.stop_event.is_set():
                            break

            self.log("\n" + "="*50, "info")
            self.log("모든 작업이 완료되었습니다!", "success")
            self.log("="*50, "info")

        except Exception as e:
            self.log(f"심각한 오류 발생: {str(e)}", "error")
            import traceback
            self.log(f"상세 오류:\n{traceback.format_exc()}", "error")

            self.error_occurred = True

        finally:
            # 네트워크 모니터링 종료
            monitor_to_save = network_monitor if 'network_monitor' in locals() else getattr(self, 'network_monitor', None)
            if monitor_to_save:
                try:
                    monitor_to_save.collect_network_requests()
                    monitor_to_save.stop_monitoring()
                    log_file = monitor_to_save.save_logs()
                    if log_file:
                        self.log(f"네트워크 로그 저장 완료: {log_file}", "info")
                    report = monitor_to_save.generate_report()
                    self.log("API 엔드포인트 분석 리포트 생성 완료", "info")
                except Exception as e:
                    self.log(f"네트워크 모니터링 종료 실패: {e}", "warning")

            # stdout/stderr 복원
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr

            # 모든 드라이버 종료
            for driver in drivers:
                try:
                    scraper.close_browser(driver)
                except:
                    pass

            if self.driver:
                try:
                    scraper.close_browser(self.driver)
                except:
                    pass

            self.log("모든 브라우저가 종료되었습니다.", "info")

            # UI 상태 복원
            self.is_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.add_btn.config(state=tk.NORMAL)
            self.remove_btn.config(state=tk.NORMAL)
            self.progress_bar.stop()
            self.progress_label.config(text="대기 중...")
            self.network_info_label.config(text="")

            if self.error_occurred:
                self.log("작업 중 오류가 발생했습니다. 로그를 확인하세요.", "error")
            elif not self.stop_event.is_set():
                self.log("모든 작업이 완료되었습니다!", "success")

    def stop_collection(self):
        """수집 즉시 중지"""
        if not self.is_running:
            return

        if messagebox.askyesno("확인", "정말 중지하시겠습니까?\n모든 브라우저가 즉시 닫히고 진행 중인 데이터는 자동 저장됩니다."):
            self.log("="*50, "warning")
            self.log("즉시 중지 요청 - 모든 작업 중단 중...", "warning")
            self.log("="*50, "warning")

            self.is_running = False
            self.stop_event.set()

            self.log(f"브라우저 종료 중... (총 {len(self.active_drivers) + (1 if self.driver else 0)}개)", "warning")

            if self.driver:
                try:
                    scraper.close_browser(self.driver)
                    self.log("메인 브라우저 종료 완료", "info")
                except Exception as e:
                    self.log(f"메인 브라우저 종료 실패: {e}", "error")
                finally:
                    self.driver = None

            for i, driver in enumerate(self.active_drivers, 1):
                try:
                    scraper.close_browser(driver)
                    self.log(f"병렬 브라우저 {i} 종료 완료", "info")
                except Exception as e:
                    self.log(f"병렬 브라우저 {i} 종료 실패: {e}", "error")

            self.active_drivers.clear()
            self.log("모든 브라우저 종료 완료", "success")
            self.log("진행 중인 데이터는 자동 저장되었습니다", "info")


def main():
    """메인 실행"""
    root = ThemedTk(theme="arc")

    default_font = ('맑은 고딕', 9)
    root.option_add("*Font", default_font)

    app = CoupangScraperGUI(root)

    def on_closing():
        if app.is_running:
            if messagebox.askyesno("확인", "수집이 진행 중입니다.\n종료하시겠습니까?"):
                app.is_running = False
                if app.driver:
                    try:
                        scraper.close_browser(app.driver)
                    except:
                        pass
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()


if __name__ == "__main__":
    main()
