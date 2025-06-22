"""
AI_Solarbot - 최종 통합 버전
- Gemini 우선 사용, 무료 한도 초과시 ChatGPT 자동 전환
- 팜솔라 교과서 기반 실제 과제 관리
- 태양광 전문 계산 기능
- 강의 지원 시스템
"""

import os
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from ai_handler import ai_handler, test_api_connection
from homework_manager import HomeworkManager
from monitoring import bot_monitor, track_command
from google_drive_handler import drive_handler, test_drive_connection
from admin_commands import (
    admin_dashboard, admin_report, admin_users, admin_backup, 
    admin_cleanup, admin_broadcast, admin_broadcast_confirm,
    admin_restart, admin_restart_confirm
)

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 봇 토큰
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'AI_Solarbot')

# 과제 관리자 인스턴스
homework_manager = HomeworkManager()

def safe_markdown(text: str) -> str:
    """텔레그램 마크다운을 안전하게 처리"""
    # 특수문자들을 이스케이프 처리하되, 의도된 마크다운은 보존
    # 백슬래시, 언더스코어, 대괄호 등을 이스케이프
    text = text.replace('\\', '\\\\')  # 백슬래시 먼저 처리
    text = text.replace('_', '\\_')   # 언더스코어 이스케이프
    text = text.replace('[', '\\[')   # 대괄호 이스케이프
    text = text.replace(']', '\\]')   # 대괄호 닫기 이스케이프
    
    # 연속된 별표 처리 (3개 이상이면 문제 발생 가능)
    text = re.sub(r'\*{3,}', '**', text)  # 3개 이상 별표는 2개로 제한
    
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """봇 시작 명령어"""
    user = update.effective_user
    
    # API 연결 상태 확인
    api_status = test_api_connection()
    gemini_status = "✅" if api_status["gemini"] else "⚠️"
    chatgpt_status = "✅" if api_status["openai"] else "⚠️"
    
    # 사용량 통계
    usage_stats = ai_handler.get_usage_stats()
    
    welcome_message = f"""안녕하세요 {user.first_name}님! 🌞

저는 {BOT_USERNAME}입니다!
ChatGPT 실무 강의와 팜솔라 업무를 도와드리는 AI 봇이에요.

🧠 AI 엔진 상태:
• Gemini {gemini_status} (오늘 {usage_stats['daily_gemini']}/1400회 사용)
• ChatGPT {chatgpt_status} (백업용)

📚 강의 관련 명령어:
/help - 전체 도움말
/homework - 현재 과제 확인
/submit - 과제 제출하기
/progress - 내 진도 확인
/template [주제] - 프롬프트 템플릿 생성

☀️ 팜솔라 전용 명령어:
/solar - 태양광 계산 가이드
/calc [용량]kW [지역] - 즉시 발전량 계산

🔧 시스템 명령어:
/status - 봇 상태 확인
/practice - 랜덤 연습 과제

💬 자유 대화:
그냥 메시지를 보내면 AI와 대화할 수 있어요!

시작해볼까요? 🚀"""
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """도움말 명령어"""
    help_text = """🤖 AI_Solarbot 완전 가이드

📚 **강의 지원 기능:**
• `/homework` - 현재 주차 과제 확인
• `/homework [주차] [강]` - 특정 과제 확인 (예: /homework 2 1)
• `/upload [과제명]` - 과제 파일 업로드 및 분석 (예: /upload 1주차2번째)
• `/explain [과제명]` - 과제 자세한 설명 제공 (예: /explain 프롬프트기초)
• `/submit [과제내용]` - 과제 제출하기
• `/progress` - 내 제출 현황 확인
• `/template [주제]` - 맞춤 프롬프트 템플릿 생성
• `/practice` - 랜덤 연습 과제

☀️ **태양광 전문 기능:**
• `/solar` - 태양광 계산 가이드
• `/calc [용량]kW [지역] [각도]` - 즉시 계산
  예: `/calc 100kW 서울`, `/calc 50kW 부산 25도`

🧠 **AI 대화:**
• 일반 메시지 → Gemini/ChatGPT 자동 응답
• 태양광 키워드 감지 → 전문 분석 제공
• 프롬프트 관련 질문 → 맞춤 가이드 제공

🔧 **시스템 기능:**
• `/status` - AI 엔진 상태 및 사용량
• `/next` - 다음 주차로 진행 (관리자용)

⚙️ **관리자 기능:**
• `/admin` - 관리자 대시보드 (관리자 전용)
• `/admin_report` - 일일 사용량 리포트
• `/admin_backup` - 데이터 백업

💡 **사용 팁:**
• 구체적으로 질문할수록 더 정확한 답변
• 태양광 계산 시 지역, 용량, 각도 명시
• 과제 제출 시 프롬프트와 결과 모두 포함

궁금한 점이 있으면 언제든 물어보세요! 🙋‍♂️"""
    await update.message.reply_text(help_text)

