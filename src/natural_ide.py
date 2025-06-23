"""
natural_ide.py - 자연어 기반 클라우드 IDE + 웹 검색 통합 시스템
팜솔라 AI 교육과정용 텔레그램 봇 - 최신 기술 정보 검색 및 코드 테스트 기능 포함
"""

import os
import re
import json
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from src.user_auth_manager import user_auth_manager
from src.user_drive_manager import user_drive_manager
from src.web_search_ide import web_search_ide
from googleapiclient.discovery import build

class CloudIDE:
    """구글 드라이브 기반 클라우드 IDE"""
    
    def __init__(self):
        self.search_history = {}  # 사용자별 검색 기록
    
    def create_file(self, user_id: str, file_name: str, content: str = "") -> Dict:
        """파일 생성"""
        # TODO: 실제 구글 드라이브 API 구현
        return {
            "success": True,
            "size": f"{len(content)}B",
            "web_link": f"https://drive.google.com/file/d/fake_id/view"
        }
    
    def read_file(self, user_id: str, file_name: str) -> Dict:
        """파일 읽기"""
        # TODO: 실제 구글 드라이브 API 구현
        return {
            "success": True,
            "highlighted_content": f"```\n# {file_name} 내용\nprint('Hello, 팜솔라!')\n```",
            "size": "50B",
            "lines": 2,
            "language": "python"
        }
    
    def edit_file(self, user_id: str, file_name: str, content: str) -> Dict:
        """파일 편집"""
        # TODO: 실제 구글 드라이브 API 구현
        return {
            "success": True,
            "new_size": f"{len(content)}B",
            "modified_time": "방금 전",
            "web_link": f"https://drive.google.com/file/d/fake_id/view"
        }
    
    def delete_file(self, user_id: str, file_name: str) -> Dict:
        """파일 삭제"""
        # TODO: 실제 구글 드라이브 API 구현
        return {"success": True}
    
    def copy_file(self, user_id: str, source: str, target: str) -> Dict:
        """파일 복사"""
        # TODO: 실제 구글 드라이브 API 구현
        return {
            "success": True,
            "original_name": source,
            "copy_name": target,
            "size": "50B",
            "web_link": f"https://drive.google.com/file/d/fake_id/view"
        }
    
    def move_file(self, user_id: str, source: str, target: str) -> Dict:
        """파일 이동/이름변경"""
        # TODO: 실제 구글 드라이브 API 구현
        return {
            "success": True,
            "old_name": source,
            "new_name": target,
            "web_link": f"https://drive.google.com/file/d/fake_id/view"
        }

