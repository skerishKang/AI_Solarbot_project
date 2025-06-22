"""
구글 드라이브 연동 모듈
- 파일 업로드/다운로드
- 폴더 관리
- 권한 설정
"""

import os
import io
import json
from typing import Optional, List, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import pickle

class GoogleDriveHandler:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.service = None
        self.credentials_file = 'config/google_credentials.json'
        self.token_file = 'config/google_token.pickle'
        self.homework_folder_id = None
        
    def authenticate(self) -> bool:
        """구글 드라이브 인증"""
        creds = None
        
        # 기존 토큰 로드
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # 토큰이 없거나 유효하지 않은 경우
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print("❌ Google API 인증 파일이 없습니다.")
                    print("📋 설정 방법:")
                    print("1. Google Cloud Console에서 프로젝트 생성")
                    print("2. Drive API 활성화")
                    print("3. OAuth 2.0 클라이언트 ID 생성")
                    print("4. credentials.json을 config/ 폴더에 저장")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 토큰 저장
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        return True
    
    def create_homework_folder(self) -> str:
        """과제 폴더 생성"""
        if not self.service:
            return None
            
        folder_metadata = {
            'name': 'AI_Solarbot_과제',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        try:
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            self.homework_folder_id = folder.get('id')
            
            # 폴더 ID 저장
            with open('config/drive_folder_id.txt', 'w') as f:
                f.write(self.homework_folder_id)
            
            return self.homework_folder_id
        except Exception as e:
            print(f"폴더 생성 오류: {e}")
            return None
    
    def get_homework_folder_id(self) -> str:
        """과제 폴더 ID 가져오기"""
        if self.homework_folder_id:
            return self.homework_folder_id
            
        # 저장된 폴더 ID 로드
        folder_id_file = 'config/drive_folder_id.txt'
        if os.path.exists(folder_id_file):
            with open(folder_id_file, 'r') as f:
                self.homework_folder_id = f.read().strip()
                return self.homework_folder_id
        
        # 폴더가 없으면 생성
        return self.create_homework_folder()
    
    def upload_file(self, file_path: str, file_name: str = None, folder_id: str = None) -> Dict:
        """파일 업로드"""
        if not self.service:
            if not self.authenticate():
                return {"error": "인증 실패"}
        
        if not os.path.exists(file_path):
            return {"error": "파일을 찾을 수 없습니다"}
        
        if not file_name:
            file_name = os.path.basename(file_path)
        
        if not folder_id:
            folder_id = self.get_homework_folder_id()
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id] if folder_id else []
        }
        
        try:
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,size'
            ).execute()
            
            # 공유 설정 (링크로 접근 가능)
            self.service.permissions().create(
                fileId=file.get('id'),
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            return {
                "success": True,
                "file_id": file.get('id'),
                "file_name": file.get('name'),
                "web_link": file.get('webViewLink'),
                "size": file.get('size')
            }
            
        except Exception as e:
            return {"error": f"업로드 실패: {str(e)}"}
    
    def download_file(self, file_id: str, save_path: str) -> Dict:
        """파일 다운로드"""
        if not self.service:
            if not self.authenticate():
                return {"error": "인증 실패"}
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            with open(save_path, 'wb') as f:
                f.write(file.getvalue())
            
            return {"success": True, "path": save_path}
            
        except Exception as e:
            return {"error": f"다운로드 실패: {str(e)}"}
    
    def list_files(self, folder_id: str = None, max_files: int = 50) -> List[Dict]:
        """파일 목록 조회"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            query = f"parents in '{folder_id}'" if folder_id else ""
            
            results = self.service.files().list(
                q=query,
                pageSize=max_files,
                fields="files(id,name,mimeType,size,createdTime,webViewLink)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            print(f"파일 목록 조회 오류: {e}")
            return []
    
    def search_files(self, keyword: str) -> List[Dict]:
        """파일 검색"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            query = f"name contains '{keyword}'"
            
            results = self.service.files().list(
                q=query,
                pageSize=20,
                fields="files(id,name,mimeType,size,createdTime,webViewLink)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            print(f"파일 검색 오류: {e}")
            return []
    
    def delete_file(self, file_id: str) -> Dict:
        """파일 삭제"""
        if not self.service:
            if not self.authenticate():
                return {"error": "인증 실패"}
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return {"success": True}
            
        except Exception as e:
            return {"error": f"삭제 실패: {str(e)}"}
    
    def get_file_info(self, file_id: str) -> Dict:
        """파일 정보 조회"""
        if not self.service:
            if not self.authenticate():
                return {"error": "인증 실패"}
        
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,createdTime,webViewLink,parents"
            ).execute()
            
            return file
            
        except Exception as e:
            return {"error": f"정보 조회 실패: {str(e)}"}

# 전역 인스턴스
drive_handler = GoogleDriveHandler()

def test_drive_connection() -> Dict:
    """구글 드라이브 연결 테스트"""
    try:
        if drive_handler.authenticate():
            # 테스트 파일 목록 조회
            files = drive_handler.list_files(max_files=1)
            return {
                "status": "connected",
                "message": "구글 드라이브 연결 성공",
                "files_count": len(files)
            }
        else:
            return {
                "status": "error",
                "message": "구글 드라이브 인증 실패"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"연결 오류: {str(e)}"
        } 