async def homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """과제 관련 명령어"""
    message_parts = update.message.text.split()
    
    if len(message_parts) == 1:
        # 현재 과제 확인
        current_hw = homework_manager.get_current_homework()
        if current_hw:
            hw_info = current_hw["homework"]
            response = f"""📚 현재 과제 안내

🎯 **{current_hw['week']}주차 {current_hw['lesson']}강**
**{hw_info['title']}**

{hw_info['description']}

⏱️ **예상 소요시간:** {hw_info['estimated_time']}
📊 **난이도:** {hw_info['difficulty']}

💡 **제출 방법:** `/submit [과제내용]`
📖 **다른 과제 보기:** `/homework [주차] [강]`"""
        else:
            response = "현재 등록된 과제가 없습니다."
            
    elif len(message_parts) == 3:
        # 특정 주차 과제 확인
        try:
            week = int(message_parts[1])
            lesson = int(message_parts[2])
            hw_data = homework_manager.get_homework_by_week(week, lesson)
            
            if "error" in hw_data:
                response = hw_data["error"]
            else:
                hw_info = hw_data["homework"]
                response = f"""📚 {week}주차 {lesson}강 과제

🎯 **{hw_info['title']}**

{hw_info['description']}

⏱️ **예상 소요시간:** {hw_info['estimated_time']}
📊 **난이도:** {hw_info['difficulty']}"""
        except ValueError:
            response = "올바른 형식: `/homework [주차번호] [강번호]`\n예: `/homework 2 1`"
    else:
        response = """📚 과제 명령어 사용법

• `/homework` - 현재 과제 확인
• `/homework [주차] [강]` - 특정 과제 확인
  예: `/homework 1 1`, `/homework 2 2`
• `/submit [내용]` - 과제 제출
• `/progress` - 제출 현황 확인"""
    
    await update.message.reply_text(response)

async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """다음 과제로 진행 (관리자용)"""
    user_id = str(update.effective_user.id)
    admin_id = os.getenv('ADMIN_USER_ID', '')
    
    if admin_id and user_id != admin_id:
        await update.message.reply_text("⚠️ 관리자만 사용할 수 있는 명령어입니다.")
        return
    
    result = homework_manager.advance_week()
    await update.message.reply_text(f"🔄 {result}")

async def submit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """과제 제출 명령어"""
    message_parts = update.message.text.split(' ', 1)
    
    if len(message_parts) < 2:
        await update.message.reply_text("""📤 과제 제출 방법

**사용법:** `/submit [과제내용]`

**예시:**
```
/submit 
프롬프트: "마케팅 매니저로서 월간 보고서를 작성해줘"
결과: [ChatGPT 응답 내용]
느낀점: 역할 설정으로 더 구체적인 답변을 얻을 수 있었음
```

**주의사항:**
• 사용한 프롬프트와 결과를 모두 포함해주세요
• 한 번에 모든 내용을 보내주세요
• 너무 긴 경우 여러 번 나누어 제출 가능""")
        return
    
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    homework_content = message_parts[1]
    
    result = homework_manager.submit_homework(user_id, user_name, homework_content)
    await update.message.reply_text(result)

async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """진도 확인 명령어"""
    user_id = str(update.effective_user.id)
    progress_data = homework_manager.get_student_progress(user_id)
    
    if "error" in progress_data:
        await update.message.reply_text(f"""📊 학습 진도 현황

{progress_data['error']}

🚀 **시작 방법:**
1. `/homework` - 현재 과제 확인
2. 과제 실습 후 `/submit`으로 제출
3. `/progress`로 진도 확인

📚 **현재 과제:** `/homework` 명령어로 확인하세요!""")
        return
    
    submissions = progress_data["submissions"]
    total = progress_data["total_submissions"]
    
    submission_list = []
    for key, data in submissions.items():
        week, lesson = key.split('_')
        submitted_date = data["submitted_at"][:10]  # YYYY-MM-DD만 표시
        submission_list.append(f"• {week}주차 {lesson}강 - {submitted_date}")
    
    response = f"""📊 **{progress_data['name']}님의 학습 진도**

✅ **총 제출 횟수:** {total}회

📚 **제출 내역:**
{chr(10).join(submission_list) if submission_list else '• 아직 제출한 과제가 없습니다.'}

🎯 **현재 과제:** `/homework` 명령어로 확인
📤 **과제 제출:** `/submit [내용]`

계속 열심히 하세요! 🚀"""
    
    await update.message.reply_text(response)

