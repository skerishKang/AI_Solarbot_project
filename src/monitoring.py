"""
AI_Solarbot 모니터링 및 로깅 시스템 (완전 메모리 기반)
- 실시간 사용자 활동 추적
- 성능 메트릭 수집
- 에러 로깅 및 알림
- 사용 패턴 분석
로컬 파일 접근 없음 - 메모리에서만 관리
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from dataclasses import dataclass
from collections import defaultdict, deque

@dataclass
class UserActivity:
    user_id: str
    username: str
    command: str
    timestamp: datetime
    response_time: float
    ai_model_used: str
    success: bool
    error_msg: str = ""

class BotMonitor:
    def __init__(self):
        # 완전 메모리 기반 - 파일 저장 없음
        
        # 메모리 내 데이터 저장 (최대 크기 제한)
        self.activities = deque(maxlen=1000)  # 최근 1000개 활동
        self.errors = deque(maxlen=500)  # 최근 500개 에러
        
        # 메모리 내 통계
        self.daily_stats = defaultdict(int)
        self.command_stats = defaultdict(int)
        self.user_stats = defaultdict(lambda: {"commands": 0, "last_active": None})
        
        # 로거 설정 (콘솔 출력만)
        self.setup_logger()
    
    def setup_logger(self):
        """전용 로거 설정 (콘솔 출력만)"""
        self.logger = logging.getLogger('BotMonitor')
        self.logger.setLevel(logging.INFO)
        
        # 콘솔 핸들러만 사용 (파일 저장 없음)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 포맷터
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
    
    def log_user_activity(self, user_id: str, username: str, command: str, 
                         response_time: float, ai_model: str, success: bool, 
                         error_msg: str = ""):
        """사용자 활동 로깅 (메모리 기반)"""
        activity = UserActivity(
            user_id=str(user_id),
            username=username or "Unknown",
            command=command,
            timestamp=datetime.now(),
            response_time=response_time,
            ai_model_used=ai_model,
            success=success,
            error_msg=error_msg
        )
        
        # 메모리에 저장
        self.activities.append(activity)
        
        # 통계 업데이트
        self._update_stats(activity)
        
        # 로그 기록 (콘솔 출력만)
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"USER:{user_id} CMD:{command} STATUS:{status} "
            f"TIME:{response_time:.2f}s MODEL:{ai_model}"
        )
    
    def _update_stats(self, activity: UserActivity):
        """통계 업데이트 (메모리 기반)"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 일일 통계
        self.daily_stats[f"{today}_total"] += 1
        if activity.success:
            self.daily_stats[f"{today}_success"] += 1
        else:
            self.daily_stats[f"{today}_errors"] += 1
        
        # 명령어 통계
        self.command_stats[activity.command] += 1
        
        # 사용자 통계
        self.user_stats[activity.user_id]["commands"] += 1
        self.user_stats[activity.user_id]["last_active"] = activity.timestamp.isoformat()
    
    def log_error(self, error_type: str, error_msg: str, user_id: str = "", 
                  command: str = ""):
        """에러 로깅 (메모리 기반)"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_msg': error_msg,
            'user_id': user_id,
            'command': command
        }
        
        # 메모리에 저장
        self.errors.append(error_data)
        
        self.logger.error(f"ERROR:{error_type} MSG:{error_msg} USER:{user_id}")
    
    def get_daily_report(self) -> str:
        """일일 리포트 생성"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        total = self.daily_stats.get(f"{today}_total", 0)
        success = self.daily_stats.get(f"{today}_success", 0)
        errors = self.daily_stats.get(f"{today}_errors", 0)
        
        success_rate = (success / total * 100) if total > 0 else 0
        
        # 인기 명령어 Top 5
        top_commands = sorted(
            self.command_stats.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # 활성 사용자 수
        active_users = len([
            user for user, data in self.user_stats.items()
            if data["last_active"] and 
            datetime.fromisoformat(data["last_active"]).date() == datetime.now().date()
        ])
        
        report = f"""📊 **{today} 일일 리포트**

📈 **사용량 통계:**
• 총 요청: {total}회
• 성공: {success}회
• 에러: {errors}회
• 성공률: {success_rate:.1f}%

👥 **사용자 활동:**
• 활성 사용자: {active_users}명
• 총 등록 사용자: {len(self.user_stats)}명

🔥 **인기 명령어:**"""
        
        for i, (cmd, count) in enumerate(top_commands, 1):
            report += f"\n{i}. /{cmd}: {count}회"
        
        return report
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 반환"""
        try:
            # 최근 활동 로드 (메모리에서)
            activities = []
            if self.activities:
                # UserActivity 객체를 딕셔너리로 변환
                activities = [
                    {
                        'user_id': activity.user_id,
                        'username': activity.username,
                        'command': activity.command,
                        'timestamp': activity.timestamp.isoformat(),
                        'response_time': activity.response_time,
                        'ai_model_used': activity.ai_model_used,
                        'success': activity.success,
                        'error_msg': activity.error_msg
                    }
                    for activity in self.activities
                ]
            
            # 최근 24시간 데이터 필터링
            recent_activities = [
                act for act in activities[-100:]  # 최근 100개
                if datetime.fromisoformat(act['timestamp']) > 
                   datetime.now() - timedelta(hours=24)
            ]
            
            if not recent_activities:
                return {"error": "최근 24시간 데이터 없음"}
            
            # 평균 응답 시간
            avg_response_time = sum(
                act['response_time'] for act in recent_activities
            ) / len(recent_activities)
            
            # AI 모델 사용 분포
            model_usage = defaultdict(int)
            for act in recent_activities:
                model_usage[act['ai_model_used']] += 1
            
            return {
                "total_requests_24h": len(recent_activities),
                "avg_response_time": round(avg_response_time, 2),
                "model_distribution": dict(model_usage),
                "success_rate": sum(1 for act in recent_activities if act['success']) / len(recent_activities) * 100
            }
            
        except Exception as e:
            self.logger.error(f"성능 메트릭 생성 실패: {e}")
            return {"error": str(e)}

# 전역 모니터 인스턴스
bot_monitor = BotMonitor()

def track_command(func):
    """명령어 실행 추적 데코레이터"""
    async def wrapper(update, context, *args, **kwargs):
        start_time = time.time()
        user_id = update.effective_user.id
        username = update.effective_user.username
        command = update.message.text.split()[0].replace('/', '')
        
        try:
            result = await func(update, context, *args, **kwargs)
            response_time = time.time() - start_time
            
            bot_monitor.log_user_activity(
                user_id=user_id,
                username=username,
                command=command,
                response_time=response_time,
                ai_model="system",
                success=True
            )
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            
            bot_monitor.log_user_activity(
                user_id=user_id,
                username=username,
                command=command,
                response_time=response_time,
                ai_model="system",
                success=False,
                error_msg=str(e)
            )
            
            bot_monitor.log_error(
                error_type="CommandError",
                error_msg=str(e),
                user_id=str(user_id),
                command=command
            )
            
            raise
    
    return wrapper 