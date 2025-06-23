"""
web_search_ide.py - 웹 검색 + 사이트 접속 기능이 포함된 고급 클라우드 IDE
최신 기술 정보 검색, 코드 예제 확인, 실시간 테스트까지 가능한 완전한 개발 환경
"""

import os
import re
import json
import requests
import subprocess
import tempfile
import time
import base64
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Selenium 관련 import
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from src.user_auth_manager import user_auth_manager
from src.user_drive_manager import user_drive_manager
from googleapiclient.discovery import build

class AdvancedWebAutomation:
    """Selenium WebDriver를 활용한 고급 웹 자동화 시스템"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.default_timeout = 10
        self.page_load_timeout = 30
        self.implicit_wait = 5
        
    def _setup_driver(self, headless: bool = True, window_size: Tuple[int, int] = (1920, 1080)) -> bool:
        """ChromeDriver 설정 및 초기화"""
        try:
            # Chrome 옵션 설정
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument('--headless')
            
            # 기본 옵션들
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
            
            # User-Agent 설정
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # ChromeDriver 자동 설치 및 서비스 설정
            service = Service(ChromeDriverManager().install())
            
            # WebDriver 초기화
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.page_load_timeout)
            self.driver.implicitly_wait(self.implicit_wait)
            
            # WebDriverWait 초기화
            self.wait = WebDriverWait(self.driver, self.default_timeout)
            
            return True
            
        except Exception as e:
            print(f"WebDriver 설정 실패: {str(e)}")
            return False
    
    def navigate_to_url(self, url: str, wait_for_element: str = None) -> Dict:
        """URL로 이동하고 페이지 로딩 완료 대기"""
        try:
            if not self.driver:
                if not self._setup_driver():
                    return {"success": False, "error": "WebDriver 초기화 실패"}
            
            # URL로 이동
            self.driver.get(url)
            
            # 특정 요소 대기 (선택사항)
            if wait_for_element:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element)))
                except TimeoutException:
                    pass  # 요소를 찾지 못해도 계속 진행
            
            # JavaScript 실행 완료 대기
            self.wait_for_page_load()
            
            return {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title,
                "page_source_length": len(self.driver.page_source)
            }
            
        except Exception as e:
            return {"success": False, "error": f"페이지 이동 실패: {str(e)}"}
    
    def wait_for_page_load(self, max_wait: int = 10) -> bool:
        """JavaScript 실행 완료까지 대기"""
        try:
            # document.readyState가 'complete'가 될 때까지 대기
            WebDriverWait(self.driver, max_wait).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # jQuery가 있다면 jQuery 완료도 대기
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda driver: driver.execute_script("return typeof jQuery === 'undefined' || jQuery.active === 0")
                )
            except:
                pass  # jQuery가 없는 경우 무시
            
            # 추가 안정화 대기
            time.sleep(0.5)
            return True
            
        except TimeoutException:
            return False
    
    def take_screenshot(self, filename: str = None) -> Dict:
        """스크린샷 캡처"""
        try:
            if not self.driver:
                return {"success": False, "error": "WebDriver가 초기화되지 않음"}
            
            if filename is None:
                filename = f"screenshot_{int(time.time())}.png"
            
            # 전체 페이지 스크린샷
            screenshot_data = self.driver.get_screenshot_as_png()
            
            # Base64 인코딩
            screenshot_base64 = base64.b64encode(screenshot_data).decode('utf-8')
            
            return {
                "success": True,
                "filename": filename,
                "data": screenshot_base64,
                "size": len(screenshot_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": f"스크린샷 캡처 실패: {str(e)}"}
    
    def interact_with_element(self, selector: str, action: str, value: str = None) -> Dict:
        """웹 요소와 상호작용 (클릭, 입력, 스크롤 등)"""
        try:
            if not self.driver:
                return {"success": False, "error": "WebDriver가 초기화되지 않음"}
            
            # 요소 찾기
            element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            
            # 요소가 보이도록 스크롤
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            result = {"success": True, "action": action, "selector": selector}
            
            if action == "click":
                # 클릭 가능할 때까지 대기
                clickable_element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                clickable_element.click()
                result["message"] = "요소 클릭 완료"
                
            elif action == "input" or action == "type":
                if value is None:
                    return {"success": False, "error": "입력값이 필요합니다"}
                
                element.clear()
                element.send_keys(value)
                result["message"] = f"'{value}' 입력 완료"
                result["input_value"] = value
                
            elif action == "get_text":
                text = element.text
                result["text"] = text
                result["message"] = "텍스트 추출 완료"
                
            elif action == "get_attribute":
                if value is None:
                    return {"success": False, "error": "속성명이 필요합니다"}
                
                attr_value = element.get_attribute(value)
                result["attribute"] = {value: attr_value}
                result["message"] = f"속성 '{value}' 추출 완료"
                
            elif action == "scroll_to":
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                result["message"] = "요소로 스크롤 완료"
                
            else:
                return {"success": False, "error": f"지원하지 않는 액션: {action}"}
            
            return result
            
        except TimeoutException:
            return {"success": False, "error": f"요소를 찾을 수 없음: {selector}"}
        except Exception as e:
            return {"success": False, "error": f"요소 상호작용 실패: {str(e)}"}
    
    def execute_javascript(self, script: str) -> Dict:
        """JavaScript 코드 실행"""
        try:
            if not self.driver:
                return {"success": False, "error": "WebDriver가 초기화되지 않음"}
            
            result = self.driver.execute_script(script)
            
            return {
                "success": True,
                "script": script,
                "result": result,
                "message": "JavaScript 실행 완료"
            }
            
        except Exception as e:
            return {"success": False, "error": f"JavaScript 실행 실패: {str(e)}"}
    
    def get_page_info(self) -> Dict:
        """현재 페이지 정보 수집"""
        try:
            if not self.driver:
                return {"success": False, "error": "WebDriver가 초기화되지 않음"}
            
            # 기본 정보
            info = {
                "success": True,
                "url": self.driver.current_url,
                "title": self.driver.title,
                "page_source_length": len(self.driver.page_source)
            }
            
            # JavaScript로 추가 정보 수집
            try:
                additional_info = self.driver.execute_script("""
                    return {
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        scroll: {
                            x: window.pageXOffset,
                            y: window.pageYOffset
                        },
                        document: {
                            readyState: document.readyState,
                            domain: document.domain,
                            referrer: document.referrer
                        },
                        performance: {
                            loadEventEnd: performance.timing.loadEventEnd,
                            navigationStart: performance.timing.navigationStart
                        }
                    };
                """)
                
                info.update(additional_info)
                
                # 페이지 로딩 시간 계산
                if additional_info.get("performance"):
                    perf = additional_info["performance"]
                    if perf["loadEventEnd"] and perf["navigationStart"]:
                        load_time = perf["loadEventEnd"] - perf["navigationStart"]
                        info["load_time_ms"] = load_time
                
            except Exception as e:
                info["js_info_error"] = str(e)
            
            return info
            
        except Exception as e:
            return {"success": False, "error": f"페이지 정보 수집 실패: {str(e)}"}
    
    def extract_dynamic_content(self, selectors: List[str]) -> Dict:
        """동적 콘텐츠 추출 (JavaScript로 렌더링된 내용 포함)"""
        try:
            if not self.driver:
                return {"success": False, "error": "WebDriver가 초기화되지 않음"}
            
            # 페이지 로딩 완료 대기
            self.wait_for_page_load()
            
            extracted_content = {}
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        content_list = []
                        for element in elements:
                            content_list.append({
                                "text": element.text,
                                "html": element.get_attribute('outerHTML'),
                                "visible": element.is_displayed()
                            })
                        
                        extracted_content[selector] = content_list
                    else:
                        extracted_content[selector] = []
                        
                except Exception as e:
                    extracted_content[selector] = {"error": str(e)}
            
            return {
                "success": True,
                "extracted_content": extracted_content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": f"동적 콘텐츠 추출 실패: {str(e)}"}
    
    def close_driver(self):
        """WebDriver 종료"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                return True
        except Exception as e:
            print(f"WebDriver 종료 실패: {str(e)}")
            return False
    
    def __del__(self):
        """소멸자 - WebDriver 자동 종료"""
        self.close_driver()