async def practice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """랜덤 연습 과제"""
    practice_hw = homework_manager.get_random_practice_homework()
    
    response = f"""🎲 **랜덤 연습 과제**

🎯 **{practice_hw['title']}**

{practice_hw['description']}

⏱️ **예상 소요시간:** {practice_hw['estimated_time']}
📊 **난이도:** {practice_hw['difficulty']}

💡 **제출:** 연습이므로 자유롭게!
🔄 **새 과제:** `/practice` 명령어 재실행"""
    
    await update.message.reply_text(response)

async def template_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """프롬프트 템플릿 생성"""
    message_parts = update.message.text.split(' ', 1)
    
    if len(message_parts) < 2:
        await update.message.reply_text("""📋 프롬프트 템플릿 생성기

**사용법:** `/template [주제]`

**예시:**
• `/template 보고서` - 보고서 작성 템플릿
• `/template 이메일` - 이메일 작성 템플릿
• `/template 태양광` - 태양광 분석 템플릿
• `/template 데이터분석` - 데이터 분석 템플릿

🎯 **팜솔라 특화 주제:**
• `/template 발전량계산`
• `/template 효율분석`
• `/template 경제성검토`

주제를 입력하시면 실무에서 바로 사용할 수 있는 프롬프트 템플릿을 만들어드립니다!""")
        return
    
    topic = message_parts[1].strip()
    await update.message.reply_text(f"🔄 '{topic}' 템플릿을 생성하고 있습니다...")
    
    response, ai_model = await ai_handler.generate_prompt_template(topic)
    await update.message.reply_text(f"{response}\n\n📝 Generated by 🧠 {ai_model}")

async def solar_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """태양광 계산기 가이드"""
    calc_text = """🌞 **태양광 발전량 계산기**

💡 **즉시 계산:**
`/calc [용량]kW [지역] [각도]`

**예시:**
• `/calc 100kW 서울` - 서울 100kW 시스템
• `/calc 50kW 부산 25도` - 부산 50kW, 25도 각도
• `/calc 200kW 광주 30도` - 광주 200kW, 30도 각도

📊 **자세한 분석 요청:**
메시지로 직접 요청하세요:
"100kW 서울에 30도 각도로 설치할 때 태양광 발전량과 경제성을 상세히 분석해줘"

🔧 **분석 포함 항목:**
• 연간/월별 발전량 예측
• 경제성 분석 (투자비, 수익, 회수기간)
• 효율 최적화 방안
• 지역별 특성 고려사항
• 설치 조건 개선 제안

⚡ **지원 지역:** 전국 주요 도시
📈 **정확도:** 실무 활용 가능 수준

지금 바로 계산해보세요!"""
    await update.message.reply_text(calc_text)

