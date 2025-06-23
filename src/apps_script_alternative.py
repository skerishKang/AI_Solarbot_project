"""
🚀 Apps Script 완전 대체 시스템
원래 목표였던 Apps Script 기능을 Python으로 완전 구현
"""

import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from dataclasses import dataclass
import requests
from urllib.parse import urlencode

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WebAppRequest:
    """웹앱 요청 데이터 클래스"""
    action: str
    user_id: str
    file_id: Optional[str] = None
    content: Optional[str] = None
    file_name: Optional[str] = None
    folder_id: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class AppsScriptAlternative:
    """Apps Script 대체 시스템"""
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.webhook_url = None
        self.active_sessions: Dict[str, Dict] = {}
        
        # Apps Script 웹앱 기능 구현
        self.webapp_handlers = {
            'doGet': self._handle_get_request,
            'doPost': self._handle_post_request,
            'createFile': self._create_file,
            'updateFile': self._update_file,
            'deleteFile': self._delete_file,
            'listFiles': self._list_files,
            'shareFile': self._share_file,
            'getFileContent': self._get_file_content,
            'createFolder': self._create_folder,
            'moveFile': self._move_file,
            'copyFile': self._copy_file
        }
        
        logger.info("🚀 Apps Script 대체 시스템 초기화 완료")
    
    def set_webhook_url(self, url: str):
        """웹훅 URL 설정 (Apps Script 웹앱 URL 대체)"""
        self.webhook_url = url
        logger.info(f"🔗 웹훅 URL 설정: {url}")
    
    async def _handle_get_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET 요청 처리 (Apps Script doGet 대체)"""
        try:
            action = params.get('action', 'status')
            user_id = params.get('user_id')
            
            if action == 'status':
                return {
                    'status': 'success',
                    'message': '팜솔라 클라우드 IDE 웹앱이 정상 작동 중입니다',
                    'timestamp': datetime.now().isoformat(),
                    'active_users': len(self.active_sessions)
                }
            
            elif action == 'list_files':
                return await self._list_files(user_id, params.get('folder_id'))
            
            elif action == 'get_file':
                return await self._get_file_content(user_id, params.get('file_id'))
            
            else:
                return {
                    'status': 'error',
                    'message': f'알 수 없는 액션: {action}'
                }
                
        except Exception as e:
            logger.error(f"❌ GET 요청 처리 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _handle_post_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST 요청 처리 (Apps Script doPost 대체)"""
        try:
            request = WebAppRequest(**data)
            
            if request.action in self.webapp_handlers:
                handler = self.webapp_handlers[request.action]
                return await handler(request)
            else:
                return {
                    'status': 'error',
                    'message': f'지원하지 않는 액션: {request.action}'
                }
                
        except Exception as e:
            logger.error(f"❌ POST 요청 처리 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _create_file(self, request: WebAppRequest) -> Dict[str, Any]:
        """파일 생성 (Apps Script 대체)"""
        try:
            from user_auth_manager import user_auth_manager
            
            if not user_auth_manager.is_user_connected(request.user_id):
                return {
                    'status': 'error',
                    'message': '사용자 인증이 필요합니다'
                }
            
            credentials = user_auth_manager.get_user_credentials(request.user_id)
            service = build('drive', 'v3', credentials=credentials)
            
            # 파일 메타데이터 설정
            file_metadata = {
                'name': request.file_name,
                'parents': [request.folder_id] if request.folder_id else []
            }
            
            # 파일 생성
            if request.content:
                from googleapiclient.http import MediaIoBaseUpload
                import io
                
                media = MediaIoBaseUpload(
                    io.BytesIO(request.content.encode('utf-8')),
                    mimetype='text/plain'
                )
                
                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,createdTime'
                ).execute()
            else:
                file = service.files().create(
                    body=file_metadata,
                    fields='id,name,createdTime'
                ).execute()
            
            # 텔레그램 알림 전송
            if self.bot:
                await self._send_creation_notification(request.user_id, file)
            
            return {
                'status': 'success',
                'file_id': file['id'],
                'file_name': file['name'],
                'created_time': file['createdTime']
            }
            
        except Exception as e:
            logger.error(f"❌ 파일 생성 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _update_file(self, request: WebAppRequest) -> Dict[str, Any]:
        """파일 업데이트 (Apps Script 대체)"""
        try:
            from user_auth_manager import user_auth_manager
            
            credentials = user_auth_manager.get_user_credentials(request.user_id)
            service = build('drive', 'v3', credentials=credentials)
            
            if request.content:
                from googleapiclient.http import MediaIoBaseUpload
                import io
                
                media = MediaIoBaseUpload(
                    io.BytesIO(request.content.encode('utf-8')),
                    mimetype='text/plain'
                )
                
                file = service.files().update(
                    fileId=request.file_id,
                    media_body=media,
                    fields='id,name,modifiedTime'
                ).execute()
            else:
                # 메타데이터만 업데이트
                file_metadata = {}
                if request.file_name:
                    file_metadata['name'] = request.file_name
                
                file = service.files().update(
                    fileId=request.file_id,
                    body=file_metadata,
                    fields='id,name,modifiedTime'
                ).execute()
            
            # 텔레그램 알림 전송
            if self.bot:
                await self._send_update_notification(request.user_id, file)
            
            return {
                'status': 'success',
                'file_id': file['id'],
                'file_name': file['name'],
                'modified_time': file['modifiedTime']
            }
            
        except Exception as e:
            logger.error(f"❌ 파일 업데이트 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _delete_file(self, request: WebAppRequest) -> Dict[str, Any]:
        """파일 삭제 (Apps Script 대체)"""
        try:
            from user_auth_manager import user_auth_manager
            
            credentials = user_auth_manager.get_user_credentials(request.user_id)
            service = build('drive', 'v3', credentials=credentials)
            
            # 파일 정보 먼저 가져오기
            file = service.files().get(fileId=request.file_id, fields='id,name').execute()
            
            # 파일 삭제
            service.files().delete(fileId=request.file_id).execute()
            
            # 텔레그램 알림 전송
            if self.bot:
                await self._send_deletion_notification(request.user_id, file)
            
            return {
                'status': 'success',
                'message': f'파일이 삭제되었습니다: {file["name"]}'
            }
            
        except Exception as e:
            logger.error(f"❌ 파일 삭제 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _list_files(self, user_id: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """파일 목록 조회 (Apps Script 대체)"""
        try:
            from user_auth_manager import user_auth_manager
            
            credentials = user_auth_manager.get_user_credentials(user_id)
            service = build('drive', 'v3', credentials=credentials)
            
            # 쿼리 구성
            if folder_id:
                query = f"'{folder_id}' in parents and trashed=false"
            else:
                query = "trashed=false"
            
            # 파일 목록 조회
            results = service.files().list(
                q=query,
                fields='files(id,name,mimeType,modifiedTime,size)',
                pageSize=100
            ).execute()
            
            files = results.get('files', [])
            
            return {
                'status': 'success',
                'files': files,
                'count': len(files)
            }
            
        except Exception as e:
            logger.error(f"❌ 파일 목록 조회 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _get_file_content(self, user_id: str, file_id: str) -> Dict[str, Any]:
        """파일 내용 조회 (Apps Script 대체)"""
        try:
            from user_auth_manager import user_auth_manager
            
            credentials = user_auth_manager.get_user_credentials(user_id)
            service = build('drive', 'v3', credentials=credentials)
            
            # 파일 메타데이터 가져오기
            file = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
            
            # 파일 내용 다운로드
            content = service.files().get_media(fileId=file_id).execute()
            
            return {
                'status': 'success',
                'file_id': file['id'],
                'file_name': file['name'],
                'mime_type': file['mimeType'],
                'content': content.decode('utf-8') if isinstance(content, bytes) else content
            }
            
        except Exception as e:
            logger.error(f"❌ 파일 내용 조회 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _share_file(self, request: WebAppRequest) -> Dict[str, Any]:
        """파일 공유 (Apps Script 대체)"""
        try:
            from user_auth_manager import user_auth_manager
            
            credentials = user_auth_manager.get_user_credentials(request.user_id)
            service = build('drive', 'v3', credentials=credentials)
            
            # 공유 권한 설정
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            service.permissions().create(
                fileId=request.file_id,
                body=permission
            ).execute()
            
            # 공유 링크 생성
            file = service.files().get(
                fileId=request.file_id,
                fields='id,name,webViewLink'
            ).execute()
            
            return {
                'status': 'success',
                'file_id': file['id'],
                'file_name': file['name'],
                'share_link': file['webViewLink']
            }
            
        except Exception as e:
            logger.error(f"❌ 파일 공유 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _create_folder(self, request: WebAppRequest) -> Dict[str, Any]:
        """폴더 생성 (Apps Script 대체)"""
        try:
            from user_auth_manager import user_auth_manager
            
            credentials = user_auth_manager.get_user_credentials(request.user_id)
            service = build('drive', 'v3', credentials=credentials)
            
            folder_metadata = {
                'name': request.file_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [request.folder_id] if request.folder_id else []
            }
            
            folder = service.files().create(
                body=folder_metadata,
                fields='id,name,createdTime'
            ).execute()
            
            return {
                'status': 'success',
                'folder_id': folder['id'],
                'folder_name': folder['name'],
                'created_time': folder['createdTime']
            }
            
        except Exception as e:
            logger.error(f"❌ 폴더 생성 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _move_file(self, request: WebAppRequest) -> Dict[str, Any]:
        """파일 이동 (Apps Script 대체)"""
        try:
            from user_auth_manager import user_auth_manager
            
            credentials = user_auth_manager.get_user_credentials(request.user_id)
            service = build('drive', 'v3', credentials=credentials)
            
            # 현재 부모 폴더 가져오기
            file = service.files().get(fileId=request.file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            
            # 파일 이동
            file = service.files().update(
                fileId=request.file_id,
                addParents=request.folder_id,
                removeParents=previous_parents,
                fields='id,name,parents'
            ).execute()
            
            return {
                'status': 'success',
                'file_id': file['id'],
                'file_name': file['name'],
                'new_parents': file['parents']
            }
            
        except Exception as e:
            logger.error(f"❌ 파일 이동 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _copy_file(self, request: WebAppRequest) -> Dict[str, Any]:
        """파일 복사 (Apps Script 대체)"""
        try:
            from user_auth_manager import user_auth_manager
            
            credentials = user_auth_manager.get_user_credentials(request.user_id)
            service = build('drive', 'v3', credentials=credentials)
            
            copy_metadata = {
                'name': request.file_name,
                'parents': [request.folder_id] if request.folder_id else []
            }
            
            copied_file = service.files().copy(
                fileId=request.file_id,
                body=copy_metadata,
                fields='id,name,createdTime'
            ).execute()
            
            return {
                'status': 'success',
                'file_id': copied_file['id'],
                'file_name': copied_file['name'],
                'created_time': copied_file['createdTime']
            }
            
        except Exception as e:
            logger.error(f"❌ 파일 복사 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _send_creation_notification(self, user_id: str, file: Dict[str, Any]):
        """파일 생성 알림 전송"""
        if self.bot:
            try:
                message = f"""🆕 **새 파일 생성됨**
📁 파일명: `{file['name']}`
🆔 파일 ID: `{file['id']}`
⏰ 생성 시간: {file.get('createdTime', 'N/A')}"""
                
                await self.bot.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"❌ 생성 알림 전송 오류: {e}")
    
    async def _send_update_notification(self, user_id: str, file: Dict[str, Any]):
        """파일 업데이트 알림 전송"""
        if self.bot:
            try:
                message = f"""✏️ **파일 업데이트됨**
📁 파일명: `{file['name']}`
🆔 파일 ID: `{file['id']}`
⏰ 수정 시간: {file.get('modifiedTime', 'N/A')}"""
                
                await self.bot.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"❌ 업데이트 알림 전송 오류: {e}")
    
    async def _send_deletion_notification(self, user_id: str, file: Dict[str, Any]):
        """파일 삭제 알림 전송"""
        if self.bot:
            try:
                message = f"""🗑️ **파일 삭제됨**
📁 파일명: `{file['name']}`
🆔 파일 ID: `{file['id']}`
⏰ 삭제 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"""
                
                await self.bot.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"❌ 삭제 알림 전송 오류: {e}")
    
    def process_webhook_request(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """웹훅 요청 처리 (Apps Script 웹앱 대체)"""
        try:
            if method.upper() == 'GET':
                return asyncio.run(self._handle_get_request(data))
            elif method.upper() == 'POST':
                return asyncio.run(self._handle_post_request(data))
            else:
                return {
                    'status': 'error',
                    'message': f'지원하지 않는 HTTP 메소드: {method}'
                }
        except Exception as e:
            logger.error(f"❌ 웹훅 요청 처리 오류: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

# 전역 인스턴스
_apps_script_alternative = None

def initialize_apps_script_alternative(bot_instance=None) -> AppsScriptAlternative:
    """Apps Script 대체 시스템 초기화"""
    global _apps_script_alternative
    _apps_script_alternative = AppsScriptAlternative(bot_instance)
    return _apps_script_alternative

def get_apps_script_alternative() -> Optional[AppsScriptAlternative]:
    """Apps Script 대체 시스템 인스턴스 반환"""
    return _apps_script_alternative 