class WebSearchIDE:
    """웹 검색 + 사이트 접속 기능이 포함된 고급 클라우드 IDE"""
    
    def __init__(self):
        self.search_history = {}  # 사용자별 검색 기록
        self.visited_sites = {}   # 사용자별 방문 사이트 기록
        self.code_snippets = {}   # 사용자별 수집된 코드 스니펫
        
        # 고급 웹 자동화 시스템
        self.web_automation = AdvancedWebAutomation()
        
        # 개발 관련 사이트 우선순위
        self.dev_sites = [
            'github.com',
            'stackoverflow.com',
            'docs.python.org',
            'developer.mozilla.org',
            'reactjs.org',
            'nodejs.org',
            'tensorflow.org',
            'pytorch.org',
            'fastapi.tiangolo.com',
            'flask.palletsprojects.com'
        ]
    
    def advanced_site_visit(self, user_id: str, url: str, automation_tasks: List[Dict] = None) -> Dict:
        """고급 웹 자동화를 사용한 사이트 방문 및 상호작용"""
        try:
            # 방문 기록 저장
            if user_id not in self.visited_sites:
                self.visited_sites[user_id] = []
            
            self.visited_sites[user_id].append({
                'url': url,
                'type': 'advanced_automation',
                'timestamp': datetime.now().isoformat()
            })
            
            # 페이지 이동
            navigation_result = self.web_automation.navigate_to_url(url)
            if not navigation_result.get("success"):
                return navigation_result
            
            result = {
                "success": True,
                "url": url,
                "navigation": navigation_result,
                "automation_results": []
            }
            
            # 자동화 작업 수행
            if automation_tasks:
                for task in automation_tasks:
                    task_type = task.get("type")
                    
                    if task_type == "screenshot":
                        screenshot_result = self.web_automation.take_screenshot(task.get("filename"))
                        result["automation_results"].append({
                            "task": "screenshot",
                            "result": screenshot_result
                        })
                    
                    elif task_type == "interact":
                        interact_result = self.web_automation.interact_with_element(
                            task.get("selector"),
                            task.get("action"),
                            task.get("value")
                        )
                        result["automation_results"].append({
                            "task": "interact",
                            "result": interact_result
                        })
                    
                    elif task_type == "javascript":
                        js_result = self.web_automation.execute_javascript(task.get("script"))
                        result["automation_results"].append({
                            "task": "javascript",
                            "result": js_result
                        })
                    
                    elif task_type == "extract_content":
                        extract_result = self.web_automation.extract_dynamic_content(task.get("selectors", []))
                        result["automation_results"].append({
                            "task": "extract_content",
                            "result": extract_result
                        })
            
            # 페이지 정보 수집
            page_info = self.web_automation.get_page_info()
            result["page_info"] = page_info
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"고급 사이트 방문 실패: {str(e)}",
                "url": url
            }
    
    def capture_page_screenshot(self, user_id: str, url: str = None) -> Dict:
        """페이지 스크린샷 캡처"""
        try:
            if url:
                # 새 URL로 이동
                nav_result = self.web_automation.navigate_to_url(url)
                if not nav_result.get("success"):
                    return nav_result
            
            # 스크린샷 캡처
            screenshot_result = self.web_automation.take_screenshot()
            
            if screenshot_result.get("success"):
                # 방문 기록에 스크린샷 정보 추가
                if user_id not in self.visited_sites:
                    self.visited_sites[user_id] = []
                
                self.visited_sites[user_id].append({
                    'url': url or self.web_automation.driver.current_url if self.web_automation.driver else "unknown",
                    'type': 'screenshot',
                    'screenshot': screenshot_result,
                    'timestamp': datetime.now().isoformat()
                })
            
            return screenshot_result
            
        except Exception as e:
            return {"success": False, "error": f"스크린샷 캡처 실패: {str(e)}"}
    
    def interact_with_page(self, user_id: str, selector: str, action: str, value: str = None) -> Dict:
        """페이지 요소와 상호작용"""
        try:
            if not self.web_automation.driver:
                return {"success": False, "error": "브라우저가 열려있지 않습니다. 먼저 사이트를 방문해주세요."}
            
            result = self.web_automation.interact_with_element(selector, action, value)
            
            # 상호작용 기록 저장
            if user_id not in self.visited_sites:
                self.visited_sites[user_id] = []
            
            self.visited_sites[user_id].append({
                'url': self.web_automation.driver.current_url,
                'type': 'interaction',
                'interaction': {
                    'selector': selector,
                    'action': action,
                    'value': value,
                    'result': result
                },
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"페이지 상호작용 실패: {str(e)}"}
    
    def execute_page_javascript(self, user_id: str, script: str) -> Dict:
        """페이지에서 JavaScript 실행"""
        try:
            if not self.web_automation.driver:
                return {"success": False, "error": "브라우저가 열려있지 않습니다. 먼저 사이트를 방문해주세요."}
            
            result = self.web_automation.execute_javascript(script)
            
            # JavaScript 실행 기록 저장
            if user_id not in self.visited_sites:
                self.visited_sites[user_id] = []
            
            self.visited_sites[user_id].append({
                'url': self.web_automation.driver.current_url,
                'type': 'javascript',
                'javascript': {
                    'script': script,
                    'result': result
                },
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"JavaScript 실행 실패: {str(e)}"}
    
    def extract_dynamic_page_content(self, user_id: str, selectors: List[str]) -> Dict:
        """동적 페이지 콘텐츠 추출"""
        try:
            if not self.web_automation.driver:
                return {"success": False, "error": "브라우저가 열려있지 않습니다. 먼저 사이트를 방문해주세요."}
            
            result = self.web_automation.extract_dynamic_content(selectors)
            
            # 콘텐츠 추출 기록 저장
            if user_id not in self.visited_sites:
                self.visited_sites[user_id] = []
            
            self.visited_sites[user_id].append({
                'url': self.web_automation.driver.current_url,
                'type': 'content_extraction',
                'extraction': {
                    'selectors': selectors,
                    'result': result
                },
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"동적 콘텐츠 추출 실패: {str(e)}"}
    
    def close_browser(self) -> Dict:
        """브라우저 종료"""
        try:
            success = self.web_automation.close_driver()
            return {
                "success": success,
                "message": "브라우저가 종료되었습니다." if success else "브라우저 종료 중 오류가 발생했습니다."
            }
        except Exception as e:
            return {"success": False, "error": f"브라우저 종료 실패: {str(e)}"}
    
    def web_search(self, user_id: str, query: str, search_type: str = "code") -> Dict:
        """웹 검색 수행 (구글 검색 API 또는 크롤링)"""
        try:
            # 검색 기록 저장
            if user_id not in self.search_history:
                self.search_history[user_id] = []
            
            self.search_history[user_id].append({
                'query': query,
                'type': search_type,
                'timestamp': datetime.now().isoformat()
            })
            
            # 개발 관련 검색어 최적화
            optimized_query = self._optimize_dev_query(query, search_type)
            
            # 검색 수행 (실제로는 Google Search API 사용 권장)
            search_results = self._perform_search(optimized_query)
            
            # 개발 사이트 우선 정렬
            prioritized_results = self._prioritize_dev_sites(search_results)
            
            return {
                "success": True,
                "query": query,
                "optimized_query": optimized_query,
                "results": prioritized_results[:10],  # 상위 10개 결과
                "total_results": len(search_results),
                "search_tips": self._get_search_tips(search_type)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"검색 실패: {str(e)}"
            }
    
    def visit_site(self, user_id: str, url: str, extract_code: bool = True) -> Dict:
        """사이트 방문 및 내용 추출 (기본 방식)"""
        try:
            # 방문 기록 저장
            if user_id not in self.visited_sites:
                self.visited_sites[user_id] = []
            
            self.visited_sites[user_id].append({
                'url': url,
                'type': 'basic_visit',
                'timestamp': datetime.now().isoformat()
            })
            
            # 사이트 내용 가져오기
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # HTML 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 기본 정보 추출
            title = soup.find('title').get_text().strip() if soup.find('title') else "제목 없음"
            
            # 텍스트 내용 추출 (스크립트, 스타일 제외)
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            clean_text = ' '.join(text_content.split())[:2000]  # 2000자 제한
            
            result = {
                "success": True,
                "url": url,
                "title": title,
                "content_preview": clean_text,
                "site_type": self._identify_site_type(url),
                "timestamp": datetime.now().isoformat()
            }
            
            # 코드 스니펫 추출
            if extract_code:
                code_snippets = self._extract_code_snippets(soup, url)
                if code_snippets:
                    result["code_snippets"] = code_snippets
                    
                    # 사용자별 코드 스니펫 저장
                    if user_id not in self.code_snippets:
                        self.code_snippets[user_id] = []
                    
                    for snippet in code_snippets:
                        self.code_snippets[user_id].append({
                            'code': snippet['code'],
                            'language': snippet['language'],
                            'source_url': url,
                            'title': title,
                            'timestamp': datetime.now().isoformat()
                        })
            
            # 관련 링크 추출
            related_links = self._extract_related_links(soup, url)
            if related_links:
                result["related_links"] = related_links[:5]  # 상위 5개
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"사이트 방문 실패: {str(e)}",
                "url": url
            }
    
    def search_and_visit(self, user_id: str, query: str, auto_visit_count: int = 3) -> Dict:
        """검색 후 자동으로 상위 사이트들 방문"""
        try:
            # 웹 검색 수행
            search_result = self.web_search(user_id, query)
            
            if not search_result.get("success"):
                return search_result
            
            visited_results = []
            search_results = search_result["results"]
            
            # 상위 사이트들 자동 방문
            for i, result in enumerate(search_results[:auto_visit_count]):
                url = result.get("url")
                if url:
                    visit_result = self.visit_site(user_id, url, extract_code=True)
                    if visit_result.get("success"):
                        visited_results.append({
                            "rank": i + 1,
                            "search_result": result,
                            "visit_result": visit_result
                        })
            
            return {
                "success": True,
                "query": query,
                "search_summary": {
                    "total_results": search_result["total_results"],
                    "visited_count": len(visited_results)
                },
                "visited_sites": visited_results,
                "all_search_results": search_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"검색 및 방문 실패: {str(e)}"
            }
    
    def get_code_snippets(self, user_id: str, language: str = None, limit: int = 10) -> Dict:
        """수집된 코드 스니펫 조회"""
        try:
            if user_id not in self.code_snippets:
                return {
                    "success": True,
                    "snippets": [],
                    "message": "아직 수집된 코드 스니펫이 없습니다."
                }
            
            snippets = self.code_snippets[user_id]
            
            # 언어별 필터링
            if language:
                snippets = [s for s in snippets if s.get('language', '').lower() == language.lower()]
            
            # 최신순 정렬 및 제한
            snippets = sorted(snippets, key=lambda x: x['timestamp'], reverse=True)[:limit]
            
            return {
                "success": True,
                "snippets": snippets,
                "total_count": len(self.code_snippets[user_id]),
                "filtered_count": len(snippets)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"코드 스니펫 조회 실패: {str(e)}"
            }
    
    def test_code_online(self, code: str, language: str = "python") -> Dict:
        """온라인에서 코드 실행 테스트"""
        try:
            if language.lower() == "python":
                return self._test_python_code(code)
            elif language.lower() in ["javascript", "js"]:
                return self._test_javascript_code(code)
            else:
                return {
                    "success": False,
                    "error": f"지원하지 않는 언어: {language}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"코드 실행 실패: {str(e)}"
            }
    
    def _optimize_dev_query(self, query: str, search_type: str) -> str:
        """개발 관련 검색어 최적화"""
        optimizations = {
            "code": f"{query} code example tutorial",
            "error": f"{query} error solution fix",
            "library": f"{query} library documentation example",
            "api": f"{query} API documentation example",
            "tutorial": f"{query} tutorial guide step by step"
        }
        
        return optimizations.get(search_type, f"{query} programming development")
    
    def _perform_search(self, query: str) -> List[Dict]:
        """실제 검색 수행 (Google Search API 또는 크롤링)"""
        # 실제로는 Google Custom Search API 사용 권장
        # 여기서는 시뮬레이션
        
        # DuckDuckGo 검색 시뮬레이션 (실제로는 API 호출)
        try:
            search_url = f"https://duckduckgo.com/html/?q={query}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 실제 구현에서는 적절한 검색 API 사용
            mock_results = [
                {
                    "title": f"{query} - GitHub Repository",
                    "url": f"https://github.com/search?q={query}",
                    "snippet": f"GitHub repositories related to {query}",
                    "site": "github.com"
                },
                {
                    "title": f"{query} - Stack Overflow",
                    "url": f"https://stackoverflow.com/search?q={query}",
                    "snippet": f"Stack Overflow questions and answers about {query}",
                    "site": "stackoverflow.com"
                },
                {
                    "title": f"{query} Documentation",
                    "url": f"https://docs.python.org/search.html?q={query}",
                    "snippet": f"Official documentation for {query}",
                    "site": "docs.python.org"
                }
            ]
            
            return mock_results
            
        except Exception as e:
            return []
    
    def _prioritize_dev_sites(self, results: List[Dict]) -> List[Dict]:
        """개발 사이트 우선순위로 정렬"""
        def get_priority(result):
            url = result.get("url", "")
            for i, site in enumerate(self.dev_sites):
                if site in url:
                    return i
            return len(self.dev_sites)
        
        return sorted(results, key=get_priority)
    
    def _identify_site_type(self, url: str) -> str:
        """사이트 타입 식별"""
        domain = urlparse(url).netloc.lower()
        
        site_types = {
            'github.com': 'repository',
            'stackoverflow.com': 'qa',
            'docs.python.org': 'documentation',
            'developer.mozilla.org': 'documentation',
            'medium.com': 'blog',
            'dev.to': 'blog',
            'youtube.com': 'video',
            'pypi.org': 'package'
        }
        
        for site, type_name in site_types.items():
            if site in domain:
                return type_name
        
        return 'general'
    
    def _extract_code_snippets(self, soup: BeautifulSoup, url: str) -> List[Dict]:
        """HTML에서 코드 스니펫 추출"""
        snippets = []
        
        # <pre>, <code> 태그에서 코드 추출
        code_elements = soup.find_all(['pre', 'code'])
        
        for element in code_elements:
            code_text = element.get_text().strip()
            
            # 너무 짧거나 긴 코드 제외
            if len(code_text) < 10 or len(code_text) > 2000:
                continue
            
            # 언어 감지
            language = self._detect_code_language(element, code_text)
            
            snippets.append({
                'code': code_text,
                'language': language,
                'source': 'code_tag'
            })
        
        # GitHub 스타일 코드 블록
        github_codes = soup.find_all('div', class_=re.compile(r'highlight'))
        for code_div in github_codes:
            code_text = code_div.get_text().strip()
            if 10 <= len(code_text) <= 2000:
                language = self._detect_code_language(code_div, code_text)
                snippets.append({
                    'code': code_text,
                    'language': language,
                    'source': 'github_highlight'
                })
        
        return snippets[:5]  # 최대 5개
    
    def _detect_code_language(self, element, code_text: str) -> str:
        """코드 언어 감지"""
        # 클래스명에서 언어 추출
        class_names = element.get('class', [])
        for class_name in class_names:
            if 'python' in class_name.lower():
                return 'python'
            elif 'javascript' in class_name.lower() or 'js' in class_name.lower():
                return 'javascript'
            elif 'html' in class_name.lower():
                return 'html'
            elif 'css' in class_name.lower():
                return 'css'
            elif 'sql' in class_name.lower():
                return 'sql'
        
        # 코드 내용으로 언어 추측
        if any(keyword in code_text for keyword in ['def ', 'import ', 'print(', 'if __name__']):
            return 'python'
        elif any(keyword in code_text for keyword in ['function', 'const ', 'let ', 'var ', '=>']):
            return 'javascript'
        elif any(keyword in code_text for keyword in ['<html', '<div', '<script']):
            return 'html'
        elif any(keyword in code_text for keyword in ['SELECT', 'FROM', 'WHERE', 'INSERT']):
            return 'sql'
        
        return 'unknown'
    
    def _extract_related_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """관련 링크 추출"""
        links = []
        
        # a 태그에서 링크 추출
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            # 상대 URL을 절대 URL로 변환
            full_url = urljoin(base_url, href)
            
            # 유효한 링크만 포함
            if text and len(text) > 5 and 'http' in full_url:
                links.append({
                    'url': full_url,
                    'text': text[:100],  # 텍스트 길이 제한
                    'type': self._identify_site_type(full_url)
                })
        
        return links
    
    def _test_python_code(self, code: str) -> Dict:
        """Python 코드 실행 테스트"""
        try:
            # 임시 파일에 코드 저장
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # 코드 실행
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 임시 파일 삭제
            os.unlink(temp_file)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "execution_time": "< 10초"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "코드 실행 시간 초과 (10초)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"실행 오류: {str(e)}"
            }
    
    def _test_javascript_code(self, code: str) -> Dict:
        """JavaScript 코드 실행 테스트 (Node.js 필요)"""
        try:
            # 임시 파일에 코드 저장
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Node.js로 코드 실행
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 임시 파일 삭제
            os.unlink(temp_file)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "execution_time": "< 10초"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "코드 실행 시간 초과 (10초)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"JavaScript 실행 오류: {str(e)} (Node.js 설치 필요)"
            }
    
    def _get_search_tips(self, search_type: str) -> List[str]:
        """검색 타입별 팁 제공"""
        tips = {
            "code": [
                "구체적인 함수명이나 라이브러리명을 포함하세요",
                "예: 'pandas dataframe merge' 대신 'pandas merge on multiple columns'"
            ],
            "error": [
                "정확한 에러 메시지를 포함하세요",
                "예: 'ModuleNotFoundError: No module named pandas'"
            ],
            "library": [
                "라이브러리 버전을 명시하면 더 정확한 결과를 얻을 수 있습니다",
                "예: 'tensorflow 2.0 tutorial'"
            ]
        }
        
        return tips[search_type] if search_type in tips else tips["general"]