class NaturalIDE:
    """자연어 기반 IDE 인터페이스"""
    
    def __init__(self):
        self.file_action_patterns = {
            'create': [
                r'(.+?)\s*(?:파일을?|을?)\s*(?:만들|생성|작성)(?:어|해)?\s*(?:줘|주세요|달라)',
                r'(?:만들|생성|작성)(?:어|해)?\s*(?:줘|주세요|달라)\s*(.+?)\s*(?:파일을?)',
                r'새로운?\s*(.+?)\s*(?:파일을?|을?)\s*(?:만들|생성)',
                r'create\s+(.+)',
                r'touch\s+(.+)'
            ],
            'web_search': [
                r'(.+?)\s*(?:을?를?)\s*(?:검색|찾아|서치)(?:해)?\s*(?:줘|주세요|달라)',
                r'(?:검색|찾아|서치)(?:해)?\s*(?:줘|주세요|달라)\s*(.+)',
                r'(.+?)\s*(?:에\s*대해|관련)\s*(?:정보|자료|코드)를?\s*(?:찾아|검색)(?:해)?\s*(?:줘|주세요|달라)',
                r'최신\s*(.+?)\s*(?:정보|버전|코드|예제)',
                r'search\s+(.+)',
                r'find\s+(.+)',
                r'google\s+(.+)'
            ],
            'visit_site': [
                r'(.+?)\s*(?:사이트|웹사이트|페이지)에?\s*(?:접속|방문)(?:해)?\s*(?:줘|주세요|달라)',
                r'(?:접속|방문)(?:해)?\s*(?:줘|주세요|달라)\s*(.+?)\s*(?:사이트|웹사이트|페이지)',
                r'(.+?)\s*(?:링크|url)를?\s*(?:열어|확인)(?:해)?\s*(?:줘|주세요|달라)',
                r'visit\s+(.+)',
                r'open\s+(.+)',
                r'browse\s+(.+)'
            ],
            'search_and_visit': [
                r'(.+?)\s*(?:을?를?)\s*(?:검색하고|찾아서)\s*(?:사이트도?\s*)?(?:접속|방문|확인)(?:해)?\s*(?:줘|주세요|달라)',
                r'(.+?)\s*(?:검색|찾기)\s*(?:후|다음에?)\s*(?:접속|방문|확인)',
                r'(.+?)\s*(?:관련)\s*(?:사이트들?을?)\s*(?:찾아서|검색해서)\s*(?:보여|확인)(?:해)?\s*(?:줘|주세요|달라)',
                r'search\s+and\s+visit\s+(.+)',
                r'find\s+and\s+open\s+(.+)'
            ],
            'test_code': [
                r'(.+?)\s*(?:코드를?|을?)\s*(?:실행|테스트|돌려)(?:해)?\s*(?:줘|주세요|달라)',
                r'(?:실행|테스트|돌려)(?:해)?\s*(?:줘|주세요|달라)\s*(.+?)\s*(?:코드를?)',
                r'(.+?)\s*(?:이?가?)\s*(?:작동하는지|동작하는지)\s*(?:확인|테스트)(?:해)?\s*(?:줘|주세요|달라)',
                r'test\s+(.+)',
                r'run\s+(.+)',
                r'execute\s+(.+)'
            ],
            'get_snippets': [
                r'(?:수집된?|저장된?|찾은?)\s*(.+?)?\s*(?:코드|스니펫)들?을?\s*(?:보여|확인)(?:해)?\s*(?:줘|주세요|달라)',
                r'(.+?)\s*(?:언어|코드)\s*(?:스니펫|예제)들?을?\s*(?:보여|확인)(?:해)?\s*(?:줘|주세요|달라)',
                r'코드\s*(?:모음|컬렉션|리스트)을?\s*(?:보여|확인)(?:해)?\s*(?:줘|주세요|달라)',
                r'snippets?\s+(.+)?',
                r'show\s+code\s+(.+)?'
            ],
            'edit': [
                r'(.+?)\s*(?:파일을?|을?)\s*(?:수정|편집|바꿔|변경)(?:해)?\s*(?:줘|주세요|달라)',
                r'(?:수정|편집|바꿔|변경)(?:해)?\s*(?:줘|주세요|달라)\s*(.+?)\s*(?:파일을?)',
                r'(.+?)\s*(?:내용을?|을?)\s*(?:바꿔|변경)(?:해)?\s*(?:줘|주세요|달라)',
                r'edit\s+(.+)',
                r'modify\s+(.+)'
            ],
            'read': [
                r'(.+?)\s*(?:파일을?|을?|의?)\s*(?:내용을?|을?)\s*(?:보여|읽어|확인)(?:해)?\s*(?:줘|주세요|달라)',
                r'(?:보여|읽어|확인)(?:해)?\s*(?:줘|주세요|달라)\s*(.+?)\s*(?:파일을?|내용을?)',
                r'(.+?)\s*(?:파일|내용)\s*(?:보기|확인)',
                r'cat\s+(.+)',
                r'view\s+(.+)',
                r'show\s+(.+)'
            ],
            'delete': [
                r'(.+?)\s*(?:파일을?|을?)\s*(?:삭제|지워|제거)(?:해)?\s*(?:줘|주세요|달라)',
                r'(?:삭제|지워|제거)(?:해)?\s*(?:줘|주세요|달라)\s*(.+?)\s*(?:파일을?)',
                r'delete\s+(.+)',
                r'remove\s+(.+)',
                r'rm\s+(.+)'
            ],
            'copy': [
                r'(.+?)\s*(?:을?를?)\s*(.+?)\s*(?:로|으로)\s*(?:복사|카피)(?:해)?\s*(?:줘|주세요|달라)',
                r'(?:복사|카피)(?:해)?\s*(?:줘|주세요|달라)\s*(.+?)\s*(?:을?를?)\s*(.+?)\s*(?:로|으로)',
                r'copy\s+(.+?)\s+(.+)',
                r'cp\s+(.+?)\s+(.+)'
            ],
            'move': [
                r'(.+?)\s*(?:을?를?)\s*(.+?)\s*(?:로|으로)\s*(?:이동|이름을?\s*바꿔|rename)(?:해)?\s*(?:줘|주세요|달라)',
                r'(?:이동|이름을?\s*바꿔|rename)(?:해)?\s*(?:줘|주세요|달라)\s*(.+?)\s*(?:을?를?)\s*(.+?)\s*(?:로|으로)',
                r'move\s+(.+?)\s+(.+)',
                r'mv\s+(.+?)\s+(.+)',
                r'rename\s+(.+?)\s+(.+)'
            ]
        }
    
    def extract_file_name(self, text: str) -> Optional[str]:
        """텍스트에서 파일명 추출"""
        # 파일 확장자 패턴
        file_patterns = [
            r'([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)',  # 확장자가 있는 파일
            r'([a-zA-Z0-9_\-]+\.py)',              # Python 파일
            r'([a-zA-Z0-9_\-]+\.js)',              # JavaScript 파일
            r'([a-zA-Z0-9_\-]+\.html?)',           # HTML 파일
            r'([a-zA-Z0-9_\-]+\.css)',             # CSS 파일
            r'([a-zA-Z0-9_\-]+\.md)',              # Markdown 파일
            r'([a-zA-Z0-9_\-]+\.json)',            # JSON 파일
            r'([a-zA-Z0-9_\-]+\.txt)',             # Text 파일
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # 확장자가 없는 경우 단어 추출 후 .txt 추가
        word_match = re.search(r'\b([a-zA-Z0-9_\-]+)\b', text)
        if word_match and len(word_match.group(1)) > 2:
            return f"{word_match.group(1)}.txt"
        
        return None
    
    def extract_content(self, text: str) -> Optional[str]:
        """텍스트에서 파일 내용 추출"""
        # 따옴표로 감싸진 내용 추출
        quote_patterns = [
            r'"([^"]*)"',
            r"'([^']*)'",
            r'```([^`]*)```',
            r'`([^`]*)`'
        ]
        
        for pattern in quote_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match and match.group(1).strip():
                return match.group(1).strip()
        
        return None
    
    def detect_intent(self, text: str) -> Tuple[str, Dict]:
        """사용자 의도 감지 (파일 작업 + 웹 검색)"""
        text_lower = text.lower()
        
        for action, patterns in self.file_action_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    if action in ['copy', 'move']:
                        # 두 개의 파일명이 필요한 작업
                        groups = match.groups()
                        if len(groups) >= 2:
                            return action, {
                                'source': groups[0].strip(),
                                'target': groups[1].strip() if len(groups) > 1 else None
                            }
                    elif action in ['web_search', 'visit_site', 'search_and_visit']:
                        # 웹 검색 관련 작업
                        groups = match.groups()
                        query_or_url = groups[0].strip() if groups else text.strip()
                        
                        # URL 감지
                        url_pattern = r'https?://[^\s]+'
                        url_match = re.search(url_pattern, text)
                        
                        return action, {
                            'query': query_or_url,
                            'url': url_match.group() if url_match else None,
                            'search_type': self._detect_search_type(text)
                        }
                    elif action in ['test_code']:
                        # 코드 테스트 작업
                        code_content = self.extract_content(text)
                        language = self._detect_language_from_text(text)
                        
                        return action, {
                            'code': code_content,
                            'language': language,
                            'file_name': self.extract_file_name(text)
                        }
                    elif action in ['get_snippets']:
                        # 코드 스니펫 조회
                        groups = match.groups()
                        language = groups[0].strip() if groups and groups[0] else None
                        
                        return action, {
                            'language': language,
                            'limit': 10
                        }
                    else:
                        # 단일 파일 작업
                        file_name = self.extract_file_name(text)
                        content = self.extract_content(text) if action in ['create', 'edit'] else None
                        
                        return action, {
                            'file_name': file_name,
                            'content': content
                        }
        
        # 기본적으로 파일명이 있으면 읽기 작업으로 판단
        file_name = self.extract_file_name(text)
        if file_name:
            return 'read', {'file_name': file_name}
        
        return 'unknown', {}
    
    def _detect_search_type(self, text: str) -> str:
        """검색 타입 감지"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['에러', '오류', 'error', 'exception', '문제']):
            return 'error'
        elif any(word in text_lower for word in ['라이브러리', 'library', '패키지', 'package', '모듈']):
            return 'library'
        elif any(word in text_lower for word in ['api', '문서', 'documentation', 'docs']):
            return 'api'
        elif any(word in text_lower for word in ['튜토리얼', 'tutorial', '강의', '가이드', 'guide']):
            return 'tutorial'
        else:
            return 'code'
    
    def _detect_language_from_text(self, text: str) -> str:
        """텍스트에서 프로그래밍 언어 감지"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['python', '파이썬', '.py']):
            return 'python'
        elif any(word in text_lower for word in ['javascript', 'js', '자바스크립트', '.js']):
            return 'javascript'
        elif any(word in text_lower for word in ['html', '.html']):
            return 'html'
        elif any(word in text_lower for word in ['css', '.css']):
            return 'css'
        elif any(word in text_lower for word in ['sql', 'database', '데이터베이스']):
            return 'sql'
        else:
            return 'python'  # 기본값
    
    def process_natural_request(self, user_id: str, text: str) -> Dict:
        """자연어 요청 처리"""
        if not user_auth_manager.is_authenticated(user_id):
            return {
                "error": "🔐 드라이브 연결이 필요합니다!\n/connect_drive 명령어로 개인 구글 드라이브를 먼저 연결해주세요."
            }
        
        # 의도 감지
        intent, params = self.detect_intent(text)
        
        if intent == 'unknown':
            return {
                "suggestion": "🤔 무엇을 도와드릴까요?\n\n예시:\n• 'test.py 파일을 만들어줘'\n• 'README.md 내용을 보여줘'\n• 'app.py 파일을 수정해줘'\n• 'config.json 파일을 삭제해줘'"
            }
        
        # 파일명 검증
        if intent != 'unknown' and not params.get('file_name') and intent not in ['copy', 'move']:
            return {
                "error": "📁 파일명을 명확히 지정해주세요.\n\n예: 'test.py 파일을 만들어줘'"
            }
        
        # 각 의도별 처리
        try:
            if intent == 'create':
                return self._handle_create(user_id, params, text)
            elif intent == 'edit':
                return self._handle_edit(user_id, params, text)
            elif intent == 'read':
                return self._handle_read(user_id, params)
            elif intent == 'delete':
                return self._handle_delete(user_id, params)
            elif intent == 'copy':
                return self._handle_copy(user_id, params)
            elif intent == 'move':
                return self._handle_move(user_id, params)
            elif intent == 'web_search':
                return self._handle_web_search(user_id, params)
            elif intent == 'visit_site':
                return self._handle_visit_site(user_id, params)
            elif intent == 'search_and_visit':
                return self._handle_search_and_visit(user_id, params)
            elif intent == 'test_code':
                return self._handle_test_code(user_id, params)
            elif intent == 'get_snippets':
                return self._handle_get_snippets(user_id, params)
            
        except Exception as e:
            return {"error": f"❌ 처리 중 오류가 발생했습니다: {str(e)}"}
    
    def _handle_create(self, user_id: str, params: Dict, original_text: str) -> Dict:
        """파일 생성 처리"""
        file_name = params['file_name']
        content = params.get('content', '')
        
        # 내용이 없으면 기본 템플릿 제공
        if not content:
            content = self._get_default_template(file_name)
        
        result = cloud_ide.create_file(user_id, file_name, content)
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"✅ **'{file_name}' 파일이 생성되었습니다!**\n\n📊 **파일 정보:**\n• 크기: {result.get('size', '0B')}\n• 링크: [구글 드라이브에서 열기]({result.get('web_link', '#')})\n\n💡 **다음 작업:**\n• 내용 확인: '{file_name} 내용을 보여줘'\n• 내용 수정: '{file_name} 파일을 수정해줘'"
            }
        else:
            return {"error": f"❌ 파일 생성 실패: {result.get('error')}"}
    
    def _handle_edit(self, user_id: str, params: Dict, original_text: str) -> Dict:
        """파일 편집 처리"""
        file_name = params['file_name']
        new_content = params.get('content')
        
        if not new_content:
            # 현재 내용을 먼저 보여주고 편집 안내
            read_result = cloud_ide.read_file(user_id, file_name)
            if read_result.get('success'):
                return {
                    "edit_mode": True,
                    "message": f"📝 **'{file_name}' 파일 편집 모드**\n\n**현재 내용:**\n{read_result.get('highlighted_content', '')}\n\n💡 **편집 방법:**\n새로운 내용을 따옴표로 감싸서 보내주세요.\n예: '{file_name} 내용을 \"새로운 코드\" 로 바꿔줘'"
                }
            else:
                return {"error": f"❌ 파일을 찾을 수 없습니다: {read_result.get('error')}"}
        
        # 파일 내용 업데이트
        result = cloud_ide.edit_file(user_id, file_name, new_content)
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"✅ **'{file_name}' 파일이 수정되었습니다!**\n\n📊 **업데이트 정보:**\n• 새 크기: {result.get('new_size', '0B')}\n• 수정 시간: {result.get('modified_time', 'N/A')}\n• 링크: [구글 드라이브에서 열기]({result.get('web_link', '#')})\n\n💡 수정된 내용을 확인하려면: '{file_name} 내용을 보여줘'"
            }
        else:
            return {"error": f"❌ 파일 편집 실패: {result.get('error')}"}
    
    def _handle_read(self, user_id: str, params: Dict) -> Dict:
        """파일 읽기 처리"""
        file_name = params['file_name']
        
        result = cloud_ide.read_file(user_id, file_name)
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"📄 **'{file_name}' 파일 내용**\n\n📊 **파일 정보:**\n• 크기: {result.get('size', '0B')}\n• 줄 수: {result.get('lines', 0)}줄\n• 언어: {result.get('language', 'text')}\n\n**내용:**\n{result.get('highlighted_content', '')}\n\n💡 **다음 작업:**\n• 수정: '{file_name} 파일을 수정해줘'\n• 복사: '{file_name}을 backup.txt로 복사해줘'"
            }
        else:
            return {"error": f"❌ 파일 읽기 실패: {result.get('error')}"}
    
    def _handle_delete(self, user_id: str, params: Dict) -> Dict:
        """파일 삭제 처리"""
        file_name = params['file_name']
        
        result = cloud_ide.delete_file(user_id, file_name)
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"🗑️ **'{file_name}' 파일이 삭제되었습니다.**\n\n⚠️ **주의:** 삭제된 파일은 구글 드라이브 휴지통에서 복구할 수 있습니다.\n\n💡 파일 목록을 확인하려면: '파일 목록을 보여줘' 또는 `/tree`"
            }
        else:
            return {"error": f"❌ 파일 삭제 실패: {result.get('error')}"}
    
    def _handle_copy(self, user_id: str, params: Dict) -> Dict:
        """파일 복사 처리"""
        source = params.get('source')
        target = params.get('target')
        
        if not source or not target:
            return {"error": "❌ 원본 파일명과 대상 파일명을 모두 지정해주세요.\n예: 'test.py를 backup.py로 복사해줘'"}
        
        result = cloud_ide.copy_file(user_id, source, target)
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"📋 **파일 복사 완료!**\n\n• 원본: {result.get('original_name')}\n• 복사본: {result.get('copy_name')}\n• 크기: {result.get('size', '0B')}\n• 링크: [구글 드라이브에서 열기]({result.get('web_link', '#')})\n\n💡 복사본 내용 확인: '{target} 내용을 보여줘'"
            }
        else:
            return {"error": f"❌ 파일 복사 실패: {result.get('error')}"}
    
    def _handle_move(self, user_id: str, params: Dict) -> Dict:
        """파일 이동/이름변경 처리"""
        source = params.get('source')
        target = params.get('target')
        
        if not source or not target:
            return {"error": "❌ 원본 파일명과 새 파일명을 모두 지정해주세요.\n예: 'old.py를 new.py로 이름을 바꿔줘'"}
        
        result = cloud_ide.move_file(user_id, source, target)
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"📁 **파일 이름 변경 완료!**\n\n• 이전 이름: {result.get('old_name')}\n• 새 이름: {result.get('new_name')}\n• 링크: [구글 드라이브에서 열기]({result.get('web_link', '#')})\n\n💡 변경된 파일 확인: '{target} 내용을 보여줘'"
            }
        else:
            return {"error": f"❌ 파일 이름 변경 실패: {result.get('error')}"}
    
    def _get_default_template(self, file_name: str) -> str:
        """파일 확장자에 따른 기본 템플릿 제공"""
        ext = os.path.splitext(file_name.lower())[1]
        
        templates = {
            '.py': f'"""\n{file_name} - Python 스크립트\n팜솔라 AI 교육과정\n"""\n\n# TODO: 코드를 작성하세요\nprint("Hello, 팜솔라!")\n',
            '.js': f'/*\n * {file_name} - JavaScript 파일\n * 팜솔라 AI 교육과정\n */\n\n// TODO: 코드를 작성하세요\nconsole.log("Hello, 팜솔라!");\n',
            '.html': f'<!DOCTYPE html>\n<html lang="ko">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>{file_name}</title>\n</head>\n<body>\n    <h1>팜솔라 AI 교육과정</h1>\n    <p>Hello, World!</p>\n</body>\n</html>\n',
            '.md': f'# {file_name}\n\n팜솔라 AI 교육과정\n\n## 개요\n\n이 문서는 팜솔라 교육과정의 일부입니다.\n\n## 내용\n\n- TODO: 내용을 작성하세요\n\n---\n*생성일: {file_name}*\n',
            '.css': f'/*\n * {file_name} - CSS 스타일시트\n * 팜솔라 AI 교육과정\n */\n\nbody {{\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n    background-color: #f5f5f5;\n}}\n\n.container {{\n    max-width: 800px;\n    margin: 0 auto;\n    background: white;\n    padding: 20px;\n    border-radius: 8px;\n    box-shadow: 0 2px 4px rgba(0,0,0,0.1);\n}}\n',
            '.json': f'{{\n    "name": "{file_name}",\n    "description": "팜솔라 AI 교육과정",\n    "version": "1.0.0",\n    "author": "팜솔라 학생",\n    "created": "{file_name}"\n}}'
        }
        
        return templates.get(ext, f'# {file_name}\n\n팜솔라 AI 교육과정\n\n내용을 작성하세요...\n')
    
    def _handle_web_search(self, user_id: str, params: Dict) -> Dict:
        """웹 검색 처리"""
        query = params.get('query', '').strip()
        search_type = params.get('search_type', 'code')
        
        if not query:
            return {"error": "❌ 검색어를 입력해주세요.\n예: 'pandas dataframe merge 검색해줘'"}
        
        result = web_search_ide.web_search(user_id, query, search_type)
        
        if result.get('success'):
            results = result.get('results', [])
            tips = result.get('search_tips', [])
            
            message = f"🔍 **'{query}' 검색 결과**\n\n"
            message += f"📊 **검색 정보:**\n• 최적화된 검색어: {result.get('optimized_query')}\n• 총 결과: {result.get('total_results')}개\n• 검색 타입: {search_type}\n\n"
            
            message += "🌐 **상위 검색 결과:**\n"
            for i, res in enumerate(results[:5], 1):
                message += f"{i}. **[{res.get('title', 'No Title')}]({res.get('url', '#')})**\n"
                message += f"   📝 {res.get('snippet', 'No description')[:100]}...\n"
                message += f"   🌍 {res.get('site', 'Unknown site')}\n\n"
            
            if tips:
                message += "💡 **검색 팁:**\n"
                for tip in tips:
                    message += f"• {tip}\n"
            
            message += "\n🚀 **다음 작업:**\n"
            message += f"• 사이트 방문: '첫 번째 사이트에 접속해줘'\n"
            message += f"• 검색+방문: '{query} 검색해서 사이트도 접속해줘'\n"
            message += f"• 코드 스니펫: '수집된 {search_type} 코드를 보여줘'"
            
            return {"success": True, "message": message}
        else:
            return {"error": f"❌ 검색 실패: {result.get('error')}"}
    
    def _handle_visit_site(self, user_id: str, params: Dict) -> Dict:
        """사이트 방문 처리"""
        url = params.get('url') or params.get('query', '').strip()
        
        if not url:
            return {"error": "❌ 방문할 URL을 입력해주세요.\n예: 'https://github.com 사이트에 접속해줘'"}
        
        # URL이 아닌 경우 검색 결과에서 URL 추출 시도
        if not url.startswith('http'):
            return {"error": "❌ 올바른 URL 형식이 아닙니다.\n예: 'https://github.com'"}
        
        result = web_search_ide.visit_site(user_id, url, extract_code=True)
        
        if result.get('success'):
            message = f"🌐 **사이트 방문 완료!**\n\n"
            message += f"📊 **사이트 정보:**\n"
            message += f"• 제목: {result.get('title', 'No Title')}\n"
            message += f"• URL: {result.get('url')}\n"
            message += f"• 타입: {result.get('site_type', 'general')}\n"
            message += f"• 방문 시간: {result.get('timestamp')}\n\n"
            
            content_preview = result.get('content_preview', '')
            if content_preview:
                message += f"📄 **내용 미리보기:**\n```\n{content_preview[:500]}...\n```\n\n"
            
            code_snippets = result.get('code_snippets', [])
            if code_snippets:
                message += f"💻 **발견된 코드 스니펫 ({len(code_snippets)}개):**\n"
                for i, snippet in enumerate(code_snippets[:3], 1):
                    message += f"{i}. **{snippet.get('language', 'unknown')}** 코드:\n"
                    message += f"```{snippet.get('language', '')}\n{snippet.get('code', '')[:200]}...\n```\n\n"
            
            related_links = result.get('related_links', [])
            if related_links:
                message += f"🔗 **관련 링크 ({len(related_links)}개):**\n"
                for i, link in enumerate(related_links[:3], 1):
                    message += f"{i}. [{link.get('text', 'Link')[:50]}...]({link.get('url')})\n"
            
            message += "\n🚀 **다음 작업:**\n"
            message += f"• 코드 테스트: '첫 번째 코드를 실행해줘'\n"
            message += f"• 스니펫 확인: '수집된 코드 스니펫을 보여줘'\n"
            message += f"• 관련 링크 방문: '두 번째 링크에 접속해줘'"
            
            return {"success": True, "message": message}
        else:
            return {"error": f"❌ 사이트 방문 실패: {result.get('error')}"}
    
    def _handle_search_and_visit(self, user_id: str, params: Dict) -> Dict:
        """검색 후 자동 사이트 방문 처리"""
        query = params.get('query', '').strip()
        search_type = params.get('search_type', 'code')
        
        if not query:
            return {"error": "❌ 검색어를 입력해주세요.\n예: 'react hooks 검색해서 사이트도 접속해줘'"}
        
        result = web_search_ide.search_and_visit(user_id, query, auto_visit_count=3)
        
        if result.get('success'):
            visited_sites = result.get('visited_sites', [])
            search_summary = result.get('search_summary', {})
            
            message = f"🔍🌐 **'{query}' 검색 + 사이트 방문 완료!**\n\n"
            message += f"📊 **작업 요약:**\n"
            message += f"• 총 검색 결과: {search_summary.get('total_results', 0)}개\n"
            message += f"• 방문한 사이트: {search_summary.get('visited_count', 0)}개\n\n"
            
            for i, site_data in enumerate(visited_sites, 1):
                search_result = site_data.get('search_result', {})
                visit_result = site_data.get('visit_result', {})
                
                message += f"🌐 **{i}. {search_result.get('title', 'No Title')}**\n"
                message += f"• URL: {visit_result.get('url')}\n"
                message += f"• 타입: {visit_result.get('site_type', 'general')}\n"
                
                code_snippets = visit_result.get('code_snippets', [])
                if code_snippets:
                    message += f"• 코드 스니펫: {len(code_snippets)}개 발견\n"
                    for j, snippet in enumerate(code_snippets[:2], 1):
                        message += f"  {j}) {snippet.get('language', 'unknown')} 코드 수집됨\n"
                
                message += "\n"
            
            message += "🚀 **다음 작업:**\n"
            message += f"• 모든 스니펫 확인: '수집된 {search_type} 코드를 보여줘'\n"
            message += f"• 코드 테스트: '첫 번째 python 코드를 실행해줘'\n"
            message += f"• 특정 사이트 재방문: '첫 번째 사이트에 다시 접속해줘'"
            
            return {"success": True, "message": message}
        else:
            return {"error": f"❌ 검색 및 방문 실패: {result.get('error')}"}
    
    def _handle_test_code(self, user_id: str, params: Dict) -> Dict:
        """코드 테스트 처리"""
        code = params.get('code', '').strip()
        language = params.get('language', 'python')
        file_name = params.get('file_name')
        
        # 코드가 없으면 파일에서 읽기 시도
        if not code and file_name:
            file_result = cloud_ide.read_file(user_id, file_name)
            if file_result.get('success'):
                # 파일 내용에서 코드 추출 (마크다운 코드 블록 제거)
                content = file_result.get('highlighted_content', '')
                code_match = re.search(r'```(?:\w+)?\n(.*?)\n```', content, re.DOTALL)
                if code_match:
                    code = code_match.group(1).strip()
                else:
                    code = content.strip()
        
        if not code:
            return {"error": "❌ 실행할 코드를 입력해주세요.\n예: 'print(\"Hello World\") 코드를 실행해줘'"}
        
        result = web_search_ide.test_code_online(code, language)
        
        if result.get('success'):
            message = f"🚀 **{language.title()} 코드 실행 완료!**\n\n"
            message += f"📝 **실행한 코드:**\n```{language}\n{code}\n```\n\n"
            
            output = result.get('output', '').strip()
            error = result.get('error', '').strip()
            return_code = result.get('return_code', 0)
            
            if return_code == 0:
                message += "✅ **실행 성공!**\n"
                if output:
                    message += f"📤 **출력 결과:**\n```\n{output}\n```\n"
                else:
                    message += "📤 **출력:** (출력 없음)\n"
            else:
                message += "❌ **실행 실패!**\n"
                if error:
                    message += f"🚨 **에러 메시지:**\n```\n{error}\n```\n"
            
            message += f"\n⏱️ **실행 시간:** {result.get('execution_time', 'N/A')}\n"
            message += f"🔢 **종료 코드:** {return_code}\n\n"
            
            if error:
                message += "🔍 **다음 작업:**\n"
                message += f"• 에러 해결: '{error.split()[0] if error else 'error'} 에러 해결 방법 검색해줘'\n"
                message += "• 코드 수정: '코드를 수정해줘'\n"
            else:
                message += "🎉 **성공! 다음 작업:**\n"
                message += "• 파일 저장: 'result.py 파일로 저장해줘'\n"
                message += "• 개선된 버전: '더 좋은 코드 예제 검색해줘'\n"
            
            return {"success": True, "message": message}
        else:
            return {"error": f"❌ 코드 실행 실패: {result.get('error')}"}
    
    def _handle_get_snippets(self, user_id: str, params: Dict) -> Dict:
        """수집된 코드 스니펫 조회 처리"""
        language = params.get('language')
        limit = params.get('limit', 10)
        
        result = web_search_ide.get_code_snippets(user_id, language, limit)
        
        if result.get('success'):
            snippets = result.get('snippets', [])
            total_count = result.get('total_count', 0)
            filtered_count = result.get('filtered_count', 0)
            
            if not snippets:
                message = "📝 **수집된 코드 스니펫이 없습니다.**\n\n"
                message += "💡 **스니펫을 수집하려면:**\n"
                message += "• 웹 검색: 'python pandas 검색해줘'\n"
                message += "• 사이트 방문: 'https://github.com 사이트에 접속해줘'\n"
                message += "• 검색+방문: 'react hooks 검색해서 사이트도 접속해줘'"
                return {"success": True, "message": message}
            
            language_filter = f" ({language})" if language else ""
            message = f"💻 **수집된 코드 스니펫{language_filter}**\n\n"
            message += f"📊 **스니펫 정보:**\n"
            message += f"• 전체 수집량: {total_count}개\n"
            message += f"• 표시 중: {filtered_count}개\n"
            if language:
                message += f"• 필터: {language} 언어만\n"
            message += "\n"
            
            for i, snippet in enumerate(snippets, 1):
                snippet_language = snippet.get('language', 'unknown')
                source_url = snippet.get('source_url', '')
                title = snippet.get('title', 'Unknown source')
                code = snippet.get('code', '')
                timestamp = snippet.get('timestamp', '')
                
                message += f"**{i}. {snippet_language.title()} 코드**\n"
                message += f"📅 수집일: {timestamp.split('T')[0] if 'T' in timestamp else timestamp}\n"
                message += f"🌐 출처: [{title[:50]}...]({source_url})\n"
                message += f"```{snippet_language}\n{code[:300]}{'...' if len(code) > 300 else ''}\n```\n\n"
                
                if i >= 5:  # 최대 5개만 표시
                    message += f"... 그리고 {len(snippets) - 5}개 더\n\n"
                    break
            
            message += "🚀 **다음 작업:**\n"
            message += f"• 코드 실행: '{i}번째 코드를 실행해줘'\n"
            message += f"• 특정 언어: 'python 코드 스니펫을 보여줘'\n"
            message += f"• 파일 저장: '첫 번째 코드를 example.py로 저장해줘'\n"
            message += f"• 더 검색: '더 많은 {language or 'python'} 예제 검색해줘'"
            
            return {"success": True, "message": message}
        else:
            return {"error": f"❌ 스니펫 조회 실패: {result.get('error')}"}

# 전역 인스턴스 생성
cloud_ide = CloudIDE()
natural_ide = NaturalIDE() 