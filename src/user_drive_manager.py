"""
user_drive_manager.py - 사용자별 구글 드라이브 관리 (완전 클라우드 기반)
구글 드라이브 전용 - 로컬 파일 접근 없음
"""

import json
import io
import time
from datetime import datetime
from typing import Dict, List, Optional
from google_drive_handler import drive_handler
from workspace_template import WorkspaceTemplate

class UserDriveManager:
    def __init__(self):
        # 완전 클라우드 기반: 구글 드라이브에만 데이터 저장
        self.user_manager_folder_name = "팜솔라_사용자관리_시스템"
        self.user_folders_file_name = "user_folders.json"
        self.user_folders = None
    
    def ensure_user_manager_folder(self) -> str:
        """사용자 관리 폴더 확인/생성"""
        try:
            if not drive_handler.authenticate():
                raise Exception("구글 드라이브 인증 실패")
            
            # 기존 폴더 검색
            query = f"name='{self.user_manager_folder_name}' and mimeType='application/vnd.google-apps.folder'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            
            # 폴더 생성
            folder_metadata = {
                'name': self.user_manager_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_handler.service.files().create(body=folder_metadata, fields='id').execute()
            return folder.get('id')
            
        except Exception as e:
            raise Exception(f"사용자 관리 폴더 생성 실패: {str(e)}")

    def load_user_folders(self) -> Dict:
        """구글 드라이브에서 사용자 폴더 정보 로드"""
        if self.user_folders is not None:
            return self.user_folders
            
        try:
            folder_id = self.ensure_user_manager_folder()
            
            # 데이터 파일 검색
            query = f"name='{self.user_folders_file_name}' and parents in '{folder_id}'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                # 기존 파일 읽기
                file_id = files[0]['id']
                content = drive_handler.service.files().get_media(fileId=file_id).execute()
                self.user_folders = json.loads(content.decode('utf-8'))
                return self.user_folders
            else:
                # 빈 데이터 반환
                self.user_folders = {}
                return self.user_folders
                
        except Exception as e:
            print(f"사용자 폴더 정보 로드 실패: {e}")
            self.user_folders = {}
            return self.user_folders
    
    def save_user_folders(self):
        """구글 드라이브에 사용자 폴더 정보 저장"""
        if self.user_folders is None:
            return
            
        try:
            folder_id = self.ensure_user_manager_folder()
            content = json.dumps(self.user_folders, ensure_ascii=False, indent=2)
            
            # 기존 파일 검색
            query = f"name='{self.user_folders_file_name}' and parents in '{folder_id}'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                # 기존 파일 업데이트
                file_id = files[0]['id']
                media_body = drive_handler.MediaIoBaseUpload(
                    io.BytesIO(content.encode('utf-8')),
                    mimetype='application/json'
                )
                drive_handler.service.files().update(
                    fileId=file_id,
                    media_body=media_body
                ).execute()
            else:
                # 새 파일 생성
                file_metadata = {
                    'name': self.user_folders_file_name,
                    'parents': [folder_id]
                }
                media_body = drive_handler.MediaIoBaseUpload(
                    io.BytesIO(content.encode('utf-8')),
                    mimetype='application/json'
                )
                drive_handler.service.files().create(
                    body=file_metadata,
                    media_body=media_body,
                    fields='id'
                ).execute()
                
        except Exception as e:
            print(f"사용자 폴더 정보 저장 실패: {e}")
    
    def get_user_folder(self, user_id: str, user_name: str) -> Dict:
        """사용자 전용 폴더 가져오기 (없으면 생성)"""
        user_id = str(user_id)
        
        # 기존 폴더가 있으면 반환
        user_folders = self.load_user_folders()
        if user_id in user_folders:
            folder_info = user_folders[user_id]
            # 폴더가 실제로 존재하는지 확인
            if self.verify_folder_exists(folder_info['folder_id']):
                return folder_info
            else:
                # 폴더가 삭제되었으면 새로 생성
                del user_folders[user_id]
                self.user_folders = user_folders
        
        # 새 폴더 생성
        return self.create_user_folder(user_id, user_name)
    
    def create_user_folder(self, user_id: str, user_name: str) -> Dict:
        """사용자 전용 폴더 생성 및 워크스페이스 자동 설정"""
        if not drive_handler.authenticate():
            return {"error": "구글 드라이브 인증 실패"}
        
        # 메인 폴더 ID 가져오기
        main_folder_id = drive_handler.get_homework_folder_id()
        if not main_folder_id:
            return {"error": "메인 폴더 생성 실패"}
        
        # 사용자 폴더 생성
        folder_name = f"사용자_{user_name}_{user_id}"
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [main_folder_id]
        }
        
        try:
            folder = drive_handler.service.files().create(
                body=folder_metadata, 
                fields='id,name,webViewLink'
            ).execute()
            
            folder_id = folder.get('id')
            folder_link = folder.get('webViewLink')
            
            # 사용자에게 편집 권한 부여
            drive_handler.service.permissions().create(
                fileId=folder_id,
                body={
                    'role': 'writer',  # 편집 권한
                    'type': 'anyone'   # 링크로 접근 가능
                }
            ).execute()
            
            # 팜솔라 워크스페이스 자동 생성
            workspace_result = self.create_workspace_structure(folder_id, user_name)
            
            # 사용자 정보 저장
            folder_info = {
                'folder_id': folder_id,
                'folder_name': folder_name,
                'folder_link': folder_link,
                'user_name': user_name,
                'created_at': str(datetime.now()),
                'file_count': 0,
                'workspace_created': workspace_result.get('success', False),
                'workspace_files': workspace_result.get('created_files', 0)
            }
            
            user_folders = self.load_user_folders()
            user_folders[str(user_id)] = folder_info
            self.user_folders = user_folders
            self.save_user_folders()
            
            success_message = f"✅ {user_name}님의 전용 폴더가 생성되었습니다!"
            if workspace_result.get('success'):
                success_message += f"\n🎓 팜솔라 교과서 워크스페이스도 자동으로 설정되었습니다! ({workspace_result.get('created_files', 0)}개 파일)"
            
            return {
                "success": True,
                "folder_info": folder_info,
                "message": success_message,
                "workspace_details": workspace_result
            }
            
        except Exception as e:
            return {"error": f"폴더 생성 실패: {str(e)}"}
    
    def create_workspace_structure(self, parent_folder_id: str, user_name: str) -> Dict:
        """사용자 워크스페이스 구조 생성 (강화된 오류 처리)"""
        workspace_template = WorkspaceTemplate()
        structure = workspace_template.base_structure["팜솔라_교과서"]
        
        created_folders = []
        created_files = []
        failed_operations = []
        progress_callback = None
        
        try:
            # 1단계: 메인 워크스페이스 폴더 생성
            if progress_callback:
                progress_callback("📁 메인 워크스페이스 폴더 생성 중...", 10)
            
            main_folder = self.create_drive_folder_with_retry(parent_folder_id, "팜솔라_교과서")
            if not main_folder.get('success'):
                raise Exception(f"메인 폴더 생성 실패: {main_folder.get('error')}")
            
            main_folder_id = main_folder['folder_id']
            created_folders.append(main_folder)
            
            # 2단계: 서브폴더 생성 (진행률 추적)
            total_operations = self._count_total_operations(structure)
            current_operation = 0
            
            for folder_name, folder_config in structure["subfolders"].items():
                try:
                    if progress_callback:
                        progress = 10 + (current_operation / total_operations) * 70
                        progress_callback(f"📂 {folder_name} 폴더 생성 중...", int(progress))
                    
                    # 서브폴더 생성
                    sub_folder = self.create_drive_folder_with_retry(main_folder_id, folder_name)
                    if sub_folder.get('success'):
                        created_folders.append(sub_folder)
                        sub_folder_id = sub_folder['folder_id']
                        
                        # 템플릿 파일 생성
                        if "template_files" in folder_config:
                            for template_file in folder_config["template_files"]:
                                try:
                                    content = workspace_template.get_advanced_template_content(
                                        template_file.replace('.md', '')
                                    )
                                    file_result = self.create_drive_file_with_retry(
                                        sub_folder_id, template_file, content
                                    )
                                    if file_result.get('success'):
                                        created_files.append(file_result)
                                    else:
                                        failed_operations.append({
                                            'type': 'file',
                                            'name': template_file,
                                            'error': file_result.get('error')
                                        })
                                except Exception as e:
                                    failed_operations.append({
                                        'type': 'file',
                                        'name': template_file,
                                        'error': str(e)
                                    })
                        
                        # 중첩 서브폴더 처리
                        if "subfolders" in folder_config:
                            nested_result = self._create_nested_folders(
                                sub_folder_id, folder_config["subfolders"], 
                                workspace_template, progress_callback
                            )
                            created_folders.extend(nested_result['folders'])
                            created_files.extend(nested_result['files'])
                            failed_operations.extend(nested_result['failed'])
                    else:
                        failed_operations.append({
                            'type': 'folder',
                            'name': folder_name,
                            'error': sub_folder.get('error')
                        })
                    
                    current_operation += 1
                    
                except Exception as e:
                    failed_operations.append({
                        'type': 'folder',
                        'name': folder_name,
                        'error': str(e)
                    })
            
            # 3단계: 코스별 구조 생성
            if progress_callback:
                progress_callback("📚 코스별 구조 생성 중...", 80)
            
            course_results = self._create_course_structures(main_folder_id, progress_callback)
            created_files += course_results['created_files']
            failed_operations.extend(course_results['failed_operations'])
            
            # 4단계: 완료 및 검증
            if progress_callback:
                progress_callback("✅ 워크스페이스 생성 완료!", 100)
            
            # 생성 결과 검증
            success_rate = self._calculate_success_rate(created_folders, created_files, failed_operations)
            
            result = {
                "success": True,
                "main_folder_id": main_folder_id,
                "main_folder_link": main_folder['folder_link'],
                "created_folders": len(created_folders),
                "created_files": len(created_files),
                "failed_operations": len(failed_operations),
                "success_rate": success_rate,
                "details": {
                    "folders": created_folders,
                    "files": created_files[:10],  # 처음 10개만 표시
                    "total_files": len(created_files)
                }
            }
            
            # 실패한 작업이 있으면 복구 시도
            if failed_operations:
                result["recovery_attempted"] = self._attempt_recovery(failed_operations, main_folder_id)
                result["failed_details"] = failed_operations[:5]  # 처음 5개 실패만 표시
            
            return result
            
        except Exception as e:
            # 전체 실패 시 롤백 시도
            if created_folders or created_files:
                rollback_result = self._rollback_workspace(created_folders, created_files)
                return {
                    "error": f"워크스페이스 생성 실패: {str(e)}",
                    "rollback_attempted": rollback_result.get('attempted', False),
                    "rollback_success": rollback_result.get('success', False),
                    "partial_cleanup": rollback_result.get('partial_cleanup', [])
                }
            else:
                return {"error": f"워크스페이스 생성 실패: {str(e)}"}
    
    def create_drive_folder_with_retry(self, parent_id: str, folder_name: str, max_retries: int = 3) -> Dict:
        """재시도 기능이 있는 폴더 생성"""
        for attempt in range(max_retries):
            try:
                result = self.create_drive_folder(parent_id, folder_name)
                if result.get('success'):
                    return result
                
                # 실패 시 잠시 대기 후 재시도
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # 점진적 대기
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    return {"error": f"폴더 생성 최종 실패 (시도 {max_retries}회): {str(e)}"}
                time.sleep(1 * (attempt + 1))
        
        return {"error": f"폴더 생성 실패: 최대 재시도 횟수 초과"}

    def create_drive_file_with_retry(self, parent_id: str, file_name: str, content: str, max_retries: int = 3) -> Dict:
        """재시도 기능이 있는 파일 생성"""
        for attempt in range(max_retries):
            try:
                result = self.create_drive_file(parent_id, file_name, content)
                if result.get('success'):
                    return result
                
                # 실패 시 잠시 대기 후 재시도
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    return {"error": f"파일 생성 최종 실패 (시도 {max_retries}회): {str(e)}"}
                time.sleep(1 * (attempt + 1))
        
        return {"error": f"파일 생성 실패: 최대 재시도 횟수 초과"}

    def _count_total_operations(self, structure: Dict) -> int:
        """전체 작업 수 계산"""
        total = 0
        if "subfolders" in structure:
            for folder_config in structure["subfolders"].values():
                total += 1  # 폴더 생성
                if "template_files" in folder_config:
                    total += len(folder_config["template_files"])  # 파일 생성
                if "subfolders" in folder_config:
                    total += self._count_total_operations(folder_config)  # 중첩 폴더
        return total

    def _create_nested_folders(self, parent_id: str, subfolders: Dict, template: 'WorkspaceTemplate', progress_callback) -> Dict:
        """중첩 폴더 구조 생성"""
        created_folders = []
        created_files = []
        failed_operations = []
        
        for folder_name, folder_config in subfolders.items():
            try:
                folder_result = self.create_drive_folder_with_retry(parent_id, folder_name)
                if folder_result.get('success'):
                    created_folders.append(folder_result)
                    folder_id = folder_result['folder_id']
                    
                    # 템플릿 파일 생성
                    if "template_files" in folder_config:
                        for template_file in folder_config["template_files"]:
                            try:
                                content = template.get_advanced_template_content(
                                    template_file.replace('.md', '').replace('.py', '').replace('.txt', '')
                                )
                                file_result = self.create_drive_file_with_retry(folder_id, template_file, content)
                                if file_result.get('success'):
                                    created_files.append(file_result)
                                else:
                                    failed_operations.append({
                                        'type': 'file',
                                        'name': template_file,
                                        'error': file_result.get('error')
                                    })
                            except Exception as e:
                                failed_operations.append({
                                    'type': 'file',
                                    'name': template_file,
                                    'error': str(e)
                                })
                else:
                    failed_operations.append({
                        'type': 'folder',
                        'name': folder_name,
                        'error': folder_result.get('error')
                    })
            except Exception as e:
                failed_operations.append({
                    'type': 'folder',
                    'name': folder_name,
                    'error': str(e)
                })
        
        return {
            'folders': created_folders,
            'files': created_files,
            'failed': failed_operations
        }

    def _create_course_structures(self, main_folder_id: str, progress_callback) -> Dict:
        """코스별 구조 생성 (12주/1년/6주)"""
        created_files = []
        failed_operations = []
        
        courses = [
            ("12주과정", 12, 3),  # 12주 과정, 처음 3주만 생성
            ("1년과정", 52, 4),   # 1년 과정, 처음 4주만 생성
            ("6주과정", 6, 6)     # 6주 과정, 전체 생성
        ]
        
        for course_name, total_weeks, create_weeks in courses:
            try:
                # 코스 폴더 찾기
                course_folder_id = None
                files = drive_handler.list_files(main_folder_id)
                for file in files:
                    if file['name'] == course_name and file['mimeType'] == 'application/vnd.google-apps.folder':
                        course_folder_id = file['id']
                        break
                
                if course_folder_id:
                    created_count = self.create_course_structure(course_folder_id, total_weeks, create_weeks)
                    created_files.extend([{"course": course_name, "files": created_count}])
                else:
                    failed_operations.append({
                        'type': 'course',
                        'name': course_name,
                        'error': '코스 폴더를 찾을 수 없음'
                    })
            except Exception as e:
                failed_operations.append({
                    'type': 'course',
                    'name': course_name,
                    'error': str(e)
                })
        
        return {
            'created_files': created_files,
            'failed_operations': failed_operations
        }

    def _calculate_success_rate(self, folders: list, files: list, failed: list) -> float:
        """성공률 계산"""
        total_operations = len(folders) + len(files) + len(failed)
        successful_operations = len(folders) + len(files)
        
        if total_operations == 0:
            return 0.0
        
        return round((successful_operations / total_operations) * 100, 2)

    def _attempt_recovery(self, failed_operations: list, main_folder_id: str) -> Dict:
        """실패한 작업 복구 시도"""
        recovery_results = []
        
        for operation in failed_operations[:3]:  # 처음 3개만 복구 시도
            try:
                if operation['type'] == 'folder':
                    result = self.create_drive_folder_with_retry(main_folder_id, operation['name'], max_retries=2)
                    recovery_results.append({
                        'operation': operation,
                        'recovery_success': result.get('success', False)
                    })
                elif operation['type'] == 'file':
                    # 파일 복구는 더 복잡하므로 간단한 기본 내용으로 생성
                    basic_content = f"# {operation['name']}\n\n이 파일은 자동 복구로 생성되었습니다.\n내용을 추가해주세요."
                    result = self.create_drive_file_with_retry(main_folder_id, operation['name'], basic_content, max_retries=2)
                    recovery_results.append({
                        'operation': operation,
                        'recovery_success': result.get('success', False)
                    })
            except Exception as e:
                recovery_results.append({
                    'operation': operation,
                    'recovery_success': False,
                    'recovery_error': str(e)
                })
        
        return {
            'attempted': len(recovery_results),
            'successful': sum(1 for r in recovery_results if r.get('recovery_success')),
            'results': recovery_results
        }

    def _rollback_workspace(self, created_folders: list, created_files: list) -> Dict:
        """워크스페이스 롤백 (생성된 폴더/파일 삭제)"""
        rollback_results = {
            'attempted': True,
            'success': False,
            'partial_cleanup': [],
            'failed_cleanup': []
        }
        
        try:
            # 파일 먼저 삭제
            for file_info in created_files:
                try:
                    if 'file_id' in file_info:
                        drive_handler.service.files().delete(fileId=file_info['file_id']).execute()
                        rollback_results['partial_cleanup'].append(f"파일: {file_info.get('file_name', 'Unknown')}")
                except Exception as e:
                    rollback_results['failed_cleanup'].append(f"파일 삭제 실패: {file_info.get('file_name', 'Unknown')} - {str(e)}")
            
            # 폴더 삭제 (역순으로)
            for folder_info in reversed(created_folders):
                try:
                    if 'folder_id' in folder_info:
                        drive_handler.service.files().delete(fileId=folder_info['folder_id']).execute()
                        rollback_results['partial_cleanup'].append(f"폴더: {folder_info.get('folder_name', 'Unknown')}")
                except Exception as e:
                    rollback_results['failed_cleanup'].append(f"폴더 삭제 실패: {folder_info.get('folder_name', 'Unknown')} - {str(e)}")
            
            # 전체 성공 여부 판단
            rollback_results['success'] = len(rollback_results['failed_cleanup']) == 0
            
        except Exception as e:
            rollback_results['failed_cleanup'].append(f"롤백 전체 실패: {str(e)}")
        
        return rollback_results
    
    def create_course_structure(self, course_folder_id: str, total_weeks: int, create_weeks: int) -> int:
        """코스별 주차 구조 생성 (제한된 주차수만)"""
        created_files = 0
        
        try:
            for week in range(1, min(create_weeks + 1, total_weeks + 1)):
                # 주차 폴더 생성
                week_folder = self.create_drive_folder(course_folder_id, f"{week}주차")
                if week_folder.get('success'):
                    week_id = week_folder['folder_id']
                    
                    # 1교시, 2교시 폴더 생성
                    for session in [1, 2]:
                        session_folder = self.create_drive_folder(week_id, f"{session}교시")
                        if session_folder.get('success'):
                            session_id = session_folder['folder_id']
                            
                            # 템플릿 파일들 생성
                            file_types = ["교과서", "강의대사", "과제", "실습"]
                            for file_type in file_types:
                                template_instance = WorkspaceTemplate()
                                content = template_instance.get_template_content(file_type, week, session)
                                file_name = f"{week}주차{session}교시_{file_type}.md"
                                
                                file_result = self.create_drive_file(session_id, file_name, content)
                                if file_result.get('success'):
                                    created_files += 1
            
            return created_files
            
        except Exception as e:
            print(f"코스 구조 생성 오류: {str(e)}")
            return created_files
    
    def create_drive_folder(self, parent_id: str, folder_name: str) -> Dict:
        """구글 드라이브에 폴더 생성"""
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = drive_handler.service.files().create(
                body=folder_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            return {
                "success": True,
                "folder_id": folder.get('id'),
                "folder_name": folder.get('name'),
                "folder_link": folder.get('webViewLink')
            }
            
        except Exception as e:
            return {"error": f"폴더 생성 실패: {str(e)}"}
    
    def create_drive_file(self, parent_id: str, file_name: str, content: str) -> Dict:
        """구글 드라이브에 텍스트 파일 생성"""
        try:
            file_metadata = {
                'name': file_name,
                'parents': [parent_id]
            }
            
            # 텍스트 내용을 바이트 스트림으로 변환
            from googleapiclient.http import MediaIoBaseUpload
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain'
            )
            
            file = drive_handler.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            return {
                "success": True,
                "file_id": file.get('id'),
                "file_name": file.get('name'),
                "file_link": file.get('webViewLink')
            }
            
        except Exception as e:
            return {"error": f"파일 생성 실패: {str(e)}"}
    
    def verify_folder_exists(self, folder_id: str) -> bool:
        """폴더 존재 여부 확인"""
        try:
            if not drive_handler.service:
                drive_handler.authenticate()
            
            drive_handler.service.files().get(fileId=folder_id).execute()
            return True
        except:
            return False
    
    def upload_to_user_folder(self, user_id: str, file_path: str, file_name: str = None) -> Dict:
        """사용자 폴더에 파일 업로드"""
        user_id = str(user_id)
        
        if user_id not in self.user_folders:
            return {"error": "사용자 폴더가 없습니다. 먼저 폴더를 생성해주세요."}
        
        folder_id = self.user_folders[user_id]['folder_id']
        result = drive_handler.upload_file(file_path, file_name, folder_id)
        
        if result.get('success'):
            # 파일 카운트 업데이트
            self.user_folders[user_id]['file_count'] += 1
            self.save_user_folders()
        
        return result
    
    def get_user_files(self, user_id: str) -> Dict:
        """사용자 폴더의 파일 목록 조회"""
        user_id = str(user_id)
        
        if user_id not in self.user_folders:
            return {"error": "사용자 폴더가 없습니다"}
        
        folder_id = self.user_folders[user_id]['folder_id']
        files = drive_handler.list_files(folder_id)
        
        return {
            "success": True,
            "folder_info": self.user_folders[user_id],
            "files": files
        }
    
    def get_user_stats(self, user_id: str) -> Dict:
        """사용자 드라이브 사용 통계"""
        user_id = str(user_id)
        
        if user_id not in self.user_folders:
            return {"error": "사용자 폴더가 없습니다"}
        
        folder_info = self.user_folders[user_id]
        files = drive_handler.list_files(folder_info['folder_id'])
        
        total_size = 0
        file_types = {}
        
        for file in files:
            if 'size' in file:
                total_size += int(file['size'])
            
            mime_type = file.get('mimeType', 'unknown')
            file_types[mime_type] = file_types.get(mime_type, 0) + 1
        
        return {
            "success": True,
            "folder_name": folder_info['folder_name'],
            "folder_link": folder_info['folder_link'],
            "file_count": len(files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
            "workspace_info": {
                "created": folder_info.get('workspace_created', False),
                "files": folder_info.get('workspace_files', 0)
            }
        }
    
    def share_folder_with_email(self, user_id: str, email: str) -> Dict:
        """사용자 이메일로 폴더 공유"""
        user_id = str(user_id)
        
        if user_id not in self.user_folders:
            return {"error": "사용자 폴더가 없습니다"}
        
        folder_id = self.user_folders[user_id]['folder_id']
        
        try:
            if not drive_handler.service:
                drive_handler.authenticate()
            
            # 이메일로 편집 권한 부여
            permission = drive_handler.service.permissions().create(
                fileId=folder_id,
                body={
                    'role': 'writer',
                    'type': 'user',
                    'emailAddress': email
                },
                sendNotificationEmail=True
            ).execute()
            
            return {
                "success": True,
                "message": f"✅ {email}에 폴더 공유 완료!",
                "permission_id": permission.get('id')
            }
            
        except Exception as e:
            return {"error": f"공유 실패: {str(e)}"}

# 전역 인스턴스 생성
user_drive_manager = UserDriveManager() 