async def quick_calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """빠른 태양광 계산"""
    message_text = update.message.text
    
    # 용량 추출
    capacity_match = re.search(r'(\d+(?:\.\d+)?)kW?', message_text, re.IGNORECASE)
    if not capacity_match:
        await update.message.reply_text("""❌ 용량을 찾을 수 없습니다.

올바른 형식: `/calc [용량]kW [지역]`
예: `/calc 100kW 서울`""")
        return
    
    capacity = float(capacity_match.group(1))
    
    # 지역 추출
    location_keywords = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종']
    location = "서울"  # 기본값
    
    for keyword in location_keywords:
        if keyword in message_text:
            location = keyword
            break
    
    # 각도 추출
    angle_match = re.search(r'(\d+)도', message_text)
    angle = int(angle_match.group(1)) if angle_match else 30
    
    await update.message.reply_text(f"🔄 계산 중... ({capacity}kW, {location}, {angle}도)")
    
    result, ai_model = await ai_handler.calculate_solar_power(capacity, location, angle)
    await update.message.reply_text(f"{result}\n\n🔢 Calculated by 🧠 {ai_model}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """봇 상태 확인"""
    api_status = test_api_connection()
    usage_stats = ai_handler.get_usage_stats()
    
    status_text = f"""🔍 **AI_Solarbot 시스템 상태**

🧠 **AI 엔진 상태:**
• Gemini: {'✅ 정상' if api_status['gemini'] else '❌ 오류'}
• ChatGPT: {'✅ 정상' if api_status['openai'] else '❌ 오류'}

📊 **오늘 사용량:**
• Gemini: {usage_stats['daily_gemini']}/1400회 ({usage_stats['gemini_remaining']}회 남음)
• ChatGPT: {usage_stats['daily_chatgpt']}회

📈 **총 누적 사용량:**
• Gemini: {usage_stats['total_gemini']}회
• ChatGPT: {usage_stats['total_chatgpt']}회

⚡ **활성 기능:**
• AI 대화 (Gemini 우선)
• 태양광 발전량 계산
• 프롬프트 템플릿 생성
• 과제 관리 시스템
• 실무 강의 지원

🔗 **봇 정보:**
• 버전: v2.0 (Gemini + ChatGPT)
• 사용자명: @{BOT_USERNAME}
• 상태: 정상 운영

{f'⚠️ 오류: {api_status["error_messages"]}' if api_status["error_messages"] else ''}"""
    
    await update.message.reply_text(status_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """전체 학생 통계 확인 (관리자용)"""
    user_id = str(update.effective_user.id)
    admin_id = os.getenv('ADMIN_USER_ID', '')
    
    if admin_id and user_id != admin_id:
        await update.message.reply_text("⚠️ 관리자만 사용할 수 있는 명령어입니다.")
        return
    
    stats = homework_manager.get_submission_stats()
    
    response = f"""📊 **전체 학생 통계**

📚 **현재 과제:** {stats['current_homework']}
👥 **등록 학생 수:** {stats['total_students']}명
✅ **제출 학생 수:** {stats['submitted_count']}명
📈 **제출률:** {stats['submission_rate']}%

🛠️ **관리 명령어:**
• `/next` - 다음 과제로 진행
• `/stats` - 통계 재확인
• `/broadcast [메시지]` - 전체 공지 (추후 추가)

🚨 **제출률 70% 이상시 자동 진행 가능**"""
    
    await update.message.reply_text(response)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """일반 메시지 처리 - AI 연동"""
    user_message = update.message.text
    user_name = update.effective_user.first_name
    
    # 태양광 계산 요청 감지
    if any(keyword in user_message.lower() for keyword in ['태양광', 'solar', '발전량', '계산']) and 'kw' in user_message.lower():
        # 숫자와 kW가 포함된 경우 자동 계산
        capacity_match = re.search(r'(\d+(?:\.\d+)?)kW?', user_message, re.IGNORECASE)
        if capacity_match:
            await update.message.reply_text("🔄 태양광 발전량을 계산해드릴게요...")
            capacity = float(capacity_match.group(1))
            
            # 지역 감지
            location_keywords = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종']
            location = "서울"
            for keyword in location_keywords:
                if keyword in user_message:
                    location = keyword
                    break
            
            result, ai_model = await ai_handler.calculate_solar_power(capacity, location)
            safe_result = safe_markdown(result)
            await update.message.reply_text(f"{safe_result}\n\n*Calculated by 🧠 {ai_model}*", parse_mode='Markdown')
            return
    
    # 일반 AI 대화
    await update.message.reply_text("🤖 생각 중...")
    response, ai_model = await ai_handler.chat_with_ai(user_message, user_name)
    # 안전한 마크다운 처리
    safe_response = safe_markdown(response)
    await update.message.reply_text(f"{safe_response}\n\n*Powered by 🧠 {ai_model}*", parse_mode='Markdown')

async def upload_homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """과제 파일 업로드 명령어"""
    message_parts = update.message.text.split(' ', 1)
    
    if len(message_parts) < 2:
        await update.message.reply_text("""📤 과제 파일 업로드 방법

**사용법:** `/upload_homework [과제명]`

**예시:**
• `/upload_homework 1주차2번째` - 1주차 2번째 과제
• `/upload_homework 프롬프트기초` - 프롬프트 기초 과제

**과제 파일 위치:**
```
수업/
├── 6주/3. 교과서/1주차2번째/1주차과제.html
├── 12주/3. 교과서/2주차1번째/2주차과제.html
└── ...
```

**지원 형식:** HTML, PDF, MD 파일
**자동 감지:** 파일명에서 주차/차수 자동 인식

과제명을 입력하시면 해당 과제 파일을 찾아서 업로드해드립니다!""")
        return
    
    homework_name = message_parts[1].strip()
    
    # 과제 파일 경로 패턴들
    possible_paths = [
        f"수업/6주/3. 교과서/{homework_name}/{homework_name}과제.html",
        f"수업/12주/3. 교과서/{homework_name}/{homework_name}과제.html",
        f"수업/1년/3. 교과서/{homework_name}/{homework_name}과제.html",
        f"수업/6주/3. 교과서/{homework_name}.html",
        f"수업/12주/3. 교과서/{homework_name}.html",
    ]
    
    # 파일 찾기
    found_file = None
    for path in possible_paths:
        if os.path.exists(path):
            found_file = path
            break
    
    if found_file:
        try:
            # 파일 크기 확인 (텔레그램 메시지 길이 제한)
            file_size = os.path.getsize(found_file)
            if file_size > 50000:  # 50KB 이상이면 요약
                await update.message.reply_text(f"""📁 **과제 파일 발견**: `{homework_name}`

📊 **파일 정보:**
• 경로: {found_file}
• 크기: {file_size:,} bytes
• 상태: ✅ 업로드 가능

⚠️ **파일이 큽니다** (50KB 초과)
전체 내용 대신 **요약본**을 제공할까요?

**선택사항:**
• /upload_homework """ + homework_name + """ full - 전체 내용
• /upload_homework """ + homework_name + """ summary - 요약본만
• /upload_homework """ + homework_name + """ structure - 구조만""")
            else:
                # 파일 내용 읽기
                with open(found_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                message_text = f"📋 **{homework_name} 과제**\n\n"
                message_text += f"📁 **파일**: {found_file}\n\n"
                message_text += content[:3000]
                if len(content) > 3000:
                    message_text += "...\n\n*[내용이 길어 일부만 표시됩니다]*"
                message_text += "\n\n💡 **추가 명령어:**\n"
                message_text += "• /homework - 현재 과제 확인\n"
                message_text += "• /submit [답안] - 과제 제출\n"
                message_text += "• /template [주제] - 관련 템플릿 생성"
                
                await update.message.reply_text(message_text)
                
        except Exception as e:
            await update.message.reply_text(f"❌ 파일 읽기 오류: {str(e)}")
    else:
        error_message = f"❌ **'{homework_name}' 과제 파일을 찾을 수 없습니다**\n\n"
        error_message += "🔍 **검색된 경로들:**\n"
        error_message += chr(10).join(f'• {path}' for path in possible_paths)
        error_message += "\n\n💡 **제안:**\n"
        error_message += "• 정확한 과제명 확인 (예: `1주차2번째`)\n"
        error_message += "• 파일 경로 확인\n"
        error_message += "• /homework 로 현재 과제 목록 확인\n\n"
        error_message += "📁 **현재 과제 폴더 구조:**\n"
        error_message += "```\n수업/6주/3. 교과서/\n├── 1주차1번째/\n├── 1주차2번째/\n├── 2주차1번째/\n└── ...\n```"
        
        await update.message.reply_text(error_message)

async def explain_homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """과제 설명 명령어"""
    message_parts = update.message.text.split(' ', 1)
    
    if len(message_parts) < 2:
        await update.message.reply_text("""📚 과제 설명 요청 방법

**사용법:** `/explain_homework [과제명 또는 과제내용]`

**예시:**
• `/explain_homework 1주차2번째` - 특정 과제 설명
• `/explain_homework 프롬프트 작성법` - 주제별 설명

**자동 연계:**
• `/upload 1주차2번째` → `/explain_homework 1주차2번째`
• 과제 파일 업로드 후 자동 설명 제공

**설명 내용:**
• 📚 과제 개요 및 목적
• 🎯 학습 목표
• 📋 단계별 풀이 가이드
• 💡 실무 활용 팁
• ⚠️ 주의사항
• ⏱️ 예상 소요시간

과제명이나 설명이 필요한 내용을 입력해주세요!""")
        return
    
    homework_input = message_parts[1].strip()
    user_name = update.effective_user.first_name
    
    # 과제 파일에서 내용 찾기 시도
    possible_paths = [
        f"수업/6주/3. 교과서/{homework_input}/{homework_input}과제.html",
        f"수업/12주/3. 교과서/{homework_input}/{homework_input}과제.html",
        f"수업/1년/3. 교과서/{homework_input}/{homework_input}과제.html",
        f"과제/{homework_input}/과제.html",
    ]
    
    homework_content = homework_input  # 기본값: 입력된 텍스트
    found_file = None
    
    # 파일에서 과제 내용 찾기
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    # HTML에서 텍스트 추출 (간단한 방법)
                    import re
                    text_content = re.sub(r'<[^>]+>', '', file_content)
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    homework_content = text_content[:2000]  # 처음 2000자만
                    found_file = path
                    break
            except:
                continue
    
    await update.message.reply_text(f"🔄 '{homework_input}' 과제를 분석하고 설명을 생성하고 있습니다...")
    
    explanation, ai_model = await ai_handler.explain_homework(homework_content, user_name)
    
    response = f"📚 **{homework_input} 과제 설명**\n\n"
    if found_file:
        response += f"📁 **분석 파일**: {found_file}\n\n"
    else:
        response += "📝 **분석 내용**: 입력된 텍스트\n\n"
    response += explanation + "\n\n"
    response += "💡 **추가 도움말:**\n"
    response += "• /template [주제] - 관련 프롬프트 템플릿\n"
    response += "• /submit [답안] - 과제 제출\n"
    response += "• /practice - 연습 과제\n\n"
    response += "\n\n📚 Generated by 🧠 " + ai_model
    
    await update.message.reply_text(response)

def main() -> None:
    """메인 함수"""
    if not BOT_TOKEN:
        print("ERROR: 봇 토큰이 설정되지 않았습니다!")
        return
    
    print(f"Starting {BOT_USERNAME} bot with Gemini + ChatGPT...")
    
    # 애플리케이션 생성
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 기본 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", track_command(start)))
    application.add_handler(CommandHandler("help", track_command(help_command)))
    application.add_handler(CommandHandler("homework", track_command(homework_command)))
    application.add_handler(CommandHandler("submit", track_command(submit_command)))
    application.add_handler(CommandHandler("progress", track_command(progress_command)))
    application.add_handler(CommandHandler("practice", track_command(practice_command)))
    application.add_handler(CommandHandler("template", track_command(template_command)))
    application.add_handler(CommandHandler("solar", track_command(solar_calculator)))
    application.add_handler(CommandHandler("calc", track_command(quick_calc_command)))
    application.add_handler(CommandHandler("status", track_command(status_command)))
    application.add_handler(CommandHandler("stats", track_command(stats_command)))
    application.add_handler(CommandHandler("next", track_command(next_command)))
    
    # 관리자 전용 명령어 핸들러 등록
    application.add_handler(CommandHandler("admin", admin_dashboard))
    application.add_handler(CommandHandler("admin_dashboard", admin_dashboard))
    application.add_handler(CommandHandler("admin_report", admin_report))
    application.add_handler(CommandHandler("admin_users", admin_users))
    application.add_handler(CommandHandler("admin_backup", admin_backup))
    application.add_handler(CommandHandler("admin_cleanup", admin_cleanup))
    application.add_handler(CommandHandler("admin_broadcast", admin_broadcast))
    application.add_handler(CommandHandler("admin_broadcast_confirm", admin_broadcast_confirm))
    application.add_handler(CommandHandler("admin_restart", admin_restart))
    application.add_handler(CommandHandler("admin_restart_confirm", admin_restart_confirm))
    
    # 일반 메시지 핸들러
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 과제 파일 업로드 명령어 추가
    application.add_handler(CommandHandler("upload_homework", track_command(upload_homework_command)))
    application.add_handler(CommandHandler("upload", track_command(upload_homework_command)))  # 단축 명령어
    
    # 과제 설명 명령어 추가
    application.add_handler(CommandHandler("explain_homework", track_command(explain_homework_command)))
    application.add_handler(CommandHandler("explain", track_command(explain_homework_command)))  # 단축 명령어
    
    # 봇 실행
    print(f"SUCCESS: {BOT_USERNAME} bot is ready with full AI integration!")
    print("Bot URL: https://t.me/AI_Solarbot")
    print("Features: Gemini + ChatGPT, Solar Calculator, Homework System")
    print("Press Ctrl+C to stop.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
