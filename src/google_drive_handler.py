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
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload
import pickle

class GoogleDriveHandler:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.service = None
        self.credentials_file = 'config/google_credentials.json'
        # 로컬 토큰 파일 제거 - 메모리 기반 인증
        self.credentials_cache = None
        self.homework_folder_id = None
        
    def authenticate(self) -> bool:
        """구글 드라이브 인증 (메모리 기반)"""
        creds = self.credentials_cache
        
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
            
            # 메모리에 토큰 저장 (로컬 파일 저장 제거)
            self.credentials_cache = creds
        
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
            
            # 폴더 ID 메모리에 저장 (로컬 파일 저장 제거)
            
            return self.homework_folder_id
        except Exception as e:
            print(f"폴더 생성 오류: {e}")
            return None
    
    def get_homework_folder_id(self) -> str:
        """과제 폴더 ID 가져오기 (메모리 기반)"""
        if self.homework_folder_id:
            return self.homework_folder_id
            
        # 구글 드라이브에서 기존 폴더 검색
        try:
            if not self.service:
                if not self.authenticate():
                    return None
                    
            query = "name='AI_Solarbot_과제' and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query, fields='files(id, name)').execute()
            folders = results.get('files', [])
            
            if folders:
                self.homework_folder_id = folders[0]['id']
                return self.homework_folder_id
        except Exception as e:
            print(f"폴더 검색 오류: {e}")
        
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
    
    def read_file_content(self, file_id: str) -> Dict:
        """파일 내용 읽기 (텍스트 파일만)"""
        if not self.service:
            if not self.authenticate():
                return {"error": "인증 실패"}
        
        try:
            # 파일 정보 먼저 확인
            file_info = self.service.files().get(fileId=file_id, fields="name,mimeType").execute()
            mime_type = file_info.get('mimeType', '')
            file_name = file_info.get('name', '')
            
            # 구글 문서인 경우
            if mime_type == 'application/vnd.google-apps.document':
                request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
            # 구글 스프레드시트인 경우
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                request = self.service.files().export_media(fileId=file_id, mimeType='text/csv')
            # 일반 텍스트 파일인 경우
            elif 'text/' in mime_type or mime_type in ['application/json', 'application/javascript']:
                request = self.service.files().get_media(fileId=file_id)
            else:
                return {"error": f"지원하지 않는 파일 형식: {mime_type}"}
            
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # 내용을 문자열로 변환
            content = file_content.getvalue().decode('utf-8')
            
            return {
                "success": True,
                "content": content,
                "file_name": file_name,
                "mime_type": mime_type,
                "size": len(content)
            }
            
        except Exception as e:
            return {"error": f"파일 읽기 실패: {str(e)}"}
    
    def update_file_content(self, file_id: str, new_content: str) -> Dict:
        """파일 내용 수정"""
        if not self.service:
            if not self.authenticate():
                return {"error": "인증 실패"}
        
        try:
            # 파일 정보 확인
            file_info = self.service.files().get(fileId=file_id, fields="name,mimeType").execute()
            mime_type = file_info.get('mimeType', '')
            
            # 구글 문서는 직접 수정 불가, 일반 텍스트 파일만 수정 가능
            if mime_type == 'application/vnd.google-apps.document':
                return {"error": "구글 문서는 직접 수정할 수 없습니다. 새 파일로 업로드하세요."}
            
            # 임시 파일 생성
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(new_content)
                temp_path = temp_file.name
            
            try:
                # 파일 업데이트
                media = MediaFileUpload(temp_path, mimetype='text/plain')
                updated_file = self.service.files().update(
                    fileId=file_id,
                    media_body=media,
                    fields='id,name,webViewLink,modifiedTime'
                ).execute()
                
                return {
                    "success": True,
                    "file_id": updated_file.get('id'),
                    "file_name": updated_file.get('name'),
                    "web_link": updated_file.get('webViewLink'),
                    "modified_time": updated_file.get('modifiedTime')
                }
                
            finally:
                # 임시 파일 삭제
                os.unlink(temp_path)
            
        except Exception as e:
            return {"error": f"파일 수정 실패: {str(e)}"}
    
    def create_text_file(self, content: str, file_name: str, folder_id: str = None) -> Dict:
        """텍스트 파일 생성"""
        if not self.service:
            if not self.authenticate():
                return {"error": "인증 실패"}
        
        try:
            if not folder_id:
                folder_id = self.get_homework_folder_id()
            
            # 임시 파일 생성
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id] if folder_id else []
                }
                
                media = MediaFileUpload(temp_path, mimetype='text/plain')
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,webViewLink,size'
                ).execute()
                
                # 공유 설정
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
                
            finally:
                # 임시 파일 삭제
                os.unlink(temp_path)
            
        except Exception as e:
            return {"error": f"파일 생성 실패: {str(e)}"}
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> Dict:
        """폴더 생성"""
        if not self.service:
            if not self.authenticate():
                return {"error": "인증 실패"}
        
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(body=folder_metadata, fields='id,name,webViewLink').execute()
            
            # 공유 설정
            self.service.permissions().create(
                fileId=folder.get('id'),
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            return {
                "success": True,
                "folder_id": folder.get('id'),
                "folder_name": folder.get('name'),
                "web_link": folder.get('webViewLink')
            }
            
        except Exception as e:
            return {"error": f"폴더 생성 실패: {str(e)}"}
    
    def read_file_content(self, file_id: str) -> Dict:
        """파일 내용 읽기 (텍스트 파일만)"""
        if not self.service:
            if not self.authenticate():
                return {"error": "인증 실패"}
        
        try:
            # 파일 정보 먼저 확인
            file_info = self.service.files().get(fileId=file_id, fields="name,mimeType,size").execute()
            file_name = file_info.get('name', '')
            mime_type = file_info.get('mimeType', '')
            file_size = int(file_info.get('size', 0))
            
            # 파일 크기 제한 (10MB)
            if file_size > 10 * 1024 * 1024:
                return {"error": "파일이 너무 큽니다 (10MB 제한)"}
            
            # 텍스트 파일 여부 확인
            text_mimes = [
                'text/plain',
                'text/markdown', 
                'text/csv',
                'application/json',
                'text/html',
                'text/css',
                'text/javascript',
                'application/javascript'
            ]
            
            # Google Docs/Sheets/Slides는 특별 처리
            if mime_type == 'application/vnd.google-apps.document':
                # Google Docs를 텍스트로 내보내기
                request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # Google Sheets를 CSV로 내보내기
                request = self.service.files().export_media(fileId=file_id, mimeType='text/csv')
            elif mime_type in text_mimes or file_name.endswith(('.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.csv')):
                # 일반 텍스트 파일
                request = self.service.files().get_media(fileId=file_id)
            else:
                return {"error": f"지원하지 않는 파일 형식입니다: {mime_type}"}
            
            # 파일 내용 다운로드
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # 텍스트로 디코딩
            try:
                content = file_content.getvalue().decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = file_content.getvalue().decode('cp949')  # 한글 윈도우 인코딩
                except UnicodeDecodeError:
                    content = file_content.getvalue().decode('utf-8', errors='ignore')
            
            return {
                "success": True,
                "file_name": file_name,
                "mime_type": mime_type,
                "size": file_size,
                "content": content[:50000]  # 50KB 제한으로 자르기
            }
            
        except Exception as e:
            return {"error": f"파일 읽기 실패: {str(e)}"}
    
    def analyze_file_with_ai(self, file_id: str, ai_handler, user_id: str, analysis_type: str = "general") -> Dict:
        """AI를 사용하여 파일 분석"""
        # 파일 내용 읽기
        file_result = self.read_file_content(file_id)
        
        if "error" in file_result:
            return file_result
        
        file_name = file_result["file_name"]
        content = file_result["content"]
        
        # 분석 유형별 프롬프트
        prompts = {
            "general": f"""
다음 파일을 분석해주세요:

파일명: {file_name}
내용:
{content}

분석 결과를 다음 형식으로 제공해주세요:
1. 파일 개요
2. 주요 내용 요약
3. 특이사항 또는 문제점
4. 개선 제안 (필요시)
""",
            "homework": f"""
다음 과제 파일을 검토해주세요:

파일명: {file_name}
내용:
{content}

과제 검토 결과:
1. 과제 완성도 (%)
2. 잘된 점
3. 부족한 점
4. 개선 방향
5. 점수 (100점 만점)
""",
            "report": f"""
다음 업무보고서를 검토해주세요:

파일명: {file_name}
내용:
{content}

보고서 검토 결과:
1. 필수 항목 체크
2. 내용의 명확성
3. 누락된 정보
4. 전체적인 평가
5. 수정 제안
""",
            "code": f"""
다음 코드 파일을 검토해주세요:

파일명: {file_name}
내용:
{content}

코드 리뷰 결과:
1. 코드 품질
2. 잠재적 문제점
3. 성능 개선 제안
4. 보안 이슈 (있다면)
5. 전체 평가
"""
        }
        
        try:
            prompt = prompts.get(analysis_type, prompts["general"])
            analysis = ai_handler.chat_with_ai(prompt, user_id)
            
            return {
                "success": True,
                "file_name": file_name,
                "analysis_type": analysis_type,
                "analysis": analysis
            }
            
        except Exception as e:
            return {"error": f"AI 분석 실패: {str(e)}"}

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