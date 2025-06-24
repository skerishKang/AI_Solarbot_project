"""
관리자 전용 명령어 모음 (완전 메모리 기반)
구글 드라이브 전용 - 로컬 파일 접근 없음
"""

import json
from datetime import datetime, timedelta
from typing import List
from telegram import Update
from telegram.ext import ContextTypes
from functools import wraps
from monitoring import bot_monitor

# 관리자 ID 목록 (환경변수나 설정 파일에서 로드하는 것이 좋음)
ADMIN_IDS = [
    123456789,  # 실제 관리자 텔레그램 ID로 변경
    987654321   # 추가 관리자 ID
]

def admin_required(func):
    """관리자 권한 확인 데코레이터"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ 관리자 권한이 필요합니다.")
            return
        return await func(update, context)
    return wrapper

@admin_required
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """관리자 대시보드"""
    try:
        # monitoring.py의 메모리 데이터 사용
        today = datetime.now().strftime('%Y-%m-%d')
        
        total = bot_monitor.daily_stats.get(f"{today}_total", 0)
        success = bot_monitor.daily_stats.get(f"{today}_success", 0)
        errors = bot_monitor.daily_stats.get(f"{today}_errors", 0)
        
        success_rate = (success / total * 100) if total > 0 else 0
        
        # 활성 사용자 수
        active_users = len([
            user for user, data in bot_monitor.user_stats.items()
            if data["last_active"] and 
            datetime.fromisoformat(data["last_active"]).date() == datetime.now().date()
        ])
        
        # 인기 명령어 Top 5
        top_commands = sorted(
            bot_monitor.command_stats.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # 최근 에러
        recent_errors = list(bot_monitor.errors)[-5:] if bot_monitor.errors else []
        
        dashboard = f"""🔧 **관리자 대시보드**

📊 **오늘 ({today}) 통계:**
• 총 요청: {total}회
• 성공: {success}회  
• 에러: {errors}회
• 성공률: {success_rate:.1f}%

👥 **사용자:**
• 오늘 활성: {active_users}명
• 총 등록: {len(bot_monitor.user_stats)}명

🔥 **인기 명령어:**"""
        
        for i, (cmd, count) in enumerate(top_commands, 1):
            dashboard += f"\n{i}. /{cmd}: {count}회"
        
        if recent_errors:
            dashboard += f"\n\n⚠️ **최근 에러 ({len(recent_errors)}개):**"
            for error in recent_errors[-3:]:
                error_time = datetime.fromisoformat(error['timestamp']).strftime('%H:%M')
                dashboard += f"\n• {error_time} - {error['error_type']}"
        
        await update.message.reply_text(dashboard)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 대시보드 로드 실패: {e}")

@admin_required
async def admin_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """상세 리포트 생성"""
    try:
        # monitoring.py의 일일 리포트 사용
        daily_report = bot_monitor.get_daily_report()
        
        # 성능 메트릭 추가
        performance = bot_monitor.get_performance_metrics()
        
        if "error" not in performance:
            report = daily_report + f"""

⚡ **성능 메트릭 (24시간):**
• 평균 응답시간: {performance['avg_response_time']}초
• 총 요청: {performance['total_requests_24h']}회
• 성공률: {performance['success_rate']:.1f}%

🤖 **AI 모델 사용:**"""
            
            for model, count in performance['model_distribution'].items():
                report += f"\n• {model}: {count}회"
        else:
            report = daily_report
        
        await update.message.reply_text(report)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 리포트 생성 실패: {e}")

@admin_required
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """사용자 관리"""
    try:
        # monitoring.py의 메모리 데이터 사용
        user_stats = bot_monitor.user_stats
        
        if not user_stats:
            await update.message.reply_text("❌ 등록된 사용자가 없습니다.")
            return
        
        # 활성 사용자 (최근 7일)
        week_ago = datetime.now() - timedelta(days=7)
        active_users = []
        inactive_users = []
        
        for user_id, stats in user_stats.items():
            if stats.get('last_active'):
                last_active = datetime.fromisoformat(stats['last_active'])
                if last_active > week_ago:
                    active_users.append((user_id, stats))
                else:
                    inactive_users.append((user_id, stats))
            else:
                inactive_users.append((user_id, stats))
        
        # 활성 사용자 정렬 (명령어 수 기준)
        active_users.sort(key=lambda x: x[1]['commands'], reverse=True)
        
        user_report = f"""👥 **사용자 관리 리포트**

📊 **전체 통계:**
• 총 사용자: {len(user_stats)}명
• 활성 사용자 (7일): {len(active_users)}명
• 비활성 사용자: {len(inactive_users)}명

