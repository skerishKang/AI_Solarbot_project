"""
AI_Solarbot 관리자 전용 명령어
- 시스템 모니터링
- 사용자 관리
- 봇 설정 변경
- 데이터 백업/복원
- 성능 최적화
"""

import os
import json
import psutil
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from pathlib import Path
from monitoring import bot_monitor
from ai_handler import ai_handler

# 관리자 ID 확인
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID', '')

def admin_required(func):
    """관리자 권한 확인 데코레이터"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if ADMIN_USER_ID and user_id != ADMIN_USER_ID:
            await update.message.reply_text("⚠️ 관리자만 사용할 수 있는 명령어입니다.")
            return
        
        return await func(update, context)
    
    return wrapper

@admin_required
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """관리자 대시보드"""
    # 시스템 리소스 정보
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/')
    
    # 봇 성능 메트릭
    performance = bot_monitor.get_performance_metrics()
    
    # AI 사용량
    usage_stats = ai_handler.get_usage_stats()
    
    dashboard = f"""🔧 **관리자 대시보드**

💻 **시스템 리소스:**
• CPU: {cpu_percent}%
• 메모리: {memory.percent}% ({memory.used//1024//1024}MB / {memory.total//1024//1024}MB)
• 디스크: {disk.percent}% ({disk.used//1024//1024//1024}GB / {disk.total//1024//1024//1024}GB)

🤖 **봇 성능:**"""
    
    if "error" not in performance:
        dashboard += f"""
• 24시간 요청: {performance['total_requests_24h']}회
• 평균 응답시간: {performance['avg_response_time']}초
• 성공률: {performance['success_rate']:.1f}%
• AI 모델 분포: {performance['model_distribution']}"""
    else:
        dashboard += f"\n• {performance['error']}"
    
    dashboard += f"""

🧠 **AI 사용량:**
• Gemini: {usage_stats['daily_gemini']}/1400회
• ChatGPT: {usage_stats['daily_chatgpt']}회
• 총 누적: Gemini {usage_stats['total_gemini']}회, ChatGPT {usage_stats['total_chatgpt']}회

⚙️ **관리 명령어:**
/admin_report - 일일 리포트
/admin_users - 사용자 관리
/admin_backup - 데이터 백업
/admin_cleanup - 로그 정리
/admin_broadcast - 전체 공지
/admin_restart - 봇 재시작 (주의!)"""
    
    await update.message.reply_text(dashboard)

@admin_required
async def admin_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """일일 리포트"""
    report = bot_monitor.get_daily_report()
    await update.message.reply_text(report)

@admin_required
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """사용자 관리"""
    try:
        data_dir = Path("../data")
        metrics_file = data_dir / "bot_metrics.json"
        
        if not metrics_file.exists():
            await update.message.reply_text("❌ 사용자 데이터가 없습니다.")
            return
        
        with open(metrics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        user_stats = data.get('user_stats', {})
        
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
    """데이터 백업"""
    try:
        await update.message.reply_text("🔄 데이터 백업 중...")
        
        # 백업 폴더 생성
        backup_dir = Path("../backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_folder = backup_dir / f"backup_{timestamp}"
        backup_folder.mkdir()
        
        # 백업할 파일들
        data_dir = Path("../data")
        files_to_backup = [
            "user_activity.json",
            "bot_metrics.json", 
            "error_log.json",
            "bot_monitor.log"
        ]
        
        src_files = [
            "../src/homework_data.json"
        ]
        
        backup_count = 0
        
        # data 폴더 백업
        for filename in files_to_backup:
            src_file = data_dir / filename
            if src_file.exists():
                dst_file = backup_folder / filename
                dst_file.write_bytes(src_file.read_bytes())
                backup_count += 1
        
        # src 폴더 백업
        for src_path in src_files:
            src_file = Path(src_path)
            if src_file.exists():
                dst_file = backup_folder / src_file.name
                dst_file.write_bytes(src_file.read_bytes())
                backup_count += 1
        
        # 백업 정보 파일
        backup_info = {
            "timestamp": timestamp,
            "files_backed_up": backup_count,
            "backup_size_mb": sum(f.stat().st_size for f in backup_folder.iterdir()) / 1024 / 1024
        }
        
        info_file = backup_folder / "backup_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        # 오래된 백업 정리 (10개 이상시)
        backup_folders = sorted([d for d in backup_dir.iterdir() if d.is_dir()])
        if len(backup_folders) > 10:
            for old_backup in backup_folders[:-10]:
                import shutil
                shutil.rmtree(old_backup)
        
        await update.message.reply_text(
            f"✅ 백업 완료!\n\n"
            f"📁 폴더: {backup_folder.name}\n"
            f"📄 파일: {backup_count}개\n"
            f"💾 크기: {backup_info['backup_size_mb']:.2f}MB"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ 백업 실패: {e}")

@admin_required
async def admin_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """로그 및 데이터 정리"""
    try:
        await update.message.reply_text("🧹 데이터 정리 중...")
        
        cleaned_files = []
        total_saved_mb = 0
        
        # 로그 파일 정리 (30일 이상 된 것)
        data_dir = Path("../data")
        log_file = data_dir / "bot_monitor.log"
        
        if log_file.exists():
            original_size = log_file.stat().st_size
            
            # 로그 파일 크기가 10MB 이상이면 정리
            if original_size > 10 * 1024 * 1024:
                # 최근 1000줄만 유지
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) > 1000:
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.writelines(lines[-1000:])
                    
                    new_size = log_file.stat().st_size
                    saved_mb = (original_size - new_size) / 1024 / 1024
                    total_saved_mb += saved_mb
                    cleaned_files.append(f"bot_monitor.log ({saved_mb:.1f}MB 절약)")
        
        # 오래된 활동 데이터 정리
        activity_file = data_dir / "user_activity.json"
        if activity_file.exists():
            with open(activity_file, 'r', encoding='utf-8') as f:
                activities = json.load(f)
            
            original_count = len(activities)
            
            # 30일 이전 데이터 삭제
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_activities = [
                act for act in activities
                if datetime.fromisoformat(act['timestamp']) > cutoff_date
            ]
            
            if len(recent_activities) < original_count:
                with open(activity_file, 'w', encoding='utf-8') as f:
                    json.dump(recent_activities, f, ensure_ascii=False, indent=2)
                
                cleaned_files.append(f"user_activity.json ({original_count - len(recent_activities)}개 항목 정리)")
        
        # 에러 로그 정리
        error_file = data_dir / "error_log.json"
        if error_file.exists():
            with open(error_file, 'r', encoding='utf-8') as f:
                errors = json.load(f)
            
            original_count = len(errors)
            
            # 최근 100개만 유지
            if original_count > 100:
                with open(error_file, 'w', encoding='utf-8') as f:
                    json.dump(errors[-100:], f, ensure_ascii=False, indent=2)
                
                cleaned_files.append(f"error_log.json ({original_count - 100}개 에러 정리)")
        
        result = "🧹 **데이터 정리 완료**\n\n"
        
        if cleaned_files:
            result += "📄 **정리된 파일들:**\n"
            for file_info in cleaned_files:
                result += f"• {file_info}\n"
            
            if total_saved_mb > 0:
                result += f"\n💾 **총 절약 용량:** {total_saved_mb:.1f}MB"
        else:
            result += "✨ 정리할 데이터가 없습니다. 시스템이 깨끗합니다!"
        
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