"""
팀 프로젝트 협업 기능 관리 시스템
- 공유 워크스페이스 생성 및 관리
- 실시간 댓글 및 피드백 시스템
- 파일 버전 관리 및 히스토리
- 강사용 모니터링 대시보드
- 팀원 초대 및 권한 관리
"""

import json
import io
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.google_drive_handler import drive_handler
from src.user_drive_manager import UserDriveManager

class CollaborationManager:
    def __init__(self):
        # 완전 클라우드 기반: 구글 드라이브에만 데이터 저장
        self.collaboration_folder_name = "팜솔라_협업관리_시스템"
        self.teams_file_name = "teams.json"
        self.comments_file_name = "comments.json"
        self.activity_file_name = "activity.json"
        
        # 캐시된 데이터
        self.teams = None
        self.comments = None
        self.activity_log = None
        self.user_drive_manager = UserDriveManager()
        
    def ensure_collaboration_folder(self) -> str:
        """협업 관리 폴더 확인/생성"""
        try:
            if not drive_handler.authenticate():
                raise Exception("구글 드라이브 인증 실패")
            
            # 기존 폴더 검색
            query = f"name='{self.collaboration_folder_name}' and mimeType='application/vnd.google-apps.folder'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            
            # 폴더 생성
            folder_metadata = {
                'name': self.collaboration_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_handler.service.files().create(body=folder_metadata, fields='id').execute()
            return folder.get('id')
            
        except Exception as e:
            raise Exception(f"협업 폴더 생성 실패: {str(e)}")
    
    def load_json_from_drive(self, file_name: str) -> Dict:
        """구글 드라이브에서 JSON 데이터 로드"""
        try:
            folder_id = self.ensure_collaboration_folder()
            
            # 데이터 파일 검색
            query = f"name='{file_name}' and parents in '{folder_id}'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                # 기존 파일 읽기
                file_id = files[0]['id']
                content = drive_handler.service.files().get_media(fileId=file_id).execute()
                return json.loads(content.decode('utf-8'))
            else:
                # 빈 데이터 반환
                return {} if file_name != self.activity_file_name else []
                
        except Exception as e:
            print(f"{file_name} 로드 실패: {e}")
            return {} if file_name != self.activity_file_name else []
    
    def save_json_to_drive(self, file_name: str, data):
        """구글 드라이브에 JSON 데이터 저장"""
        try:
            folder_id = self.ensure_collaboration_folder()
            content = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 기존 파일 검색
            query = f"name='{file_name}' and parents in '{folder_id}'"
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
                    'name': file_name,
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
            print(f"{file_name} 저장 실패: {e}")

    def load_teams(self) -> Dict:
        """팀 정보 로드"""
        if self.teams is None:
            self.teams = self.load_json_from_drive(self.teams_file_name)
        return self.teams
    
    def save_teams(self):
        """팀 정보 저장"""
        if self.teams is not None:
            self.save_json_to_drive(self.teams_file_name, self.teams)
    
    def load_comments(self) -> Dict:
        """댓글 정보 로드"""
        if self.comments is None:
            self.comments = self.load_json_from_drive(self.comments_file_name)
        return self.comments
    
    def save_comments(self):
        """댓글 정보 저장"""
        if self.comments is not None:
            self.save_json_to_drive(self.comments_file_name, self.comments)
    
    def load_activity(self) -> List:
        """활동 로그 로드"""
        if self.activity_log is None:
            self.activity_log = self.load_json_from_drive(self.activity_file_name)
        return self.activity_log
    
    def save_activity(self):
        """활동 로그 저장"""
        if self.activity_log is not None:
            self.save_json_to_drive(self.activity_file_name, self.activity_log)

    def create_team_workspace(self, team_name: str, creator_id: str, creator_name: str, course_type: str = "12주") -> Dict:
        """팀 워크스페이스 생성"""
        if not drive_handler.authenticate():
            return {"error": "구글 드라이브 인증 실패"}
        
        try:
            # 팀 폴더 생성
            main_folder_id = drive_handler.get_homework_folder_id()
            team_folder_name = f"팀_{team_name}_{int(time.time())}"
            
            team_folder_metadata = {
                'name': team_folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [main_folder_id]
            }
            
            team_folder = drive_handler.service.files().create(
                body=team_folder_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            team_folder_id = team_folder.get('id')
            team_folder_link = team_folder.get('webViewLink')
            
            # 팀 워크스페이스 구조 생성
            workspace_structure = self.create_team_workspace_structure(team_folder_id, course_type)
            
            # 팀 정보 저장
            team_id = f"team_{int(time.time())}"
            team_info = {
                'team_id': team_id,
                'team_name': team_name,
                'folder_id': team_folder_id,
                'folder_link': team_folder_link,
                'creator_id': str(creator_id),
                'creator_name': creator_name,
                'members': {
                    str(creator_id): {
                        'name': creator_name,
                        'role': 'leader',
                        'joined_at': datetime.now().isoformat(),
                        'permissions': ['read', 'write', 'invite', 'manage']
                    }
                },
                'created_at': datetime.now().isoformat(),
                'course_type': course_type,
                'workspace_structure': workspace_structure,
                'settings': {
                    'allow_comments': True,
                    'require_approval': False,
                    'auto_sync': True,
                    'notification_level': 'all'
                }
            }
            
            teams = self.load_teams()
            teams[team_id] = team_info
            self.teams = teams
            self.save_teams()
            
            # 활동 로그 추가
            self.log_activity(team_id, creator_id, 'team_created', {
                'team_name': team_name,
                'workspace_files': workspace_structure.get('created_files', 0)
            })
            
            return {
                "success": True,
                "team_info": team_info,
                "message": f"✅ '{team_name}' 팀 워크스페이스가 생성되었습니다!\n📁 {workspace_structure.get('created_files', 0)}개의 파일이 자동으로 생성되었습니다."
            }
            
        except Exception as e:
            return {"error": f"팀 워크스페이스 생성 실패: {str(e)}"}

    def create_team_workspace_structure(self, team_folder_id: str, course_type: str) -> Dict:
        """팀 워크스페이스 구조 생성"""
        try:
            created_folders = []
            created_files = []
            
            # 기본 팀 폴더 구조
            team_structure = {
                "📋 프로젝트 계획": {
                    "files": ["프로젝트_계획서.md", "역할분담.md", "일정관리.md"]
                },
                "💻 소스코드": {
                    "subfolders": ["main", "modules", "tests", "docs"]
                },
                "📊 과제 제출": {
                    "subfolders": [f"{i}주차" for i in range(1, 13 if course_type == "12주" else 7)]
                },
                "🔄 버전 관리": {
                    "files": ["변경이력.md", "릴리즈노트.md"]
                },
                "💬 팀 커뮤니케이션": {
                    "files": ["회의록.md", "Q&A.md", "피드백.md"]
                },
                "📈 진도 관리": {
                    "files": ["진도현황.md", "개인별_진도.md"]
                }
            }
            
            # 폴더 및 파일 생성
            for folder_name, config in team_structure.items():
                folder_result = self.user_drive_manager.create_drive_folder(team_folder_id, folder_name)
                if folder_result.get('success'):
                    created_folders.append(folder_result)
                    folder_id = folder_result['folder_id']
                    
                    # 파일 생성
                    if 'files' in config:
                        for file_name in config['files']:
                            content = self.get_team_template_content(file_name, folder_name)
                            file_result = self.user_drive_manager.create_drive_file(folder_id, file_name, content)
                            if file_result.get('success'):
                                created_files.append(file_result)
                    
                    # 서브폴더 생성
                    if 'subfolders' in config:
                        for subfolder_name in config['subfolders']:
                            subfolder_result = self.user_drive_manager.create_drive_folder(folder_id, subfolder_name)
                            if subfolder_result.get('success'):
                                created_folders.append(subfolder_result)
            
            return {
                'success': True,
                'created_folders': len(created_folders),
                'created_files': len(created_files),
                'folders': created_folders,
                'files': created_files
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_team_template_content(self, file_name: str, folder_name: str) -> str:
        """팀 프로젝트용 템플릿 콘텐츠 생성"""
        templates = {
            "프로젝트_계획서.md": f"""# 🎯 프로젝트 계획서

## 📋 프로젝트 개요
- **프로젝트명**: 
- **팀명**: 
- **기간**: 
- **목표**: 

## 👥 팀원 구성
| 이름 | 역할 | 담당 업무 | 연락처 |
|------|------|-----------|--------|
|      |      |           |        |

## 📅 일정 계획
- [ ] 1주차: 프로젝트 기획 및 설계
- [ ] 2주차: 기본 구조 구현
- [ ] 3주차: 핵심 기능 개발
- [ ] 4주차: 테스트 및 디버깅
- [ ] 5주차: 최종 완성 및 발표 준비

## 🎯 주요 기능
1. 
2. 
3. 

## 📊 성공 지표
- 
- 
- 

---
*최종 수정: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
""",
            "역할분담.md": f"""# 👥 팀 역할 분담

## 🎯 전체 역할 개요
| 팀원 | 주요 역할 | 세부 담당 | 진행률 |
|------|-----------|-----------|--------|
|      | 팀장      |           | 0%     |
|      | 개발자    |           | 0%     |
|      | 디자이너  |           | 0%     |
|      | 테스터    |           | 0%     |

## 📋 상세 업무 분담

### 🔧 개발 업무
- **프론트엔드**: 
- **백엔드**: 
- **데이터베이스**: 
- **API 설계**: 

### 📊 관리 업무
- **프로젝트 관리**: 
- **일정 관리**: 
- **품질 관리**: 
- **문서화**: 

### 🎨 디자인 업무
- **UI/UX 설계**: 
- **그래픽 디자인**: 
- **사용자 경험**: 

## ⚡ 협업 규칙
1. **코드 리뷰**: 모든 코드는 최소 1명의 검토 필요
2. **커밋 메시지**: 명확하고 구체적으로 작성
3. **회의**: 주 2회 정기 회의 (월, 목)
4. **소통**: 텔레그램 그룹으로 실시간 소통
5. **문서화**: 작업 완료 시 반드시 문서 업데이트

---
*최종 수정: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
""",
            "회의록.md": f"""# 📝 팀 회의록

## 🗓️ 회의 기록

### 📅 {datetime.now().strftime('%Y-%m-%d')} 회의
**참석자**: 
**시간**: 
**장소**: 텔레그램 그룹

#### 📋 안건
1. 
2. 
3. 

#### 💬 논의 내용
- 
- 
- 

#### ✅ 결정 사항
- [ ] 
- [ ] 
- [ ] 

#### 📝 다음 회의까지 할 일
| 담당자 | 업무 | 마감일 |
|--------|------|--------|
|        |      |        |

---

### 📅 이전 회의 기록
*여기에 이전 회의록들이 추가됩니다*

## 📊 회의 통계
- **총 회의 횟수**: 1
- **평균 참석률**: 100%
- **완료된 액션 아이템**: 0/0

---
*최종 수정: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
""",
            "진도현황.md": f"""# 📈 팀 진도 현황

## 🎯 전체 진행률
**전체 진행률**: 5% (프로젝트 시작)

```
프로젝트 진행률: [█░░░░░░░░░] 5%
```

## 📊 영역별 진행률
| 영역 | 진행률 | 상태 | 담당자 |
|------|--------|------|--------|
| 📋 기획 | 10% | 🔄 진행중 | |
| 💻 개발 | 0% | ⏳ 대기중 | |
| 🎨 디자인 | 0% | ⏳ 대기중 | |
| 🧪 테스트 | 0% | ⏳ 대기중 | |
| 📝 문서화 | 5% | 🔄 진행중 | |

## 👥 개인별 진행률
| 팀원 | 전체 기여도 | 이번 주 활동 | 다음 주 계획 |
|------|-------------|--------------|--------------|
|      | 0%          |              |              |

## 📅 주차별 목표 달성률
| 주차 | 목표 | 달성률 | 상태 |
|------|------|--------|------|
| 1주차 | 프로젝트 기획 | 10% | 🔄 |
| 2주차 | 기본 구조 | 0% | ⏳ |
| 3주차 | 핵심 기능 | 0% | ⏳ |
| 4주차 | 테스트 | 0% | ⏳ |
| 5주차 | 완성 | 0% | ⏳ |

## ⚠️ 주의사항
- 
- 
- 

## 🎉 이번 주 성과
- ✅ 팀 워크스페이스 생성 완료
- ✅ 기본 문서 템플릿 설정
- 

---
*최종 수정: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        }
        
        return templates.get(file_name, f"# {file_name}\n\n*이 파일은 {folder_name}에서 자동 생성되었습니다.*\n\n---\n*생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    def invite_member(self, team_id: str, inviter_id: str, member_id: str, member_name: str, role: str = "member") -> Dict:
        """팀에 멤버 초대"""
        if team_id not in self.teams:
            return {"error": "존재하지 않는 팀입니다"}
        
        team = self.teams[team_id]
        
        # 초대 권한 확인
        if str(inviter_id) not in team['members']:
            return {"error": "팀 멤버가 아닙니다"}
        
        inviter = team['members'][str(inviter_id)]
        if 'invite' not in inviter.get('permissions', []):
            return {"error": "초대 권한이 없습니다"}
        
        # 이미 멤버인지 확인
        if str(member_id) in team['members']:
            return {"error": "이미 팀 멤버입니다"}
        
        # 멤버 추가
        permissions = ['read', 'write'] if role == 'member' else ['read', 'write', 'invite', 'manage']
        team['members'][str(member_id)] = {
            'name': member_name,
            'role': role,
            'joined_at': datetime.now().isoformat(),
            'permissions': permissions,
            'invited_by': str(inviter_id)
        }
        
        # 구글 드라이브 권한 부여
        try:
            drive_handler.service.permissions().create(
                fileId=team['folder_id'],
                body={
                    'role': 'writer',
                    'type': 'anyone'
                }
            ).execute()
        except Exception as e:
            pass  # 이미 권한이 있을 수 있음
        
        self.save_teams()
        
        # 활동 로그
        self.log_activity(team_id, inviter_id, 'member_invited', {
            'member_name': member_name,
            'member_id': member_id,
            'role': role
        })
        
        return {
            "success": True,
            "message": f"✅ {member_name}님이 '{team['team_name']}' 팀에 초대되었습니다!"
        }

    def add_comment(self, team_id: str, file_path: str, user_id: str, user_name: str, comment: str, line_number: Optional[int] = None) -> Dict:
        """파일에 댓글 추가"""
        if team_id not in self.teams:
            return {"error": "존재하지 않는 팀입니다"}
        
        if str(user_id) not in self.teams[team_id]['members']:
            return {"error": "팀 멤버가 아닙니다"}
        
        comment_id = f"comment_{int(time.time() * 1000)}"
        file_key = f"{team_id}:{file_path}"
        
        if file_key not in self.comments:
            self.comments[file_key] = []
        
        comment_data = {
            'comment_id': comment_id,
            'user_id': str(user_id),
            'user_name': user_name,
            'comment': comment,
            'line_number': line_number,
            'timestamp': datetime.now().isoformat(),
            'replies': []
        }
        
        self.comments[file_key].append(comment_data)
        self.save_comments()
        
        # 활동 로그
        self.log_activity(team_id, user_id, 'comment_added', {
            'file_path': file_path,
            'comment_preview': comment[:50] + '...' if len(comment) > 50 else comment
        })
        
        return {
            "success": True,
            "comment_id": comment_id,
            "message": "💬 댓글이 추가되었습니다!"
        }

    def get_file_comments(self, team_id: str, file_path: str) -> Dict:
        """파일의 모든 댓글 조회"""
        file_key = f"{team_id}:{file_path}"
        comments = self.comments.get(file_key, [])
        
        # 댓글을 시간순으로 정렬
        comments.sort(key=lambda x: x['timestamp'])
        
        return {
            "success": True,
            "comments": comments,
            "total_comments": len(comments)
        }

    def get_team_activity(self, team_id: str, days: int = 7) -> Dict:
        """팀 활동 내역 조회"""
        if team_id not in self.teams:
            return {"error": "존재하지 않는 팀입니다"}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        team_activities = [
            activity for activity in self.activity_log
            if activity.get('team_id') == team_id 
            and datetime.fromisoformat(activity['timestamp']) > cutoff_date
        ]
        
        # 활동을 시간순으로 정렬 (최신순)
        team_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "success": True,
            "activities": team_activities,
            "total_activities": len(team_activities),
            "period_days": days
        }

    def get_instructor_dashboard(self, instructor_id: str) -> Dict:
        """강사용 모니터링 대시보드"""
        # 모든 팀 정보 수집
        all_teams = []
        total_students = 0
        active_teams = 0
        
        for team_id, team_info in self.teams.items():
            # 팀 활동 통계
            recent_activity = len([
                activity for activity in self.activity_log
                if activity.get('team_id') == team_id 
                and datetime.fromisoformat(activity['timestamp']) > datetime.now() - timedelta(days=7)
            ])
            
            # 팀 진행률 계산 (간단한 휴리스틱)
            progress = self.calculate_team_progress(team_id)
            
            team_summary = {
                'team_id': team_id,
                'team_name': team_info['team_name'],
                'member_count': len(team_info['members']),
                'created_at': team_info['created_at'],
                'progress': progress,
                'recent_activity': recent_activity,
                'folder_link': team_info['folder_link']
            }
            
            all_teams.append(team_summary)
            total_students += len(team_info['members'])
            if recent_activity > 0:
                active_teams += 1
        
        # 전체 통계
        dashboard = {
            "success": True,
            "summary": {
                "total_teams": len(all_teams),
                "total_students": total_students,
                "active_teams": active_teams,
                "average_team_size": total_students / len(all_teams) if all_teams else 0
            },
            "teams": all_teams,
            "recent_activities": self.activity_log[-20:] if self.activity_log else []  # 최근 20개 활동
        }
        
        return dashboard

    def calculate_team_progress(self, team_id: str) -> int:
        """팀 진행률 계산 (간단한 휴리스틱)"""
        if team_id not in self.teams:
            return 0
        
        # 활동 기반 진행률 계산
        team_activities = [
            activity for activity in self.activity_log
            if activity.get('team_id') == team_id
        ]
        
        # 기본 점수 (팀 생성)
        progress = 5
        
        # 활동별 점수 추가
        activity_scores = {
            'member_invited': 10,
            'comment_added': 5,
            'file_created': 15,
            'file_updated': 10,
            'workspace_updated': 20
        }
        
        for activity in team_activities:
            activity_type = activity.get('action_type', '')
            progress += activity_scores.get(activity_type, 2)
        
        return min(progress, 100)  # 최대 100%

    def log_activity(self, team_id: str, user_id: str, action_type: str, details: Dict):
        """활동 로그 기록"""
        activity = {
            'team_id': team_id,
            'user_id': str(user_id),
            'action_type': action_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.activity_log.append(activity)
        
        # 로그가 너무 많아지면 오래된 것 삭제 (최근 1000개만 유지)
        if len(self.activity_log) > 1000:
            self.activity_log = self.activity_log[-1000:]
        
        self.save_activity()

    def get_team_list(self, user_id: str) -> Dict:
        """사용자가 속한 팀 목록 조회"""
        user_teams = []
        
        for team_id, team_info in self.teams.items():
            if str(user_id) in team_info['members']:
                member_info = team_info['members'][str(user_id)]
                team_summary = {
                    'team_id': team_id,
                    'team_name': team_info['team_name'],
                    'role': member_info['role'],
                    'member_count': len(team_info['members']),
                    'folder_link': team_info['folder_link'],
                    'progress': self.calculate_team_progress(team_id)
                }
                user_teams.append(team_summary)
        
        return {
            "success": True,
            "teams": user_teams,
            "total_teams": len(user_teams)
        }

    def share_file_with_team(self, team_id: str, file_id: str, user_id: str, message: str = "") -> Dict:
        """팀과 파일 공유"""
        if team_id not in self.teams:
            return {"error": "존재하지 않는 팀입니다"}
        
        if str(user_id) not in self.teams[team_id]['members']:
            return {"error": "팀 멤버가 아닙니다"}
        
        try:
            # 파일 정보 가져오기
            file_info = drive_handler.service.files().get(
                fileId=file_id,
                fields='name,webViewLink,mimeType'
            ).execute()
            
            # 활동 로그
            self.log_activity(team_id, user_id, 'file_shared', {
                'file_name': file_info.get('name'),
                'file_link': file_info.get('webViewLink'),
                'message': message
            })
            
            return {
                "success": True,
                "file_info": file_info,
                "message": f"📎 파일이 팀과 공유되었습니다!"
            }
            
        except Exception as e:
            return {"error": f"파일 공유 실패: {str(e)}"}

# 전역 인스턴스
collaboration_manager = CollaborationManager()