🔥 **활성 사용자 Top 10:**"""
        
        for i, (user_id, stats) in enumerate(active_users[:10], 1):
            last_active = datetime.fromisoformat(stats['last_active']).strftime('%m/%d')
            user_report += f"\n{i}. ID:{user_id[-4:]} | {stats['commands']}회 | {last_active}"
        
        if len(user_report) > 4000:  # 텔레그램 메시지 길이 제한
            user_report = user_report[:4000] + "\n..."
        
        await update.message.reply_text(user_report)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 사용자 데이터 로드 실패: {e}")

@admin_required
async def admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """메모리 데이터 상태 확인"""
    try:
        await update.message.reply_text("📊 메모리 데이터 상태 확인 중...")
        
        # 메모리 사용량 정보
        activities_count = len(bot_monitor.activities)
        errors_count = len(bot_monitor.errors)
        users_count = len(bot_monitor.user_stats)
        commands_count = len(bot_monitor.command_stats)
        
        status_report = f"""💾 **메모리 데이터 상태**

📈 **저장된 데이터:**
• 사용자 활동: {activities_count}개
• 에러 로그: {errors_count}개  
• 등록 사용자: {users_count}명
• 명령어 통계: {commands_count}개

ℹ️ **메모리 기반 시스템:**
• 활동 로그: 최대 1,000개 유지
• 에러 로그: 최대 500개 유지
• 재시작 시 데이터 초기화됨

⚠️ **중요:** 영구 저장이 필요한 데이터는 
구글 드라이브 시스템을 사용하세요."""
        
        await update.message.reply_text(status_report)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 상태 확인 실패: {e}")

@admin_required
async def admin_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """메모리 데이터 정리"""
    try:
        await update.message.reply_text("🧹 메모리 데이터 정리 중...")
        
        # 현재 상태 저장
        before_activities = len(bot_monitor.activities)
        before_errors = len(bot_monitor.errors)
        
        # 30일 이전 활동 데이터 정리
        cutoff_date = datetime.now() - timedelta(days=30)
        filtered_activities = [
            activity for activity in bot_monitor.activities
            if activity.timestamp > cutoff_date
        ]
        
        # 메모리 데이터 업데이트
        bot_monitor.activities.clear()
        bot_monitor.activities.extend(filtered_activities)
        
        # 오래된 일일 통계 정리 (30일 이전)
        old_stats_keys = [
            key for key in bot_monitor.daily_stats.keys()
            if '_' in key and len(key.split('_')[0]) == 10  # YYYY-MM-DD 형식
        ]
        
        removed_stats = 0
        for key in old_stats_keys:
            try:
                date_str = key.split('_')[0]
                stat_date = datetime.strptime(date_str, '%Y-%m-%d')
                if stat_date < cutoff_date:
                    del bot_monitor.daily_stats[key]
                    removed_stats += 1
            except:
                continue
        
        after_activities = len(bot_monitor.activities)
        after_errors = len(bot_monitor.errors)
        
        result = f"""🧹 **메모리 정리 완료**

📊 **정리 결과:**
• 활동 로그: {before_activities} → {after_activities}개
• 에러 로그: {before_errors} → {after_errors}개
• 오래된 통계: {removed_stats}개 제거

✅ 30일 이전 데이터가 정리되었습니다."""
        
        await update.message.reply_text(result)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 정리 실패: {e}")

@admin_required
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """전체 사용자에게 공지사항 전송"""
    message_parts = update.message.text.split(' ', 1)
    
    if len(message_parts) < 2:
        await update.message.reply_text("""📢 **전체 공지 사용법**

`/admin_broadcast [공지내용]`

**예시:**
```
/admin_broadcast 시스템 점검으로 인해 내일 오전 2시-4시 서비스가 일시 중단됩니다.
```

**주의사항:**
• 모든 등록된 사용자에게 발송됩니다
• 신중하게 사용해주세요
• 취소할 수 없습니다""")
        return
    
    broadcast_message = message_parts[1]
    
    # 확인 메시지
    await update.message.reply_text(
        f"📢 **전체 공지 확인**\n\n"
        f"다음 메시지를 모든 사용자에게 보내시겠습니까?\n\n"
        f"```\n{broadcast_message}\n```\n\n"
        f"확인하려면 `/admin_broadcast_confirm {broadcast_message[:50]}`를 입력하세요."
    )

@admin_required  
async def admin_broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """공지사항 전송 확인 및 실행"""
    # 이 부분은 실제 구현시 사용자 목록을 가져와서 전송하는 로직이 필요
    await update.message.reply_text("⚠️ 실제 전송 기능은 보안상 주석 처리되어 있습니다.")

@admin_required
async def admin_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇 재시작 (주의!)"""
    await update.message.reply_text(
        "⚠️ **봇 재시작 경고**\n\n"
        "봇을 재시작하면 현재 실행 중인 모든 작업이 중단됩니다.\n"
        "정말 재시작하시겠습니까?\n\n"
        "확인: `/admin_restart_confirm`"
    )

@admin_required
async def admin_restart_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇 재시작 확인"""
    await update.message.reply_text("🔄 봇을 재시작합니다...")
    
    # 실제 재시작 로직 (주의: 프로덕션에서는 더 안전한 방법 사용)
    import sys
    import os
    
    # 현재 스크립트 재실행
    os.execv(sys.executable, ['python'] + sys.argv) 