"""
🔄 폴링 기반 실시간 동기화 시스템
Apps Script 대안으로 더 안정적이고 간단한 폴링 방식 구현
"""

import json
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from dataclasses import dataclass
import hashlib
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FileSnapshot:
    """파일 스냅샷 데이터 클래스"""
    file_id: str
    name: str
    modified_time: str
    size: Optional[int] = None
    md5_checksum: Optional[str] = None
    parents: List[str] = None

@dataclass
class SyncEvent:
    """동기화 이벤트 데이터 클래스"""
    event_type: str  # 'created', 'modified', 'deleted'
    file_id: str
    file_name: str
    user_id: str
    timestamp: datetime
    old_snapshot: Optional[FileSnapshot] = None
    new_snapshot: Optional[FileSnapshot] = None

class PollingSyncManager:
    """폴링 기반 실시간 동기화 관리자"""
    
    def __init__(self, bot_instance=None, poll_interval: int = 30):
        self.bot = bot_instance
        self.poll_interval = poll_interval  # 폴링 간격 (초)
        
        # 사용자별 상태 관리
        self.user_credentials: Dict[str, Credentials] = {}
        self.user_snapshots: Dict[str, Dict[str, FileSnapshot]] = {}
        self.sync_threads: Dict[str, threading.Thread] = {}
        self.active_users: Set[str] = set()
        
        # 동기화 통계
        self.sync_stats = {
            'total_syncs': 0,
            'files_created': 0,
            'files_modified': 0,
            'files_deleted': 0,
            'last_sync_time': None
        }
        
        logger.info("🔄 폴링 동기화 시스템 초기화 완료")
    
    def register_user(self, user_id: str, credentials: Credentials):
        """사용자 등록 및 동기화 시작"""
        try:
            self.user_credentials[user_id] = credentials
            self.user_snapshots[user_id] = {}
            
            # 초기 스냅샷 생성
            self._create_initial_snapshot(user_id)
            
            # 동기화 스레드 시작
            self._start_sync_thread(user_id)
            
            self.active_users.add(user_id)
            
            logger.info(f"✅ 사용자 동기화 시작: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 사용자 등록 오류: {e}")
            return False
    
    def unregister_user(self, user_id: str):
        """사용자 등록 해제 및 동기화 중지"""
        try:
            if user_id in self.active_users:
                self.active_users.remove(user_id)
            
            # 동기화 스레드 정리
            if user_id in self.sync_threads:
                # 스레드는 daemon이므로 자동으로 종료됨
                del self.sync_threads[user_id]
            
            # 데이터 정리
            self.user_credentials.pop(user_id, None)
            self.user_snapshots.pop(user_id, None)
            
            logger.info(f"🛑 사용자 동기화 중지: {user_id}")
            
        except Exception as e:
            logger.error(f"❌ 사용자 등록 해제 오류: {e}")
    
    def _create_initial_snapshot(self, user_id: str):
        """초기 파일 스냅샷 생성"""
        try:
            credentials = self.user_credentials[user_id]
            service = build('drive', 'v3', credentials=credentials)
            
            # 팜솔라 워크스페이스 폴더 찾기
            workspace_id = self._get_workspace_folder_id(service)
            if not workspace_id:
                logger.warning(f"⚠️ 워크스페이스 폴더를 찾을 수 없음: {user_id}")
                return
            
            # 워크스페이스 내 모든 파일 조회
            query = f"'{workspace_id}' in parents and trashed=false"
            fields = 'files(id,name,modifiedTime,size,md5Checksum,parents)'
            
            results = service.files().list(
                q=query,
                fields=fields,
                pageSize=1000
            ).execute()
            
            files = results.get('files', [])
            snapshots = {}
            
            for file in files:
                snapshot = FileSnapshot(
                    file_id=file['id'],
                    name=file['name'],
                    modified_time=file['modifiedTime'],
                    size=file.get('size'),
                    md5_checksum=file.get('md5Checksum'),
                    parents=file.get('parents', [])
                )
                snapshots[file['id']] = snapshot
            
            self.user_snapshots[user_id] = snapshots
            
            logger.info(f"📸 초기 스냅샷 생성 완료: {user_id} ({len(snapshots)}개 파일)")
            
        except Exception as e:
            logger.error(f"❌ 초기 스냅샷 생성 오류: {e}")
    
    def _get_workspace_folder_id(self, service) -> Optional[str]:
        """팜솔라 워크스페이스 폴더 ID 조회"""
        try:
            query = "name='팜솔라_워크스페이스' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = service.files().list(q=query, fields='files(id)').execute()
            
            folders = results.get('files', [])
            if folders:
                return folders[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 워크스페이스 폴더 조회 오류: {e}")
            return None
    
    def _start_sync_thread(self, user_id: str):
        """사용자별 동기화 스레드 시작"""
        def sync_worker():
            logger.info(f"🔄 동기화 스레드 시작: {user_id}")
            
            while user_id in self.active_users:
                try:
                    # 파일 변경사항 감지 및 처리
                    self._poll_and_sync(user_id)
                    
                    # 폴링 간격만큼 대기
                    time.sleep(self.poll_interval)
                    
                except Exception as e:
                    logger.error(f"❌ 동기화 스레드 오류 ({user_id}): {e}")
                    time.sleep(5)  # 오류 시 5초 대기
            
            logger.info(f"🛑 동기화 스레드 종료: {user_id}")
        
        thread = threading.Thread(target=sync_worker, daemon=True)
        thread.start()
        self.sync_threads[user_id] = thread
    
    def _poll_and_sync(self, user_id: str):
        """파일 변경사항 폴링 및 동기화"""
        try:
            credentials = self.user_credentials[user_id]
            service = build('drive', 'v3', credentials=credentials)
            
            # 현재 파일 상태 조회
            workspace_id = self._get_workspace_folder_id(service)
            if not workspace_id:
                return
            
            query = f"'{workspace_id}' in parents and trashed=false"
            fields = 'files(id,name,modifiedTime,size,md5Checksum,parents)'
            
            results = service.files().list(
                q=query,
                fields=fields,
                pageSize=1000
            ).execute()
            
            current_files = {file['id']: file for file in results.get('files', [])}
            old_snapshots = self.user_snapshots.get(user_id, {})
            
            # 변경사항 감지
            events = self._detect_changes(user_id, old_snapshots, current_files)
            
            # 이벤트 처리
            for event in events:
                self._process_sync_event(event)
            
            # 스냅샷 업데이트
            new_snapshots = {}
            for file_id, file_data in current_files.items():
                new_snapshots[file_id] = FileSnapshot(
                    file_id=file_id,
                    name=file_data['name'],
                    modified_time=file_data['modifiedTime'],
                    size=file_data.get('size'),
                    md5_checksum=file_data.get('md5Checksum'),
                    parents=file_data.get('parents', [])
                )
            
            self.user_snapshots[user_id] = new_snapshots
            
            # 통계 업데이트
            if events:
                self.sync_stats['total_syncs'] += len(events)
                self.sync_stats['last_sync_time'] = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ 폴링 동기화 오류 ({user_id}): {e}")
    
    def _detect_changes(self, user_id: str, old_snapshots: Dict[str, FileSnapshot], 
                       current_files: Dict[str, Any]) -> List[SyncEvent]:
        """파일 변경사항 감지"""
        events = []
        
        try:
            current_file_ids = set(current_files.keys())
            old_file_ids = set(old_snapshots.keys())
            
            # 새로 생성된 파일
            created_files = current_file_ids - old_file_ids
            for file_id in created_files:
                file_data = current_files[file_id]
                events.append(SyncEvent(
                    event_type='created',
                    file_id=file_id,
                    file_name=file_data['name'],
                    user_id=user_id,
                    timestamp=datetime.now(),
                    new_snapshot=FileSnapshot(
                        file_id=file_id,
                        name=file_data['name'],
                        modified_time=file_data['modifiedTime'],
                        size=file_data.get('size'),
                        md5_checksum=file_data.get('md5Checksum'),
                        parents=file_data.get('parents', [])
                    )
                ))
                self.sync_stats['files_created'] += 1
            
            # 삭제된 파일
            deleted_files = old_file_ids - current_file_ids
            for file_id in deleted_files:
                old_snapshot = old_snapshots[file_id]
                events.append(SyncEvent(
                    event_type='deleted',
                    file_id=file_id,
                    file_name=old_snapshot.name,
                    user_id=user_id,
                    timestamp=datetime.now(),
                    old_snapshot=old_snapshot
                ))
                self.sync_stats['files_deleted'] += 1
            
            # 수정된 파일
            common_files = current_file_ids & old_file_ids
            for file_id in common_files:
                old_snapshot = old_snapshots[file_id]
                current_file = current_files[file_id]
                
                # 수정 시간 또는 체크섬 비교
                if (old_snapshot.modified_time != current_file['modifiedTime'] or
                    old_snapshot.md5_checksum != current_file.get('md5Checksum')):
                    
                    events.append(SyncEvent(
                        event_type='modified',
                        file_id=file_id,
                        file_name=current_file['name'],
                        user_id=user_id,
                        timestamp=datetime.now(),
                        old_snapshot=old_snapshot,
                        new_snapshot=FileSnapshot(
                            file_id=file_id,
                            name=current_file['name'],
                            modified_time=current_file['modifiedTime'],
                            size=current_file.get('size'),
                            md5_checksum=current_file.get('md5Checksum'),
                            parents=current_file.get('parents', [])
                        )
                    ))
                    self.sync_stats['files_modified'] += 1
            
            if events:
                logger.info(f"🔍 변경사항 감지 ({user_id}): 생성 {len(created_files)}, 수정 {len([e for e in events if e.event_type == 'modified'])}, 삭제 {len(deleted_files)}")
            
            return events
            
        except Exception as e:
            logger.error(f"❌ 변경사항 감지 오류: {e}")
            return []
    
    def _process_sync_event(self, event: SyncEvent):
        """동기화 이벤트 처리"""
        try:
            emoji_map = {
                'created': '🆕',
                'modified': '✏️',
                'deleted': '🗑️'
            }
            
            emoji = emoji_map.get(event.event_type, '🔄')
            logger.info(f"{emoji} 파일 {event.event_type}: {event.file_name} ({event.user_id})")
            
            # 텔레그램 봇으로 알림 전송
            if self.bot:
                self._send_telegram_notification(event)
            
            # 추가 처리 로직 (필요시 구현)
            if event.event_type == 'created':
                self._handle_file_created(event)
            elif event.event_type == 'modified':
                self._handle_file_modified(event)
            elif event.event_type == 'deleted':
                self._handle_file_deleted(event)
            
        except Exception as e:
            logger.error(f"❌ 동기화 이벤트 처리 오류: {e}")
    
    def _send_telegram_notification(self, event: SyncEvent):
        """텔레그램 알림 전송"""
        try:
            emoji_map = {
                'created': '🆕',
                'modified': '✏️',
                'deleted': '🗑️'
            }
            
            action_map = {
                'created': '생성됨',
                'modified': '수정됨',
                'deleted': '삭제됨'
            }
            
            emoji = emoji_map.get(event.event_type, '🔄')
            action = action_map.get(event.event_type, '변경됨')
            
            message = f"{emoji} **실시간 동기화 알림**\n\n"
            message += f"📄 파일: `{event.file_name}`\n"
            message += f"🔄 상태: {action}\n"
            message += f"⏰ 시간: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if event.event_type == 'modified' and event.old_snapshot and event.new_snapshot:
                # 파일 크기 변화 표시
                old_size = event.old_snapshot.size or 0
                new_size = event.new_snapshot.size or 0
                if old_size != new_size:
                    size_change = new_size - old_size
                    size_emoji = "📈" if size_change > 0 else "📉"
                    message += f"{size_emoji} 크기 변화: {size_change:+,} bytes\n"
            
            message += f"\n💡 **팜솔라 클라우드 IDE** - 실시간 파일 동기화"
            
            # 실제 메시지 전송은 봇 인스턴스를 통해 처리
            logger.info(f"📢 알림 준비: {message[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ 텔레그램 알림 전송 오류: {e}")
    
    def _handle_file_created(self, event: SyncEvent):
        """파일 생성 이벤트 처리"""
        logger.debug(f"📄 파일 생성 처리: {event.file_name}")
        # 추가 로직 구현 가능
    
    def _handle_file_modified(self, event: SyncEvent):
        """파일 수정 이벤트 처리"""
        logger.debug(f"✏️ 파일 수정 처리: {event.file_name}")
        # 추가 로직 구현 가능
    
    def _handle_file_deleted(self, event: SyncEvent):
        """파일 삭제 이벤트 처리"""
        logger.debug(f"🗑️ 파일 삭제 처리: {event.file_name}")
        # 추가 로직 구현 가능
    
    def get_sync_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """동기화 상태 조회"""
        try:
            if user_id:
                # 특정 사용자 상태
                is_active = user_id in self.active_users
                file_count = len(self.user_snapshots.get(user_id, {}))
                
                return {
                    "user_id": user_id,
                    "is_active": is_active,
                    "file_count": file_count,
                    "poll_interval": self.poll_interval
                }
            else:
                # 전체 시스템 상태
                return {
                    "active_users": len(self.active_users),
                    "total_files": sum(len(snapshots) for snapshots in self.user_snapshots.values()),
                    "poll_interval": self.poll_interval,
                    "stats": self.sync_stats
                }
                
        except Exception as e:
            logger.error(f"❌ 동기화 상태 조회 오류: {e}")
            return {"error": str(e)}
    
    def force_sync(self, user_id: str) -> bool:
        """강제 동기화 실행"""
        try:
            if user_id not in self.active_users:
                logger.warning(f"⚠️ 비활성 사용자 강제 동기화 요청: {user_id}")
                return False
            
            logger.info(f"🔄 강제 동기화 시작: {user_id}")
            self._poll_and_sync(user_id)
            logger.info(f"✅ 강제 동기화 완료: {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 강제 동기화 오류: {e}")
            return False
    
    def set_poll_interval(self, interval: int):
        """폴링 간격 설정"""
        if interval < 5:
            logger.warning("⚠️ 폴링 간격은 최소 5초 이상이어야 합니다")
            interval = 5
        
        self.poll_interval = interval
        logger.info(f"⏰ 폴링 간격 변경: {interval}초")
    
    def shutdown(self):
        """동기화 시스템 종료"""
        try:
            logger.info("🛑 동기화 시스템 종료 시작")
            
            # 모든 사용자 등록 해제
            active_users = list(self.active_users)
            for user_id in active_users:
                self.unregister_user(user_id)
            
            logger.info("✅ 동기화 시스템 종료 완료")
            
        except Exception as e:
            logger.error(f"❌ 동기화 시스템 종료 오류: {e}")

# 전역 동기화 매니저 인스턴스
polling_sync_manager = None

def initialize_polling_sync(bot_instance=None, poll_interval: int = 30) -> PollingSyncManager:
    """폴링 동기화 시스템 초기화"""
    global polling_sync_manager
    polling_sync_manager = PollingSyncManager(bot_instance, poll_interval)
    return polling_sync_manager

def get_polling_sync_manager() -> Optional[PollingSyncManager]:
    """폴링 동기화 매니저 인스턴스 반환"""
    return polling_sync_manager

if __name__ == "__main__":
    # 테스트용 실행
    manager = initialize_polling_sync(poll_interval=10)
    
    print("🔄 폴링 동기화 시스템 테스트 모드")
    print("Ctrl+C로 종료")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 시스템 종료 중...")
        manager.shutdown()
        print("✅ 종료 완료") 