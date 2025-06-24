"""
Report Manager - 업무보고 시스템 관리 (완전 클라우드 기반)
구글 드라이브 전용 - 로컬 파일 접근 없음
"""

import json
import io
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from google_drive_handler import drive_handler

logger = logging.getLogger(__name__)

class ReportManager:
    """업무보고 시스템 관리 클래스 (완전 클라우드 기반)"""
    
    def __init__(self):
        # 완전 클라우드 기반: 구글 드라이브에만 데이터 저장
        self.report_manager_folder_name = "팜솔라_보고서관리_시스템"
        self.reports_file_name = "reports.json"
        self.templates_file_name = "report_templates.json"
        
        # 캐시된 데이터
        self.reports_data = None
        self.templates = None
        
        # 기본 템플릿 설정
        self.default_templates = {
            "daily": {
                "name": "일일 업무보고서",
                "checklist": [
                    "오늘 완료한 주요 업무",
                    "진행 중인 업무 현황", 
                    "내일 예정 업무",
                    "이슈 및 건의사항",
                    "기타 특이사항"
                ],
                "required_fields": ["완료한 업무", "진행 중인 업무", "내일 예정 업무"]
            },
            "weekly": {
                "name": "주간 업무보고서",
                "checklist": [
                    "주요 성과 및 완료 업무",
                    "목표 달성률",
                    "다음 주 계획",
                    "개선사항 및 제안",
                    "교육 및 학습 내용"
                ],
                "required_fields": ["주요 성과", "목표 달성률", "다음 주 계획"]
            },
            "project": {
                "name": "프로젝트 진행보고서",
                "checklist": [
                    "프로젝트 진행률",
                    "완료된 작업",
                    "현재 진행 작업",
                    "예정 작업",
                    "리스크 및 이슈",
                    "필요한 지원사항"
                ],
                "required_fields": ["진행률", "완료된 작업", "현재 진행 작업", "예정 작업"]
            }
        }
        
    def ensure_report_manager_folder(self) -> str:
        """보고서 관리 폴더 확인/생성"""
        try:
            if not drive_handler.authenticate():
                raise Exception("구글 드라이브 인증 실패")
            
            # 기존 폴더 검색
            query = f"name='{self.report_manager_folder_name}' and mimeType='application/vnd.google-apps.folder'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            
            # 폴더 생성
            folder_metadata = {
                'name': self.report_manager_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_handler.service.files().create(body=folder_metadata, fields='id').execute()
            return folder.get('id')
            
        except Exception as e:
            raise Exception(f"보고서 관리 폴더 생성 실패: {str(e)}")

    def _load_data(self):
        """구글 드라이브에서 보고서 데이터 로드"""
        if self.reports_data is not None:
            return
            
        try:
            folder_id = self.ensure_report_manager_folder()
            
            # 데이터 파일 검색
            query = f"name='{self.reports_file_name}' and parents in '{folder_id}'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                # 기존 파일 읽기
                file_id = files[0]['id']
                content = drive_handler.service.files().get_media(fileId=file_id).execute()
                self.reports_data = json.loads(content.decode('utf-8'))
            else:
                # 빈 데이터 생성
                self.reports_data = {}
                
        except Exception as e:
            logger.error(f"보고서 데이터 로드 실패: {e}")
            self.reports_data = {}
            
        # 템플릿 로드
        try:
            # 템플릿 파일 검색
            query = f"name='{self.templates_file_name}' and parents in '{folder_id}'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                # 기존 파일 읽기
                file_id = files[0]['id']
                content = drive_handler.service.files().get_media(fileId=file_id).execute()
                self.templates = json.loads(content.decode('utf-8'))
            else:
                # 기본 템플릿 생성
                self.templates = self.default_templates.copy()
                self._save_templates()
                
        except Exception as e:
            logger.error(f"템플릿 데이터 로드 실패: {e}")
            self.templates = self.default_templates.copy()

    def _save_data(self):
        """구글 드라이브에 보고서 데이터 저장"""
        if self.reports_data is None:
            return
            
        try:
            folder_id = self.ensure_report_manager_folder()
            content = json.dumps(self.reports_data, ensure_ascii=False, indent=2)
            
            # 기존 파일 검색
            query = f"name='{self.reports_file_name}' and parents in '{folder_id}'"
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
                    'name': self.reports_file_name,
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
            logger.error(f"보고서 데이터 저장 실패: {e}")

    def _save_templates(self):
        """구글 드라이브에 템플릿 데이터 저장"""
        if self.templates is None:
            return
            
        try:
            folder_id = self.ensure_report_manager_folder()
            content = json.dumps(self.templates, ensure_ascii=False, indent=2)
            
            # 기존 파일 검색
            query = f"name='{self.templates_file_name}' and parents in '{folder_id}'"
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
                    'name': self.templates_file_name,
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
            logger.error(f"템플릿 데이터 저장 실패: {e}")

    def start_report(self, user_id: str, report_type: str = "daily") -> Dict:
        """보고서 작성 시작"""
        self._load_data()  # 데이터 로드 확인
        
        if report_type not in self.templates:
            return {"error": f"지원하지 않는 보고서 타입: {report_type}"}
        
        template = self.templates[report_type]
        report_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 새 보고서 세션 생성
        report_session = {
            "report_id": report_id,
            "user_id": user_id,
            "type": report_type,
            "template": template,
            "status": "in_progress",
            "created_at": datetime.now().isoformat(),
            "responses": {},
            "current_step": 0,
            "completed_fields": []
        }
        
        # 사용자별 활성 보고서 설정
        if user_id not in self.reports_data:
            self.reports_data[user_id] = {"active_report": None, "completed_reports": []}
        
        self.reports_data[user_id]["active_report"] = report_session
        self._save_data()
        
        return {
            "success": True,
            "report_id": report_id,
            "template": template,
            "first_question": template["checklist"][0] if template["checklist"] else None
        }
    
    def get_active_report(self, user_id: str) -> Optional[Dict]:
        """사용자의 활성 보고서 조회"""
        self._load_data()  # 데이터 로드 확인
        
        if user_id not in self.reports_data:
            return None
        
        return self.reports_data[user_id].get("active_report")
    
    def add_response(self, user_id: str, response: str) -> Dict:
        """보고서 응답 추가"""
        active_report = self.get_active_report(user_id)
        if not active_report:
            return {"error": "진행 중인 보고서가 없습니다. /report 명령어로 시작하세요."}
        
        template = active_report["template"]
        current_step = active_report["current_step"]
        checklist = template["checklist"]
        
        if current_step >= len(checklist):
            return {"error": "모든 항목이 완료되었습니다."}
        
        # 현재 질문에 대한 응답 저장
        current_question = checklist[current_step]
        active_report["responses"][current_question] = response
        active_report["completed_fields"].append(current_question)
        
        # 다음 단계로 이동
        active_report["current_step"] += 1
        
        # 완료 여부 확인
        if active_report["current_step"] >= len(checklist):
            return self._check_completion(user_id, active_report)
        else:
            # 다음 질문 제공
            next_question = checklist[active_report["current_step"]]
            self._save_data()
            
            return {
                "success": True,
                "next_question": next_question,
                "progress": f"{active_report['current_step']}/{len(checklist)}",
                "completed": False
            }
    
    def _check_completion(self, user_id: str, report: Dict) -> Dict:
        """보고서 완료 여부 확인"""
        template = report["template"]
        required_fields = template.get("required_fields", [])
        responses = report["responses"]
        
        # 필수 항목 확인
        missing_fields = []
        for field in required_fields:
            # 필수 항목이 응답에 포함되어 있는지 확인 (부분 매칭)
            found = False
            for question in responses:
                if any(keyword in question for keyword in field.split()):
                    if responses[question].strip():
                        found = True
                        break
            if not found:
                missing_fields.append(field)
        
        if missing_fields:
            return {
                "success": False,
                "missing_fields": missing_fields,
                "message": "필수 항목이 누락되었습니다.",
                "completed": False
            }
        else:
            # 보고서 완료
            report["status"] = "completed"
            report["completed_at"] = datetime.now().isoformat()
            
            # 완료된 보고서로 이동
            self.reports_data[user_id]["completed_reports"].append(report)
            self.reports_data[user_id]["active_report"] = None
            self._save_data()
            
            return {
                "success": True,
                "completed": True,
                "report": report,
                "message": "보고서가 완료되었습니다!"
            }
    
    def get_report_summary(self, user_id: str, report_id: str = None) -> Dict:
        """보고서 요약 생성"""
        if report_id:
            # 특정 보고서 조회
            report = self._find_report_by_id(user_id, report_id)
        else:
            # 최근 완료된 보고서 조회
            if user_id not in self.reports_data:
                return {"error": "보고서가 없습니다."}
            
            completed_reports = self.reports_data[user_id].get("completed_reports", [])
            if not completed_reports:
                return {"error": "완료된 보고서가 없습니다."}
            
            report = completed_reports[-1]  # 가장 최근 보고서
        
        if not report:
            return {"error": "보고서를 찾을 수 없습니다."}
        
        # 요약 생성
        summary = {
            "report_id": report["report_id"],
            "type": report["type"],
            "created_at": report["created_at"],
            "completed_at": report.get("completed_at"),
            "responses": report["responses"],
            "template_name": report["template"]["name"]
        }
        
        return {"success": True, "summary": summary}
    
    def _find_report_by_id(self, user_id: str, report_id: str) -> Optional[Dict]:
        """ID로 보고서 찾기"""
        if user_id not in self.reports_data:
            return None
        
        # 활성 보고서에서 찾기
        active_report = self.reports_data[user_id].get("active_report")
        if active_report and active_report["report_id"] == report_id:
            return active_report
        
        # 완료된 보고서에서 찾기
        completed_reports = self.reports_data[user_id].get("completed_reports", [])
        for report in completed_reports:
            if report["report_id"] == report_id:
                return report
        
        return None
    
    def cancel_report(self, user_id: str) -> Dict:
        """진행 중인 보고서 취소"""
        if user_id not in self.reports_data:
            return {"error": "진행 중인 보고서가 없습니다."}
        
        active_report = self.reports_data[user_id].get("active_report")
        if not active_report:
            return {"error": "진행 중인 보고서가 없습니다."}
        
        self.reports_data[user_id]["active_report"] = None
        self._save_data()
        
        return {"success": True, "message": "보고서 작성이 취소되었습니다."}
    
    def get_user_reports(self, user_id: str, limit: int = 10) -> Dict:
        """사용자의 보고서 목록 조회"""
        if user_id not in self.reports_data:
            return {"success": True, "reports": []}
        
        completed_reports = self.reports_data[user_id].get("completed_reports", [])
        
        # 최신순으로 정렬
        sorted_reports = sorted(completed_reports, 
                              key=lambda x: x.get("completed_at", ""), 
                              reverse=True)
        
        # 제한된 수만 반환
        limited_reports = sorted_reports[:limit]
        
        # 간단한 정보만 포함
        report_list = []
        for report in limited_reports:
            report_list.append({
                "report_id": report["report_id"],
                "type": report["type"],
                "template_name": report["template"]["name"],
                "created_at": report["created_at"],
                "completed_at": report.get("completed_at")
            })
        
        return {"success": True, "reports": report_list}
    
    def get_available_templates(self) -> Dict:
        """사용 가능한 템플릿 목록"""
        template_list = []
        for key, template in self.templates.items():
            template_list.append({
                "key": key,
                "name": template["name"],
                "checklist_count": len(template["checklist"]),
                "required_fields_count": len(template.get("required_fields", []))
            })
        
        return {"success": True, "templates": template_list}
    
    def format_report_for_manager(self, report: Dict, user_name: str = "직원") -> str:
        """관리자용 보고서 포맷팅"""
        template_name = report["template"]["name"]
        created_at = datetime.fromisoformat(report["created_at"]).strftime("%Y-%m-%d %H:%M")
        completed_at = datetime.fromisoformat(report["completed_at"]).strftime("%Y-%m-%d %H:%M")
        
        formatted_report = f"""📋 **{template_name}**

👤 **작성자:** {user_name}
📅 **작성 시작:** {created_at}
✅ **완료 시간:** {completed_at}
🆔 **보고서 ID:** {report['report_id']}

📝 **보고 내용:**
"""
        
        for question, answer in report["responses"].items():
            formatted_report += f"\n**• {question}**\n{answer}\n"
        
        formatted_report += f"\n─────────────────\n💡 AI_Solarbot 자동 생성 보고서"
        
        return formatted_report 