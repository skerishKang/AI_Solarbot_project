"""
Email Manager - Gmail API 통합 이메일 관리 시스템 (완전 클라우드 기반)
구글 드라이브 전용 - 로컬 파일 접근 없음
"""

import os
import json
import base64
import email
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

logger = logging.getLogger(__name__)

class EmailManager:
    """Gmail API를 사용한 이메일 관리 클래스 (완전 클라우드 기반)"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, credentials_file: str = 'credentials.json'):
        self.credentials_file = credentials_file
        self.service = None
        self.last_check_time = {}  # 사용자별 마지막 확인 시간
        self.monitoring_enabled = {}  # 사용자별 모니터링 활성화 상태
        # 완전 메모리 기반 - 토큰을 메모리에만 저장
        self.user_credentials = {}  # 사용자별 인증 정보 메모리 저장
        self.user_email_settings = {}  # 사용자별 이메일 설정
        
    def authenticate_gmail(self, user_id: str) -> bool:
        """Gmail API 인증 (메모리 기반)"""
        try:
            creds = None
            
            # 메모리에서 기존 인증 정보 확인
            if user_id in self.user_credentials:
                creds = self.user_credentials[user_id]
            
            # 토큰이 유효하지 않으면 새로 인증
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # 메모리에 토큰 저장 (로컬 파일 저장 제거)
                self.user_credentials[user_id] = creds
            
            self.service = build('gmail', 'v1', credentials=creds)
            return True
            
        except Exception as e:
            logger.error(f"Gmail 인증 실패: {e}")
            return False
    
    def get_user_email(self, user_id: str) -> str:
        """사용자의 Gmail 주소 가져오기"""
        try:
            if not self.service:
                if not self.authenticate_gmail(user_id):
                    return None
            
            profile = self.service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
            
        except Exception as e:
            logger.error(f"사용자 이메일 가져오기 실패: {e}")
            return None
    
    def check_new_emails(self, user_id: str) -> List[Dict]:
        """새로운 이메일 확인"""
        try:
            if not self.service:
                if not self.authenticate_gmail(user_id):
                    return []
            
            # 마지막 확인 시간 이후의 이메일만 가져오기
            last_check = self.last_check_time.get(user_id, datetime.now() - timedelta(hours=1))
            query = f'is:unread after:{last_check.strftime("%Y/%m/%d")}'
            
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=10).execute()
            
            messages = results.get('messages', [])
            new_emails = []
            
            for message in messages:
                email_data = self.get_email_details(message['id'])
                if email_data:
                    new_emails.append(email_data)
            
            # 마지막 확인 시간 업데이트
            self.last_check_time[user_id] = datetime.now()
            return new_emails
            
        except Exception as e:
            logger.error(f"새 이메일 확인 실패: {e}")
            return []
    
    def get_email_details(self, message_id: str) -> Dict:
        """이메일 상세 정보 가져오기"""
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full').execute()
            
            headers = message['payload'].get('headers', [])
            
            # 헤더에서 정보 추출
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '제목 없음')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '발신자 없음')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            message_id_header = next((h['value'] for h in headers if h['name'] == 'Message-ID'), '')
            
            # 본문 추출
            body = self.extract_email_body(message['payload'])
            
            return {
                'id': message_id,
                'message_id': message_id_header,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body[:500] + '...' if len(body) > 500 else body,  # 미리보기용 500자
                'full_body': body,
                'thread_id': message.get('threadId', '')
            }
            
        except Exception as e:
            logger.error(f"이메일 상세 정보 가져오기 실패: {e}")
            return None
    
    def extract_email_body(self, payload) -> str:
        """이메일 본문 추출"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                    # HTML 태그 제거 (간단한 버전)
                    body = re.sub('<[^<]+?>', '', html_body)
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body.strip()
    
    def send_reply(self, original_message_id: str, reply_text: str, user_id: str) -> bool:
        """이메일 답장 보내기"""
        try:
            if not self.service:
                if not self.authenticate_gmail(user_id):
                    return False
            
            # 원본 메시지 가져오기
            original = self.service.users().messages().get(
                userId='me', id=original_message_id, format='full').execute()
            
            headers = original['payload'].get('headers', [])
            
            # 원본 정보 추출
            original_subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            original_from = next((h['value'] for h in headers if h['name'] == 'From'), '')
            original_message_id = next((h['value'] for h in headers if h['name'] == 'Message-ID'), '')
            
            # 발신자 이메일 주소만 추출
            sender_email = re.findall(r'<(.+?)>', original_from)
            if sender_email:
                to_email = sender_email[0]
            else:
                to_email = original_from
            
            # 답장 제목 생성
            reply_subject = original_subject
            if not reply_subject.startswith('Re:'):
                reply_subject = f'Re: {reply_subject}'
            
            # 답장 메시지 생성
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = reply_subject
            message['In-Reply-To'] = original_message_id
            message['References'] = original_message_id
            
            # 본문 추가
            message.attach(MIMEText(reply_text, 'plain', 'utf-8'))
            
            # 메시지 인코딩
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # 답장 전송
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message, 'threadId': original.get('threadId', '')}
            ).execute()
            
            logger.info(f"답장 전송 성공: {send_result['id']}")
            return True
            
        except Exception as e:
            logger.error(f"답장 전송 실패: {e}")
            return False
    
    def generate_ai_reply(self, email_content: str, ai_handler, user_id: str) -> str:
        """AI를 사용하여 답장 생성"""
        try:
            prompt = f"""
다음 이메일에 대한 적절한 답장을 한국어로 작성해주세요.
정중하고 전문적인 톤으로 작성하되, 내용은 간결하게 해주세요.

원본 이메일:
{email_content}

답장을 작성할 때 고려사항:
1. 정중한 인사말로 시작
2. 원본 이메일의 내용에 대한 적절한 응답
3. 필요시 추가 정보 요청이나 다음 단계 제안
4. 정중한 마무리 인사

답장 내용만 작성해주세요:
"""
            
            response = ai_handler.chat_with_ai(prompt, user_id)
            return response
            
        except Exception as e:
            logger.error(f"AI 답장 생성 실패: {e}")
            return "죄송합니다. AI 답장 생성 중 오류가 발생했습니다."
    
    def mark_as_read(self, message_id: str, user_id: str) -> bool:
        """이메일을 읽음으로 표시"""
        try:
            if not self.service:
                if not self.authenticate_gmail(user_id):
                    return False
            
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"읽음 표시 실패: {e}")
            return False
    
    def enable_email_monitoring(self, user_id: str) -> bool:
        """사용자의 이메일 모니터링 활성화"""
        try:
            if self.authenticate_gmail(user_id):
                self.user_email_settings[user_id] = {
                    'monitoring_enabled': True,
                    'last_check': datetime.now()
                }
                self.monitoring_enabled[user_id] = True
                return True
            return False
            
        except Exception as e:
            logger.error(f"이메일 모니터링 활성화 실패: {e}")
            return False
    
    def disable_email_monitoring(self, user_id: str):
        """사용자의 이메일 모니터링 비활성화"""
        if user_id in self.user_email_settings:
            self.user_email_settings[user_id]['monitoring_enabled'] = False
            self.monitoring_enabled[user_id] = False
    
    def is_monitoring_enabled(self, user_id: str) -> bool:
        """사용자의 이메일 모니터링 상태 확인"""
        return self.monitoring_enabled.get(user_id, False) 