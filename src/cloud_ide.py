"""
클라우드 IDE 핵심 기능 모듈
- 파일/폴더 트리 탐색
- 인라인 파일 편집
- 파일 생성/삭제/이동/복사
- 코드 하이라이팅 및 미리보기
- 사용자별 워크스페이스 관리
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple
from user_auth_manager import user_auth_manager
from google_drive_handler import GoogleDriveHandler

class CloudIDE:
    def __init__(self):
        self.drive_handler = GoogleDriveHandler()
        self.supported_extensions = {
            '.py': '🐍',
            '.js': '📜',
            '.html': '🌐',
            '.css': '🎨',
            '.md': '📝',
            '.txt': '📄',
            '.json': '📋',
            '.xml': '📄',
            '.sql': '🗃️',
            '.sh': '⚡',
            '.bat': '⚡',
            '.yml': '⚙️',
            '.yaml': '⚙️'
        }
        
        self.language_keywords = {
            'python': ['def', 'class', 'import', 'from', 'if', 'else', 'for', 'while', 'try', 'except'],
            'javascript': ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'try', 'catch'],
            'html': ['<html>', '<head>', '<body>', '<div>', '<span>', '<script>', '<style>'],
            'css': ['color:', 'background:', 'margin:', 'padding:', 'display:', 'position:'],
            'sql': ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'TABLE']
        }
    
    def get_file_icon(self, file_name: str, is_folder: bool = False) -> str:
        """파일 타입에 따른 아이콘 반환"""
        if is_folder:
            return '📁'
        
        ext = os.path.splitext(file_name.lower())[1]
        return self.supported_extensions.get(ext, '📄')
    
    def format_file_tree(self, files: List[Dict], current_path: str = "") -> str:
        """파일 트리를 보기 좋게 포맷팅"""
        if not files:
            return "📂 빈 폴더입니다."
        
        tree_lines = []
        folders = []
        files_list = []
        
        # 폴더와 파일 분리
        for item in files:
            if item.get('mimeType') == 'application/vnd.google-apps.folder':
                folders.append(item)
            else:
                files_list.append(item)
        
        # 폴더 먼저 표시
        for i, folder in enumerate(sorted(folders, key=lambda x: x['name'])):
            icon = '📁'
            prefix = '├── ' if i < len(folders) - 1 or files_list else '└── '
            tree_lines.append(f"{prefix}{icon} {folder['name']}/")
        
        # 파일 표시
        for i, file in enumerate(sorted(files_list, key=lambda x: x['name'])):
            icon = self.get_file_icon(file['name'])
            prefix = '├── ' if i < len(files_list) - 1 else '└── '
            size = self.format_file_size(file.get('size', '0'))
            tree_lines.append(f"{prefix}{icon} {file['name']} ({size})")
        
        return "\n".join(tree_lines)
    
    def format_file_size(self, size_str: str) -> str:
        """파일 크기를 사람이 읽기 쉬운 형태로 변환"""
        try:
            size = int(size_str)
            if size < 1024:
                return f"{size}B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f}KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size/(1024*1024):.1f}MB"
            else:
                return f"{size/(1024*1024*1024):.1f}GB"
        except:
            return "0B"
    
    def detect_language(self, file_name: str, content: str = "") -> str:
        """파일 확장자와 내용으로 언어 감지"""
        ext = os.path.splitext(file_name.lower())[1]
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.md': 'markdown',
            '.json': 'json'
        }
        
        if ext in extension_map:
            return extension_map[ext]
        
        # 내용으로 언어 추측
        if content:
            content_lower = content.lower()
            for lang, keywords in self.language_keywords.items():
                if any(keyword.lower() in content_lower for keyword in keywords):
                    return lang
        
        return 'text'
    
    def highlight_code(self, content: str, language: str) -> str:
        """간단한 코드 하이라이팅 (마크다운 형식)"""
        if not content.strip():
            return "```\n(빈 파일)\n```"
        
        # 너무 긴 파일은 앞부분만 표시
        if len(content) > 2000:
            content = content[:2000] + "\n... (파일이 잘렸습니다. 전체 내용은 구글 드라이브에서 확인하세요)"
        
        return f"```{language}\n{content}\n```"
    
    def edit_file(self, user_id: str, file_path: str, new_content: str) -> Dict:
        """파일 편집"""
        if not user_auth_manager.is_authenticated(user_id):
            return {"error": "드라이브 연결이 필요합니다. /connect_drive를 먼저 실행하세요."}
        
        try:
            # 사용자 서비스 가져오기
            service = user_auth_manager.get_user_service(user_id)
            if not service:
                return {"error": "사용자 인증 정보를 찾을 수 없습니다."}
            
            # 파일 검색
            file_info = self.find_file_by_path(user_id, file_path)
            if file_info.get('error'):
                return file_info
            
            file_id = file_info['file_id']
            
            # 파일 내용 업데이트 (MediaIoBaseUpload 사용)
            from googleapiclient.http import MediaIoBaseUpload
            import io
            
            media = MediaIoBaseUpload(
                io.BytesIO(new_content.encode('utf-8')),
                mimetype='text/plain'
            )
            
            updated_file = service.files().update(
                fileId=file_id,
                media_body=media,
                fields='id,name,webViewLink,modifiedTime,size'
            ).execute()
            
            return {
                "success": True,
                "file_name": updated_file.get('name'),
                "file_id": updated_file.get('id'),
                "web_link": updated_file.get('webViewLink'),
                "modified_time": updated_file.get('modifiedTime'),
                "new_size": self.format_file_size(updated_file.get('size', '0'))
            }
            
        except Exception as e:
            return {"error": f"파일 편집 실패: {str(e)}"}
    
    def create_file(self, user_id: str, file_path: str, content: str = "", folder_id: str = None) -> Dict:
        """새 파일 생성"""
        if not user_auth_manager.is_authenticated(user_id):
            return {"error": "드라이브 연결이 필요합니다."}
        
        try:
            service = user_auth_manager.get_user_service(user_id)
            if not service:
                return {"error": "사용자 인증 정보를 찾을 수 없습니다."}
            
            # 파일명 추출
            file_name = os.path.basename(file_path)
            if not file_name:
                return {"error": "올바른 파일명을 입력하세요."}
            
            # 폴더 ID가 없으면 루트 폴더 사용
            if not folder_id:
                folder_id = user_auth_manager.get_user_root_folder(user_id)
            
            # 파일 메타데이터
            file_metadata = {
                'name': file_name,
                'parents': [folder_id] if folder_id else []
            }
            
            # 파일 생성
            from googleapiclient.http import MediaIoBaseUpload
            import io
            
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain'
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,size'
            ).execute()
            
            return {
                "success": True,
                "file_name": file.get('name'),
                "file_id": file.get('id'),
                "web_link": file.get('webViewLink'),
                "size": self.format_file_size(file.get('size', '0'))
            }
            
        except Exception as e:
            return {"error": f"파일 생성 실패: {str(e)}"}
    
    def delete_file(self, user_id: str, file_path: str) -> Dict:
        """파일 삭제"""
        if not user_auth_manager.is_authenticated(user_id):
            return {"error": "드라이브 연결이 필요합니다."}
        
        try:
            service = user_auth_manager.get_user_service(user_id)
            if not service:
                return {"error": "사용자 인증 정보를 찾을 수 없습니다."}
            
            # 파일 검색
            file_info = self.find_file_by_path(user_id, file_path)
            if file_info.get('error'):
                return file_info
            
            file_id = file_info['file_id']
            file_name = file_info['file_name']
            
            # 파일 삭제
            service.files().delete(fileId=file_id).execute()
            
            return {
                "success": True,
                "message": f"'{file_name}' 파일이 삭제되었습니다.",
                "deleted_file": file_name
            }
            
        except Exception as e:
            return {"error": f"파일 삭제 실패: {str(e)}"}
    
    def move_file(self, user_id: str, source_path: str, dest_path: str) -> Dict:
        """파일 이동"""
        if not user_auth_manager.is_authenticated(user_id):
            return {"error": "드라이브 연결이 필요합니다."}
        
        try:
            service = user_auth_manager.get_user_service(user_id)
            if not service:
                return {"error": "사용자 인증 정보를 찾을 수 없습니다."}
            
            # 원본 파일 검색
            file_info = self.find_file_by_path(user_id, source_path)
            if file_info.get('error'):
                return file_info
            
            file_id = file_info['file_id']
            old_name = file_info['file_name']
            
            # 새 이름 추출
            new_name = os.path.basename(dest_path)
            
            # 파일 이름 변경
            updated_file = service.files().update(
                fileId=file_id,
                body={'name': new_name},
                fields='id,name,webViewLink'
            ).execute()
            
            return {
                "success": True,
                "message": f"'{old_name}' → '{new_name}'으로 이동되었습니다.",
                "old_name": old_name,
                "new_name": updated_file.get('name'),
                "web_link": updated_file.get('webViewLink')
            }
            
        except Exception as e:
            return {"error": f"파일 이동 실패: {str(e)}"}
    
    def copy_file(self, user_id: str, source_path: str, dest_path: str) -> Dict:
        """파일 복사"""
        if not user_auth_manager.is_authenticated(user_id):
            return {"error": "드라이브 연결이 필요합니다."}
        
        try:
            service = user_auth_manager.get_user_service(user_id)
            if not service:
                return {"error": "사용자 인증 정보를 찾을 수 없습니다."}
            
            # 원본 파일 검색
            file_info = self.find_file_by_path(user_id, source_path)
            if file_info.get('error'):
                return file_info
            
            file_id = file_info['file_id']
            original_name = file_info['file_name']
            
            # 복사본 이름 추출
            copy_name = os.path.basename(dest_path)
            
            # 파일 복사
            copied_file = service.files().copy(
                fileId=file_id,
                body={'name': copy_name},
                fields='id,name,webViewLink,size'
            ).execute()
            
            return {
                "success": True,
                "message": f"'{original_name}' → '{copy_name}'으로 복사되었습니다.",
                "original_name": original_name,
                "copy_name": copied_file.get('name'),
                "copy_id": copied_file.get('id'),
                "web_link": copied_file.get('webViewLink'),
                "size": self.format_file_size(copied_file.get('size', '0'))
            }
            
        except Exception as e:
            return {"error": f"파일 복사 실패: {str(e)}"}
    
    def read_file(self, user_id: str, file_path: str) -> Dict:
        """파일 내용 읽기"""
        if not user_auth_manager.is_authenticated(user_id):
            return {"error": "드라이브 연결이 필요합니다."}
        
        try:
            service = user_auth_manager.get_user_service(user_id)
            if not service:
                return {"error": "사용자 인증 정보를 찾을 수 없습니다."}
            
            # 파일 검색
            file_info = self.find_file_by_path(user_id, file_path)
            if file_info.get('error'):
                return file_info
            
            file_id = file_info['file_id']
            file_name = file_info['file_name']
            
            # 파일 내용 읽기
            from googleapiclient.http import MediaIoBaseDownload
            import io
            
            request = service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            content = file_content.getvalue().decode('utf-8')
            language = self.detect_language(file_name, content)
            highlighted_content = self.highlight_code(content, language)
            
            return {
                "success": True,
                "file_name": file_name,
                "content": content,
                "highlighted_content": highlighted_content,
                "language": language,
                "size": self.format_file_size(str(len(content))),
                "lines": len(content.split('\n'))
            }
            
        except Exception as e:
            return {"error": f"파일 읽기 실패: {str(e)}"}
    
    def find_file_by_path(self, user_id: str, file_path: str) -> Dict:
        """파일 경로로 파일 검색"""
        try:
            service = user_auth_manager.get_user_service(user_id)
            if not service:
                return {"error": "사용자 인증 정보를 찾을 수 없습니다."}
            
            # 파일명만 추출
            file_name = os.path.basename(file_path)
            
            # 파일 검색
            query = f"name='{file_name}'"
            results = service.files().list(
                q=query,
                fields="files(id,name,mimeType,size,webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                return {"error": f"'{file_name}' 파일을 찾을 수 없습니다."}
            
            # 첫 번째 매칭 파일 반환
            file = files[0]
            return {
                "success": True,
                "file_id": file['id'],
                "file_name": file['name'],
                "mime_type": file.get('mimeType'),
                "size": file.get('size', '0'),
                "web_link": file.get('webViewLink')
            }
            
        except Exception as e:
            return {"error": f"파일 검색 실패: {str(e)}"}

# 전역 인스턴스 생성
cloud_ide = CloudIDE() 