# 전역 인스턴스
web_search_ide = WebSearchIDE()

# 비동기 크롤링 시스템 추가
import asyncio
import aiohttp
import aiofiles
from asyncio_throttle import Throttler
from typing import Any, Coroutine
import random

class AsyncWebCrawler:
    """asyncio와 aiohttp를 활용한 고성능 비동기 크롤링 시스템"""
    
    def __init__(self, max_concurrent: int = 10, requests_per_second: int = 5):
        self.max_concurrent = max_concurrent
        self.requests_per_second = requests_per_second
        self.throttler = Throttler(rate_limit=requests_per_second)
        self.session = None
        self.results = []
        self.failed_urls = []
        
        # 다양한 User-Agent 목록
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def fetch_url(self, url: str, retries: int = 3, backoff_factor: float = 1.0) -> Dict:
        """단일 URL 비동기 크롤링 (지수 백오프 재시도 포함)"""
        for attempt in range(retries + 1):
            try:
                async with self.throttler:
                    # 랜덤 User-Agent 설정
                    headers = {'User-Agent': random.choice(self.user_agents)}
                    
                    async with self.session.get(url, headers=headers, ssl=False) as response:
                        # 상태 코드 확인
                        if response.status == 200:
                            content = await response.text()
                            
                            # BeautifulSoup으로 파싱
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            # 메타데이터 추출
                            title = soup.find('title')
                            title_text = title.get_text().strip() if title else "제목 없음"
                            
                            # 설명 메타태그 추출
                            description_tag = soup.find('meta', attrs={'name': 'description'})
                            description = description_tag.get('content', '') if description_tag else ''
                            
                            # 키워드 메타태그 추출
                            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
                            keywords = keywords_tag.get('content', '') if keywords_tag else ''
                            
                            # 코드 블록 추출
                            code_blocks = self._extract_code_blocks_async(soup)
                            
                            # 링크 추출
                            links = self._extract_links_async(soup, url)
                            
                            return {
                                'success': True,
                                'url': url,
                                'status_code': response.status,
                                'title': title_text,
                                'description': description,
                                'keywords': keywords,
                                'content_length': len(content),
                                'code_blocks': code_blocks,
                                'links': links[:10],  # 상위 10개 링크만
                                'crawl_time': datetime.now().isoformat(),
                                'attempt': attempt + 1
                            }
                        else:
                            if attempt == retries:
                                return {
                                    'success': False,
                                    'url': url,
                                    'error': f'HTTP {response.status}',
                                    'attempt': attempt + 1
                                }
                            
            except asyncio.TimeoutError:
                if attempt == retries:
                    return {
                        'success': False,
                        'url': url,
                        'error': '요청 시간 초과',
                        'attempt': attempt + 1
                    }
                    
            except Exception as e:
                if attempt == retries:
                    return {
                        'success': False,
                        'url': url,
                        'error': str(e),
                        'attempt': attempt + 1
                    }
            
            # 지수 백오프 대기
            if attempt < retries:
                wait_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(wait_time)
        
        return {
            'success': False,
            'url': url,
            'error': '모든 재시도 실패',
            'attempt': retries + 1
        }
    
    async def crawl_multiple_urls(self, urls: List[str], progress_callback=None) -> Dict:
        """다중 URL 동시 크롤링"""
        start_time = time.time()
        
        # Semaphore로 동시 실행 수 제한
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def crawl_with_semaphore(url: str) -> Dict:
            async with semaphore:
                result = await self.fetch_url(url)
                if progress_callback:
                    await progress_callback(url, result)
                return result
        
        # 모든 URL에 대해 동시 크롤링 실행
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 정리
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    'url': urls[i],
                    'error': str(result),
                    'success': False
                })
            elif result.get('success', False):
                successful_results.append(result)
            else:
                failed_results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        return {
            'success': True,
            'total_urls': len(urls),
            'successful_count': len(successful_results),
            'failed_count': len(failed_results),
            'success_rate': len(successful_results) / len(urls) * 100,
            'total_time': total_time,
            'average_time_per_url': total_time / len(urls),
            'successful_results': successful_results,
            'failed_results': failed_results,
            'performance_stats': {
                'urls_per_second': len(urls) / total_time,
                'concurrent_requests': self.max_concurrent,
                'throttle_rate': self.requests_per_second
            }
        }
    
    async def search_and_crawl(self, search_query: str, max_results: int = 10) -> Dict:
        """검색 결과를 기반으로 한 자동 크롤링"""
        try:
            # 구글 검색 API 또는 웹 스크래핑으로 검색 결과 URL 수집
            search_urls = await self._perform_async_search(search_query, max_results)
            
            if not search_urls:
                return {
                    'success': False,
                    'error': '검색 결과를 찾을 수 없습니다',
                    'query': search_query
                }
            
            # 검색된 URL들을 동시 크롤링
            crawl_results = await self.crawl_multiple_urls(search_urls)
            
            # 검색 쿼리와 관련된 콘텐츠 필터링
            relevant_results = self._filter_relevant_content(
                crawl_results['successful_results'], 
                search_query
            )
            
            return {
                'success': True,
                'search_query': search_query,
                'total_crawled': crawl_results['total_urls'],
                'relevant_count': len(relevant_results),
                'crawl_stats': crawl_results['performance_stats'],
                'relevant_results': relevant_results,
                'all_results': crawl_results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'검색 및 크롤링 실패: {str(e)}',
                'query': search_query
            }
    
    def _extract_code_blocks_async(self, soup: BeautifulSoup) -> List[Dict]:
        """비동기 환경에서 코드 블록 추출"""
        code_blocks = []
        
        # <pre>, <code> 태그에서 코드 추출
        for tag in soup.find_all(['pre', 'code']):
            code_text = tag.get_text().strip()
            if len(code_text) > 10:  # 최소 길이 필터
                # 언어 감지
                language = self._detect_language_from_tag(tag, code_text)
                
                code_blocks.append({
                    'code': code_text[:1000],  # 최대 1000자
                    'language': language,
                    'tag': tag.name,
                    'length': len(code_text)
                })
                
                if len(code_blocks) >= 5:  # 최대 5개까지만
                    break
        
        return code_blocks
    
    def _extract_links_async(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """비동기 환경에서 링크 추출"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                # 절대 URL로 변환
                full_url = urljoin(base_url, href)
                link_text = link.get_text().strip()
                
                if link_text and len(link_text) > 0:
                    links.append({
                        'url': full_url,
                        'text': link_text[:100],  # 최대 100자
                        'domain': urlparse(full_url).netloc
                    })
        
        return links
    
    def _detect_language_from_tag(self, tag, code_text: str) -> str:
        """태그 속성과 코드 내용으로부터 언어 감지"""
        # class 속성에서 언어 정보 추출
        class_attr = tag.get('class', [])
        for cls in class_attr:
            if isinstance(cls, str):
                if 'python' in cls.lower():
                    return 'python'
                elif 'javascript' in cls.lower() or 'js' in cls.lower():
                    return 'javascript'
                elif 'java' in cls.lower():
                    return 'java'
                elif 'cpp' in cls.lower() or 'c++' in cls.lower():
                    return 'cpp'
                elif 'html' in cls.lower():
                    return 'html'
                elif 'css' in cls.lower():
                    return 'css'
        
        # 코드 내용으로부터 언어 추측
        if 'def ' in code_text or 'import ' in code_text or 'print(' in code_text:
            return 'python'
        elif 'function' in code_text or 'var ' in code_text or 'let ' in code_text:
            return 'javascript'
        elif '<html' in code_text or '<div' in code_text:
            return 'html'
        elif 'public class' in code_text or 'System.out.println' in code_text:
            return 'java'
        
        return 'unknown'
    
    async def _perform_async_search(self, query: str, max_results: int) -> List[str]:
        """비동기 검색 수행 (실제 구현에서는 검색 API 사용)"""
        # 개발 관련 사이트들을 우선적으로 검색
        dev_sites = [
            f"https://stackoverflow.com/search?q={query.replace(' ', '+')}",
            f"https://github.com/search?q={query.replace(' ', '+')}",
            f"https://docs.python.org/3/search.html?q={query.replace(' ', '+')}",
            f"https://developer.mozilla.org/en-US/search?q={query.replace(' ', '+')}",
            f"https://www.w3schools.com/search/search_asp.asp?search={query.replace(' ', '+')}",
        ]
        
        return dev_sites[:max_results]
    
    def _filter_relevant_content(self, results: List[Dict], query: str) -> List[Dict]:
        """검색 쿼리와 관련성이 높은 콘텐츠 필터링"""
        query_keywords = query.lower().split()
        relevant_results = []
        
        for result in results:
            relevance_score = 0
            
            # 제목에서 키워드 매칭
            title = result.get('title', '').lower()
            for keyword in query_keywords:
                if keyword in title:
                    relevance_score += 3
            
            # 설명에서 키워드 매칭
            description = result.get('description', '').lower()
            for keyword in query_keywords:
                if keyword in description:
                    relevance_score += 2
            
            # 코드 블록에서 키워드 매칭
            for code_block in result.get('code_blocks', []):
                code_text = code_block.get('code', '').lower()
                for keyword in query_keywords:
                    if keyword in code_text:
                        relevance_score += 1
            
            # 관련성 점수가 1 이상인 경우만 포함
            if relevance_score >= 1:
                result['relevance_score'] = relevance_score
                relevant_results.append(result)
        
        # 관련성 점수 순으로 정렬
        relevant_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return relevant_results 