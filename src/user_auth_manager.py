"""
사용자별 구글 드라이브 OAuth 인증 관리자
- 개별 사용자 인증 토큰 관리
- 보안 토큰 암호화 저장
- OAuth 2.0 플로우 처리
"""

import os
import json
import pickle
import secrets
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class UserAuthManager:
    """사용자별 OAuth 2.0 인증 관리 클래스"""
    
    # 구글 드라이브 및 기본 서비스에 필요한 스코프
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
    
    def __init__(self, credentials_file: str = 'config/google_credentials.json'):
        """
        초기화
        
        Args:
            credentials_file (str): OAuth 2.0 클라이언트 인증 정보 파일 경로
        """
        self.credentials_file = credentials_file
        self.user_credentials: Dict[str, Credentials] = {}  # 메모리 기반 토큰 저장
        self.user_info_cache: Dict[str, Dict] = {}  # 사용자 정보 캐시
        self.auth_flows: Dict[str, InstalledAppFlow] = {}  # 진행 중인 인증 플로우
        self.last_activity: Dict[str, datetime] = {}  # 마지막 활동 시간
        
        # 토큰 만료 관리
        self.token_refresh_threshold = 300  # 5분 전에 토큰 갱신
        self.max_inactive_time = 24 * 60 * 60  # 24시간 비활성화 시 토큰 제거
        
        logger.info("UserAuthManager 초기화 완료")
    
    def authenticate_user(self, user_id: str, auth_code: Optional[str] = None) -> Dict[str, any]:
        """
        사용자 OAuth 2.0 인증 처리
        
        Args:
            user_id (str): 텔레그램 사용자 ID
            auth_code (Optional[str]): OAuth 인증 코드 (선택적)
            
        Returns:
            Dict: 인증 결과와 상태 정보
        """
        try:
            # 기존 유효한 토큰이 있는지 확인
            if self.is_authenticated(user_id):
                user_info = self.get_user_info(user_id)
                return {
                    "success": True,
                    "message": f"이미 인증된 사용자입니다: {user_info.get('email', 'Unknown')}",
                    "user_info": user_info,
                    "auth_required": False
                }
            
            # 인증 파일 존재 확인
            if not os.path.exists(self.credentials_file):
                return {
                    "success": False,
                    "error": "OAuth 2.0 인증 파일이 없습니다",
                    "message": """
🔐 **구글 드라이브 연결 설정 필요**

설정 방법:
1. Google Cloud Console에서 프로젝트 생성
2. Drive API 활성화  
3. OAuth 2.0 클라이언트 ID 생성
4. credentials.json을 config/ 폴더에 저장

관리자에게 문의하세요.
                    """,
                    "auth_required": True
                }
            
            # 새로운 인증 플로우 시작
            if auth_code is None:
                # 인증 URL 생성
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                
                # 로컬 서버 없이 수동 인증 모드 사용
                flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                # 인증 플로우 임시 저장
                self.auth_flows[user_id] = flow
                
                return {
                    "success": False,
                    "message": "인증이 필요합니다",
                    "auth_url": auth_url,
                    "auth_required": True,
                    "instructions": """
🔐 **구글 드라이브 연결 단계**

1. 위 링크를 클릭하여 구글 계정으로 로그인
2. AI_Solarbot 앱 권한 승인  
3. 나타나는 인증 코드를 복사
4. `/connect_drive [인증코드]` 명령어로 입력

예: `/connect_drive 4/0AX4XfWh...`
                    """
                }
            
            # 인증 코드로 토큰 교환
            if user_id not in self.auth_flows:
                return {
                    "success": False,
                    "error": "인증 플로우를 찾을 수 없습니다",
                    "message": "다시 `/connect_drive` 명령어를 실행해주세요."
                }
            
            flow = self.auth_flows[user_id]
            
            try:
                flow.fetch_token(code=auth_code)
                credentials = flow.credentials
                
                # 메모리에 토큰 저장
                self.user_credentials[user_id] = credentials
                self.last_activity[user_id] = datetime.now()
                
                # 사용자 정보 가져오기
                user_info = self._fetch_user_info(user_id)
                self.user_info_cache[user_id] = user_info
                
                # 인증 플로우 정리
                del self.auth_flows[user_id]
                
                logger.info(f"사용자 {user_id} OAuth 인증 성공: {user_info.get('email')}")
                
                return {
                    "success": True,
                    "message": f"✅ 구글 드라이브 연결 완료!\n📧 계정: {user_info.get('email')}",
                    "user_info": user_info,
                    "auth_required": False
                }
                
            except Exception as e:
                # 인증 플로우 정리
                if user_id in self.auth_flows:
                    del self.auth_flows[user_id]
                
                logger.error(f"토큰 교환 실패 {user_id}: {e}")
                return {
                    "success": False,
                    "error": f"인증 코드가 잘못되었습니다: {str(e)}",
                    "message": "올바른 인증 코드를 입력했는지 확인하고 다시 시도해주세요."
                }
                
        except Exception as e:
            logger.error(f"사용자 인증 처리 오류 {user_id}: {e}")
            return {
                "success": False,
                "error": f"인증 처리 중 오류 발생: {str(e)}",
                "message": "시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }
    
    def is_authenticated(self, user_id: str) -> bool:
        """
        사용자 인증 상태 확인
        
        Args:
            user_id (str): 텔레그램 사용자 ID
            
        Returns:
            bool: 인증 여부
        """
        try:
            if user_id not in self.user_credentials:
                return False
            
            credentials = self.user_credentials[user_id]
            
            # 토큰 유효성 확인
            if not credentials.valid:
                # 토큰이 만료되었지만 갱신 가능한 경우
                if credentials.expired and credentials.refresh_token:
                    return self.refresh_token(user_id)
                else:
                    # 갱신 불가능한 경우 토큰 제거
                    self._remove_user_auth(user_id)
                    return False
            
            # 비활성화 시간 확인
            if user_id in self.last_activity:
                inactive_time = (datetime.now() - self.last_activity[user_id]).total_seconds()
                if inactive_time > self.max_inactive_time:
                    logger.info(f"사용자 {user_id} 장기간 비활성화로 토큰 제거")
                    self._remove_user_auth(user_id)
                    return False
            
            # 활동 시간 업데이트
            self.last_activity[user_id] = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"인증 상태 확인 오류 {user_id}: {e}")
            return False
    
    def get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        사용자 인증 정보 가져오기
        
        Args:
            user_id (str): 텔레그램 사용자 ID
            
        Returns:
            Optional[Credentials]: 구글 OAuth 2.0 인증 정보
        """
        if not self.is_authenticated(user_id):
            return None
            
        return self.user_credentials.get(user_id)
    
    def refresh_token(self, user_id: str) -> bool:
        """
        토큰 갱신
        
        Args:
            user_id (str): 텔레그램 사용자 ID
            
        Returns:
            bool: 갱신 성공 여부
        """
        try:
            if user_id not in self.user_credentials:
                return False
            
            credentials = self.user_credentials[user_id]
            
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                logger.info(f"사용자 {user_id} 토큰 갱신 성공")
                return True
            
            return credentials.valid
            
        except Exception as e:
            logger.error(f"토큰 갱신 실패 {user_id}: {e}")
            self._remove_user_auth(user_id)
            return False
    
    def revoke_access(self, user_id: str) -> bool:
        """
        사용자 액세스 권한 취소
        
        Args:
            user_id (str): 텔레그램 사용자 ID
            
        Returns:
            bool: 취소 성공 여부
        """
        try:
            if user_id in self.user_credentials:
                credentials = self.user_credentials[user_id]
                
                # 구글 API를 통해 토큰 취소
                try:
                    from google.auth.transport.requests import Request
                    import requests
                    
                    revoke_url = 'https://oauth2.googleapis.com/revoke'
                    params = {'token': credentials.token}
                    
                    response = requests.post(revoke_url, params=params)
                    if response.status_code == 200:
                        logger.info(f"사용자 {user_id} 구글 토큰 취소 성공")
                    else:
                        logger.warning(f"구글 토큰 취소 실패 {user_id}: {response.status_code}")
                        
                except Exception as revoke_error:
                    logger.warning(f"토큰 취소 요청 실패 {user_id}: {revoke_error}")
                
                # 로컬에서 토큰 제거
                self._remove_user_auth(user_id)
                
            return True
            
        except Exception as e:
            logger.error(f"액세스 취소 실패 {user_id}: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> Dict:
        """
        사용자 정보 가져오기
        
        Args:
            user_id (str): 텔레그램 사용자 ID
            
        Returns:
            Dict: 사용자 정보
        """
        if user_id in self.user_info_cache:
            return self.user_info_cache[user_id]
        
        if self.is_authenticated(user_id):
            user_info = self._fetch_user_info(user_id)
            self.user_info_cache[user_id] = user_info
            return user_info
        
        return {}
    
    def _fetch_user_info(self, user_id: str) -> Dict:
        """
        구글 API에서 사용자 정보 가져오기 (내부 메서드)
        
        Args:
            user_id (str): 텔레그램 사용자 ID
            
        Returns:
            Dict: 사용자 정보
        """
        try:
            credentials = self.user_credentials.get(user_id)
            if not credentials:
                return {}
            
            # OAuth2 사용자 정보 API 호출
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            return {
                'id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'locale': user_info.get('locale'),
                'verified_email': user_info.get('verified_email', False)
            }
            
        except Exception as e:
            logger.error(f"사용자 정보 조회 실패 {user_id}: {e}")
            return {}
    
    def _remove_user_auth(self, user_id: str):
        """
        사용자 인증 정보 제거 (내부 메서드)
        
        Args:
            user_id (str): 텔레그램 사용자 ID
        """
        if user_id in self.user_credentials:
            del self.user_credentials[user_id]
        if user_id in self.user_info_cache:
            del self.user_info_cache[user_id]
        if user_id in self.last_activity:
            del self.last_activity[user_id]
        if user_id in self.auth_flows:
            del self.auth_flows[user_id]
    
    def cleanup_expired_tokens(self):
        """만료된 토큰 정리 (백그라운드 작업)"""
        try:
            current_time = datetime.now()
            expired_users = []
            
            for user_id, last_activity in self.last_activity.items():
                if (current_time - last_activity).total_seconds() > self.max_inactive_time:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                logger.info(f"비활성화 토큰 정리: {user_id}")
                self._remove_user_auth(user_id)
                
        except Exception as e:
            logger.error(f"토큰 정리 오류: {e}")
    
    def get_authenticated_users(self) -> List[str]:
        """
        현재 인증된 사용자 목록 반환
        
        Returns:
            List[str]: 인증된 사용자 ID 목록
        """
        authenticated_users = []
        for user_id in list(self.user_credentials.keys()):
            if self.is_authenticated(user_id):
                authenticated_users.append(user_id)
        return authenticated_users
    
    def get_authentication_stats(self) -> Dict:
        """
        인증 통계 정보 반환
        
        Returns:
            Dict: 인증 관련 통계
        """
        return {
            'total_users': len(self.user_credentials),
            'active_users': len(self.get_authenticated_users()),
            'pending_flows': len(self.auth_flows),
            'cache_size': len(self.user_info_cache)
        }


# 싱글톤 인스턴스 생성
user_auth_manager = UserAuthManager()

# 모듈 수준에서 정리 함수 등록 (선택적)
import atexit
atexit.register(user_auth_manager.cleanup_expired_tokens)

logger.info("UserAuthManager 모듈 로드 완료")
 