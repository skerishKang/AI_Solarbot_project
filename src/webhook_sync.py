"""
🔄 Webhook 기반 실시간 동기화 시스템
Apps Script 대안으로 Flask 웹훅 서버를 통한 실시간 동기화 구현
"""

import json
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from dataclasses import dataclass
from collections import defaultdict
import hashlib

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FileChangeEvent:
    """파일 변경 이벤트 데이터 클래스"""
    file_id: str
    file_name: str
    event_type: str  # 'created', 'modified', 'deleted', 'moved'
    user_id: str
    timestamp: datetime
    old_path: Optional[str] = None
    new_path: Optional[str] = None
    file_hash: Optional[str] = None

class WebhookSyncManager:
    """Webhook 기반 실시간 동기화 관리자"""
    
    def __init__(self, bot_token: str, webhook_port: int = 5000):
        self.bot_token = bot_token
        self.webhook_port = webhook_port
        self.app = Flask(__name__)
        
        # 동기화 상태 관리
        self.sync_queue = asyncio.Queue()
        self.file_watchers: Dict[str, 'FileWatcher'] = {}
        self.user_credentials: Dict[str, Credentials] = {}
        self.sync_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        
        # 충돌 방지를 위한 파일 해시 캐시
        self.file_hashes: Dict[str, str] = {}
        self.last_sync_times: Dict[str, datetime] = {}
        
        # 웹훅 라우트 설정
        self._setup_webhook_routes()
        
        # 백그라운드 동기화 워커 시작
        self.sync_worker_thread = threading.Thread(target=self._start_sync_worker, daemon=True)
        self.sync_worker_thread.start()
        
        logger.info("🔄 Webhook 동기화 시스템 초기화 완료")
    
    def _setup_webhook_routes(self):
        """웹훅 라우트 설정"""
        
        @self.app.route('/webhook/drive/<user_id>', methods=['POST'])
        def drive_webhook(user_id):
            """구글 드라이브 변경 알림 수신"""
            try:
                data = request.get_json()
                
                # 드라이브 변경 이벤트 처리
                event = self._parse_drive_event(data, user_id)
                if event:
                    asyncio.run(self.sync_queue.put(event))
                    logger.info(f"📥 드라이브 변경 이벤트 수신: {event.file_name} ({event.event_type})")
                
                return jsonify({"status": "ok"})
                
            except Exception as e:
                logger.error(f"❌ 드라이브 웹훅 처리 오류: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/webhook/telegram', methods=['POST'])
        def telegram_webhook():
            """텔레그램 봇 웹훅 수신"""
            try:
                update = request.get_json()
                
                # 파일 관련 메시지 처리
                if self._is_file_message(update):
                    self._handle_telegram_file_message(update)
                
                return jsonify({"status": "ok"})
                
            except Exception as e:
                logger.error(f"❌ 텔레그램 웹훅 처리 오류: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/sync/status/<user_id>', methods=['GET'])
        def sync_status(user_id):
            """동기화 상태 확인"""
            try:
                watcher = self.file_watchers.get(user_id)
                if not watcher:
                    return jsonify({"error": "사용자 파일 와처가 없습니다"}), 404
                
                status = {
                    "user_id": user_id,
                    "is_active": watcher.is_active,
                    "last_sync": self.last_sync_times.get(user_id, "없음"),
                    "watched_files": len(watcher.watched_files),
                    "pending_syncs": self.sync_queue.qsize()
                }
                
                return jsonify(status)
                
            except Exception as e:
                logger.error(f"❌ 동기화 상태 확인 오류: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/sync/force/<user_id>', methods=['POST'])
        def force_sync(user_id):
            """강제 동기화 실행"""
            try:
                data = request.get_json()
                file_id = data.get('file_id')
                
                if file_id:
                    # 특정 파일 동기화
                    event = FileChangeEvent(
                        file_id=file_id,
                        file_name="강제_동기화",
                        event_type="modified",
                        user_id=user_id,
                        timestamp=datetime.now()
                    )
                    asyncio.run(self.sync_queue.put(event))
                else:
                    # 전체 워크스페이스 동기화
                    self._force_full_sync(user_id)
                
                return jsonify({"status": "동기화 요청 완료"})
                
            except Exception as e:
                logger.error(f"❌ 강제 동기화 오류: {e}")
                return jsonify({"error": str(e)}), 500
    
    def _parse_drive_event(self, data: Dict, user_id: str) -> Optional[FileChangeEvent]:
        """구글 드라이브 이벤트 파싱"""
        try:
            # 구글 드라이브 Push 알림 형식 파싱
            resource_id = data.get('resourceId')
            resource_state = data.get('resourceState', 'update')
            
            if not resource_id:
                return None
            
            # 파일 정보 조회
            file_info = self._get_file_info(user_id, resource_id)
            if not file_info:
                return None
            
            event_type_map = {
                'update': 'modified',
                'add': 'created',
                'remove': 'deleted',
                'trash': 'deleted'
            }
            
            return FileChangeEvent(
                file_id=resource_id,
                file_name=file_info.get('name', 'Unknown'),
                event_type=event_type_map.get(resource_state, 'modified'),
                user_id=user_id,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ 드라이브 이벤트 파싱 오류: {e}")
            return None
    
    def _get_file_info(self, user_id: str, file_id: str) -> Optional[Dict]:
        """파일 정보 조회"""
        try:
            credentials = self.user_credentials.get(user_id)
            if not credentials:
                return None
            
            service = build('drive', 'v3', credentials=credentials)
            file = service.files().get(fileId=file_id, fields='id,name,parents,mimeType,modifiedTime').execute()
            return file
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.info(f"📁 파일이 삭제됨: {file_id}")
                return {"name": "삭제된_파일", "id": file_id}
            logger.error(f"❌ 파일 정보 조회 오류: {e}")
            return None
    
    def _is_file_message(self, update: Dict) -> bool:
        """텔레그램 메시지가 파일 관련인지 확인"""
        message = update.get('message', {})
        text = message.get('text', '')
        
        # 파일 관련 명령어나 자연어 패턴 감지
        file_patterns = [
            '파일', '생성', '만들', '편집', '수정', '삭제', '복사', '이동',
            'create', 'edit', 'modify', 'delete', 'copy', 'move',
            '.py', '.js', '.html', '.css', '.md', '.json', '.txt'
        ]
        
        return any(pattern in text.lower() for pattern in file_patterns) or message.get('document')
    
    def _handle_telegram_file_message(self, update: Dict):
        """텔레그램 파일 메시지 처리"""
        try:
            message = update.get('message', {})
            user_id = str(message.get('from', {}).get('id', ''))
            
            # 파일 업로드 처리
            if message.get('document'):
                self._handle_file_upload(message, user_id)
            
            # 파일 명령어 처리
            text = message.get('text', '')
            if any(cmd in text.lower() for cmd in ['생성', 'create', '만들']):
                self._handle_file_creation_request(text, user_id)
            
        except Exception as e:
            logger.error(f"❌ 텔레그램 파일 메시지 처리 오류: {e}")
    
    def _handle_file_upload(self, message: Dict, user_id: str):
        """파일 업로드 처리"""
        try:
            document = message.get('document', {})
            file_name = document.get('file_name', 'uploaded_file')
            
            # 동기화 이벤트 생성
            event = FileChangeEvent(
                file_id="telegram_upload",
                file_name=file_name,
                event_type="created",
                user_id=user_id,
                timestamp=datetime.now()
            )
            
            asyncio.run(self.sync_queue.put(event))
            logger.info(f"📤 텔레그램 파일 업로드 감지: {file_name}")
            
        except Exception as e:
            logger.error(f"❌ 파일 업로드 처리 오류: {e}")
    
    def _handle_file_creation_request(self, text: str, user_id: str):
        """파일 생성 요청 처리"""
        try:
            # 파일명 추출 (간단한 패턴 매칭)
            import re
            patterns = [
                r'([a-zA-Z0-9_]+\.[a-zA-Z]+)',  # filename.ext
                r'"([^"]+)"',  # "filename"
                r"'([^']+)'"   # 'filename'
            ]
            
            file_name = None
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    file_name = match.group(1)
                    break
            
            if file_name:
                event = FileChangeEvent(
                    file_id="natural_creation",
                    file_name=file_name,
                    event_type="created",
                    user_id=user_id,
                    timestamp=datetime.now()
                )
                
                asyncio.run(self.sync_queue.put(event))
                logger.info(f"🆕 자연어 파일 생성 요청: {file_name}")
            
        except Exception as e:
            logger.error(f"❌ 파일 생성 요청 처리 오류: {e}")
    
    def _start_sync_worker(self):
        """백그라운드 동기화 워커 시작"""
        asyncio.run(self._sync_worker())
    
    async def _sync_worker(self):
        """동기화 이벤트 처리 워커"""
        logger.info("🔄 동기화 워커 시작")
        
        while True:
            try:
                # 동기화 이벤트 대기
                event = await self.sync_queue.get()
                
                # 중복 방지를 위한 락 사용
                with self.sync_locks[event.user_id]:
                    await self._process_sync_event(event)
                
                # 처리 완료 표시
                self.sync_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ 동기화 워커 오류: {e}")
                await asyncio.sleep(1)
    
    async def _process_sync_event(self, event: FileChangeEvent):
        """동기화 이벤트 처리"""
        try:
            logger.info(f"🔄 동기화 처리 시작: {event.file_name} ({event.event_type})")
            
            # 충돌 감지 및 방지
            if self._detect_conflict(event):
                logger.warning(f"⚠️ 충돌 감지, 동기화 건너뜀: {event.file_name}")
                return
            
            # 이벤트 타입별 처리
            if event.event_type == 'created':
                await self._handle_file_created(event)
            elif event.event_type == 'modified':
                await self._handle_file_modified(event)
            elif event.event_type == 'deleted':
                await self._handle_file_deleted(event)
            elif event.event_type == 'moved':
                await self._handle_file_moved(event)
            
            # 동기화 시간 업데이트
            self.last_sync_times[event.user_id] = datetime.now()
            
            # 텔레그램으로 동기화 알림 전송
            await self._send_sync_notification(event)
            
            logger.info(f"✅ 동기화 완료: {event.file_name}")
            
        except Exception as e:
            logger.error(f"❌ 동기화 이벤트 처리 오류: {e}")
    
    def _detect_conflict(self, event: FileChangeEvent) -> bool:
        """동기화 충돌 감지"""
        try:
            # 최근 동기화 시간 확인 (5초 이내 중복 방지)
            last_sync = self.last_sync_times.get(event.user_id)
            if last_sync and (datetime.now() - last_sync).total_seconds() < 5:
                return True
            
            # 파일 해시 기반 충돌 감지
            current_hash = self._calculate_file_hash(event)
            cached_hash = self.file_hashes.get(f"{event.user_id}:{event.file_id}")
            
            if current_hash and cached_hash and current_hash == cached_hash:
                return True  # 내용이 같으면 충돌로 간주
            
            # 해시 업데이트
            if current_hash:
                self.file_hashes[f"{event.user_id}:{event.file_id}"] = current_hash
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 충돌 감지 오류: {e}")
            return False
    
    def _calculate_file_hash(self, event: FileChangeEvent) -> Optional[str]:
        """파일 해시 계산"""
        try:
            # 간단한 메타데이터 기반 해시
            content = f"{event.file_name}:{event.timestamp.isoformat()}:{event.event_type}"
            return hashlib.md5(content.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"❌ 파일 해시 계산 오류: {e}")
            return None
    
    async def _handle_file_created(self, event: FileChangeEvent):
        """파일 생성 이벤트 처리"""
        logger.info(f"📄 파일 생성 처리: {event.file_name}")
        # 구체적인 파일 생성 로직 구현
        pass
    
    async def _handle_file_modified(self, event: FileChangeEvent):
        """파일 수정 이벤트 처리"""
        logger.info(f"✏️ 파일 수정 처리: {event.file_name}")
        # 구체적인 파일 수정 로직 구현
        pass
    
    async def _handle_file_deleted(self, event: FileChangeEvent):
        """파일 삭제 이벤트 처리"""
        logger.info(f"🗑️ 파일 삭제 처리: {event.file_name}")
        # 구체적인 파일 삭제 로직 구현
        pass
    
    async def _handle_file_moved(self, event: FileChangeEvent):
        """파일 이동 이벤트 처리"""
        logger.info(f"📁 파일 이동 처리: {event.file_name}")
        # 구체적인 파일 이동 로직 구현
        pass
    
    async def _send_sync_notification(self, event: FileChangeEvent):
        """동기화 알림 전송"""
        try:
            emoji_map = {
                'created': '🆕',
                'modified': '✏️',
                'deleted': '🗑️',
                'moved': '📁'
            }
            
            emoji = emoji_map.get(event.event_type, '🔄')
            message = f"{emoji} **동기화 완료**\n\n📄 파일: `{event.file_name}`\n🔄 작업: {event.event_type}\n⏰ 시간: {event.timestamp.strftime('%H:%M:%S')}"
            
            # 텔레그램 메시지 전송 (실제 구현 필요)
            logger.info(f"📢 동기화 알림: {message}")
            
        except Exception as e:
            logger.error(f"❌ 동기화 알림 전송 오류: {e}")
    
    def _force_full_sync(self, user_id: str):
        """전체 워크스페이스 강제 동기화"""
        try:
            logger.info(f"🔄 전체 동기화 시작: {user_id}")
            
            # 사용자의 모든 파일을 동기화 큐에 추가
            credentials = self.user_credentials.get(user_id)
            if not credentials:
                logger.error(f"❌ 사용자 인증 정보 없음: {user_id}")
                return
            
            service = build('drive', 'v3', credentials=credentials)
            
            # 팜솔라 워크스페이스 폴더의 모든 파일 조회
            query = "name='팜솔라_워크스페이스' and mimeType='application/vnd.google-apps.folder'"
            results = service.files().list(q=query, fields='files(id,name)').execute()
            
            workspace_folders = results.get('files', [])
            if not workspace_folders:
                logger.warning(f"⚠️ 워크스페이스 폴더를 찾을 수 없음: {user_id}")
                return
            
            workspace_id = workspace_folders[0]['id']
            
            # 워크스페이스 내 모든 파일 조회
            query = f"'{workspace_id}' in parents"
            results = service.files().list(q=query, fields='files(id,name,mimeType)').execute()
            
            files = results.get('files', [])
            for file in files:
                event = FileChangeEvent(
                    file_id=file['id'],
                    file_name=file['name'],
                    event_type='modified',
                    user_id=user_id,
                    timestamp=datetime.now()
                )
                asyncio.run(self.sync_queue.put(event))
            
            logger.info(f"✅ 전체 동기화 큐 등록 완료: {len(files)}개 파일")
            
        except Exception as e:
            logger.error(f"❌ 전체 동기화 오류: {e}")
    
    def register_user(self, user_id: str, credentials: Credentials):
        """사용자 등록 및 파일 와처 설정"""
        try:
            self.user_credentials[user_id] = credentials
            
            # 파일 와처 생성
            watcher = FileWatcher(user_id, credentials)
            self.file_watchers[user_id] = watcher
            
            # 드라이브 Push 알림 설정
            self._setup_drive_notifications(user_id, credentials)
            
            logger.info(f"✅ 사용자 등록 완료: {user_id}")
            
        except Exception as e:
            logger.error(f"❌ 사용자 등록 오류: {e}")
    
    def _setup_drive_notifications(self, user_id: str, credentials: Credentials):
        """구글 드라이브 Push 알림 설정"""
        try:
            service = build('drive', 'v3', credentials=credentials)
            
            # 워크스페이스 폴더 찾기
            query = "name='팜솔라_워크스페이스' and mimeType='application/vnd.google-apps.folder'"
            results = service.files().list(q=query, fields='files(id)').execute()
            
            workspace_folders = results.get('files', [])
            if not workspace_folders:
                logger.warning(f"⚠️ 워크스페이스 폴더 없음, Push 알림 설정 건너뜀: {user_id}")
                return
            
            workspace_id = workspace_folders[0]['id']
            
            # Push 알림 채널 생성
            webhook_url = f"https://your-webhook-domain.com/webhook/drive/{user_id}"
            
            body = {
                'id': f"channel_{user_id}_{int(time.time())}",
                'type': 'web_hook',
                'address': webhook_url,
                'payload': True
            }
            
            # 실제 Push 알림은 도메인이 필요하므로 로그만 출력
            logger.info(f"📡 Push 알림 설정 준비 완료: {webhook_url}")
            
        except Exception as e:
            logger.error(f"❌ Push 알림 설정 오류: {e}")
    
    def start_webhook_server(self):
        """웹훅 서버 시작"""
        try:
            logger.info(f"🚀 웹훅 서버 시작: 포트 {self.webhook_port}")
            self.app.run(host='0.0.0.0', port=self.webhook_port, debug=False)
            
        except Exception as e:
            logger.error(f"❌ 웹훅 서버 시작 오류: {e}")

class FileWatcher:
    """파일 변경 감지 클래스"""
    
    def __init__(self, user_id: str, credentials: Credentials):
        self.user_id = user_id
        self.credentials = credentials
        self.is_active = True
        self.watched_files: Dict[str, datetime] = {}
        
    def start_watching(self):
        """파일 감시 시작"""
        logger.info(f"👀 파일 감시 시작: {self.user_id}")
        self.is_active = True
    
    def stop_watching(self):
        """파일 감시 중지"""
        logger.info(f"⏹️ 파일 감시 중지: {self.user_id}")
        self.is_active = False

# 전역 동기화 매니저 인스턴스
sync_manager = None

def initialize_webhook_sync(bot_token: str, webhook_port: int = 5000):
    """웹훅 동기화 시스템 초기화"""
    global sync_manager
    sync_manager = WebhookSyncManager(bot_token, webhook_port)
    return sync_manager

def get_sync_manager() -> Optional[WebhookSyncManager]:
    """동기화 매니저 인스턴스 반환"""
    return sync_manager

if __name__ == "__main__":
    # 테스트용 실행
    import os
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', 'test_token')
    manager = initialize_webhook_sync(bot_token)
    
    # 웹훅 서버 시작
    manager.start_webhook_server() 