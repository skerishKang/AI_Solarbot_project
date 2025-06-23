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
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from ai_handler import ai_handler, test_api_connection
from homework_manager import HomeworkManager
from cloud_homework_manager import cloud_homework_manager
from monitoring import bot_monitor, track_command
from google_drive_handler import drive_handler, test_drive_connection
from user_drive_manager import user_drive_manager
from email_manager import EmailManager
from report_manager import ReportManager
from user_auth_manager import user_auth_manager
from admin_commands import (
    admin_dashboard, admin_report, admin_users, admin_backup, 
    admin_cleanup, admin_broadcast, admin_broadcast_confirm,
    admin_restart, admin_restart_confirm
)

# 자연어 기반 IDE 처리를 위한 import 추가
from natural_ide import natural_ide

# 웹 검색 IDE 기능 import 추가
from web_search_ide import web_search_ide

# 실시간 동기화 시스템 import 추가
from polling_sync import initialize_polling_sync, get_polling_sync_manager

# Apps Script 대체 시스템 import 추가
from apps_script_alternative import initialize_apps_script_alternative, get_apps_script_alternative

# 협업 기능 import 추가
from collaboration_manager import collaboration_manager

# 최신 기술 정보 업데이트 시스템 import 추가
from tech_info_updater import tech_updater

# 확장된 온라인 코드 실행 시스템 import 추가
from online_code_executor import online_code_executor

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

# 이메일 관리자 인스턴스
email_manager = EmailManager()

# 업무보고 관리자 인스턴스
report_manager = ReportManager()

# 사용자별 이메일 상태 저장
user_email_states = {}  # {user_id: {'pending_reply': email_data, 'awaiting_reply': bool}}

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

🧠 **AI 엔진 상태:**
• Gemini {gemini_status} (오늘 {usage_stats['daily_gemini']}/1400회 사용)
• ChatGPT {chatgpt_status} (백업용)

📋 **주요 명령어:**
• `/commands` - 📝 모든 명령어 목록
• `/help` - 📖 상세 도움말
• `/homework` - 📚 현재 과제 확인
• `/model` - 🤖 AI 모델 선택
• `/solar` - ☀️ 태양광 계산
• `/email` - 📧 이메일 관리
• `/drive` - 📁 구글 드라이브
• `/status` - 🔧 봇 상태 확인

💬 **자유 대화:**
그냥 메시지를 보내면 AI와 대화할 수 있어요!

**💡 팁:** `/commands`로 모든 명령어를 확인하세요!

시작해볼까요? 🚀"""
    await update.message.reply_text(welcome_message)

async def commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """모든 명령어 목록"""
    commands_text = """📝 **AI_Solarbot 명령어 목록**

🎯 **기본 명령어:**
• `/start` - 봇 시작 및 환영 메시지
• `/help` - 상세 도움말 보기
• `/commands` - 이 명령어 목록 보기

🤖 **AI 모델 선택:**
• `/model` - 현재 모델 확인 및 선택 옵션
• `/model 2.0` - Gemini 2.0 (빠른 균형형)
• `/model 2.5` - Gemini 2.5 (최고 정확도)
• `/model gpt` - GPT-4o (창의적 답변)

📚 **강의 지원:**
• `/homework` - 현재 과제 확인
• `/homework [주차] [강]` - 특정 과제 확인
• `/submit [내용]` - 과제 제출
• `/progress` - 제출 현황 확인
• `/template [주제]` - 프롬프트 템플릿 생성
• `/practice` - 랜덤 연습 과제
• `/upload [과제명]` - 과제 파일 업로드
• `/explain [과제명]` - 과제 설명

☀️ **태양광 계산:**
• `/solar` - 태양광 계산 가이드
• `/calc [용량]kW [지역]` - 즉시 발전량 계산

📧 **이메일 관리:**
• `/email` - 이메일 기능 안내
• `/email_connect` - Gmail 연결
• `/email_check` - 새 이메일 확인
• `/email_reply [메시지]` - 답장 보내기

📁 **구글 드라이브:**
• `/drive` - 드라이브 기능 안내
• `/drive_list` - 파일 목록 보기
• `/drive_read [파일명]` - 파일 내용 읽기
• `/drive_create [파일명] [내용]` - 파일 생성
• `/drive_update [파일ID] [새내용]` - 파일 수정

💻 **클라우드 IDE:**
• `/connect_drive` - 개인 드라이브 연결
• `/drive_status` - 연결 상태 확인
• `/tree` - 파일 트리 보기
• `/mkdir [폴더명]` - 새 폴더 생성
• `/workspace` - 워크스페이스 상태 확인
• `/create_workspace` - 팜솔라 워크스페이스 생성
• `/edit [파일명] [내용]` - 파일 편집
• `/cat [파일명]` - 파일 내용 보기
• `/touch [파일명]` - 새 파일 생성
• `/rm [파일명]` - 파일 삭제
• `/mv [원본] [대상]` - 파일 이동/이름변경
• `/cp [원본] [대상]` - 파일 복사
• `/run [파일명]` - 코드 실행 (추후 구현)
• `/disconnect_drive` - 드라이브 연결 해제

🔍 **웹 검색 & 코드 테스트:**
• `/search [검색어]` - 개발 관련 웹 검색
• `/visit [URL]` - 사이트 방문 및 코드 추출
• `/search_visit [검색어]` - 검색 후 자동 사이트 방문
• `/test_code [코드]` - 온라인 코드 실행 테스트
• `/snippets [언어]` - 수집된 코드 스니펫 보기
• `/search_history` - 검색 기록 확인

🤖 **고급 웹 자동화:**
• `/auto_visit [URL]` - 고급 자동화 사이트 방문
• `/screenshot [URL]` - 웹페이지 스크린샷 캡처
• `/click [selector]` - 웹 요소 클릭
• `/type [selector] [text]` - 웹 요소에 텍스트 입력
• `/extract [selectors]` - 동적 콘텐츠 추출
• `/js [script]` - 페이지에서 JavaScript 실행
• `/close_browser` - 브라우저 종료

🚀 **비동기 크롤링 (3-5배 빠름):**
• `/async_crawl [URL1] [URL2] ...` - 다중 URL 동시 크롤링

📡 **최신 기술 정보 업데이트:**
• `/tech_summary` - 📊 전체 기술 정보 요약
• `/github_trending [언어]` - 🔥 GitHub 트렌딩 리포지토리
• `/tech_news` - 📰 최신 기술 뉴스 (RSS 피드)
• `/stackoverflow [태그]` - ❓ Stack Overflow 인기 질문
• `/package_info [패키지명] [npm/pypi]` - 📦 패키지 최신 정보
• `/tech_auto_update` - 🔄 자동 업데이트 설정

💻 **확장된 코드 실행 (10개 언어):**
• `/run_code [언어] [코드]` - 💾 코드 실행 (Python, JS, Java, C++, Go, Rust, PHP, Ruby, C#, TypeScript)
• `/supported_languages` - 📋 지원 언어 목록
• `/language_info [언어]` - 📖 특정 언어 정보
• `/code_stats` - 📊 코드 실행 통계
• `/performance_test [언어] [코드]` - ⚡ 성능 분석 테스트
• `/code_history` - 📚 최근 실행 이력
• `/async_search [검색어]` - 검색 기반 비동기 크롤링
• `/crawl_performance [URLs]` - 성능 비교 테스트

🔄 **실시간 동기화:**
• `/sync_status` - 동기화 상태 확인
• `/sync_force` - 강제 동기화 실행
• `/sync_interval [초]` - 폴링 간격 설정
• `/test_sync` - 동기화 시스템 종합 테스트

🤝 **팀 협업:**
• `/team` - 팀 기능 안내
• `/team_create [팀명]` - 팀 워크스페이스 생성
• `/team_invite [팀ID] [멤버ID]` - 팀원 초대
• `/team_list` - 내 팀 목록
• `/team_comment [팀ID] [파일] [댓글]` - 파일 댓글 추가
• `/team_comments [팀ID] [파일]` - 파일 댓글 보기
• `/team_activity [팀ID]` - 팀 활동 내역
• `/instructor_dashboard` - 강사용 모니터링

📋 **업무보고:**
• `/report` - 업무보고 시작
• `/report_status` - 진행 상황 확인
• `/report_complete` - 보고서 완료/전송
• `/report_list` - 내 보고서 목록
• `/report_view [ID]` - 특정 보고서 보기

🔧 **시스템:**
• `/status` - 봇 상태 및 사용량 확인

⚙️ **관리자 전용:**
• `/admin` - 관리자 대시보드
• `/next` - 다음 주차로 진행

💡 **사용법 예시:**
• `/model` → 현재 AI 모델 확인
• `/homework 2 1` → 2주차 1강 과제 보기
• `/calc 100kW 서울` → 서울 100kW 발전량 계산
• `/template 마케팅` → 마케팅 프롬프트 템플릿

더 자세한 설명은 `/help`를 입력하세요! 📖"""
    await update.message.reply_text(commands_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """상세 도움말"""
    help_text = """🤖 **AI_Solarbot 상세 가이드**

📚 **강의 지원 기능:**
• `/homework` - 현재 주차 과제 확인
• `/homework [주차] [강]` - 특정 과제 확인 (예: /homework 2 1)
• `/upload [과제명]` - 과제 파일 업로드 및 분석 (예: /upload 1주차2번째)
• `/explain [과제명]` - 과제 자세한 설명 제공 (예: /explain 프롬프트기초)
• `/submit [과제내용]` - 과제 제출하기
• `/progress` - 내 제출 현황 확인
• `/template [주제]` - 맞춤 프롬프트 템플릿 생성
• `/practice` - 랜덤 연습 과제

🤖 **AI 모델 선택:**
• `/model` - 현재 모델 확인 및 선택 메뉴
• `/model 2.0` - Gemini 2.0-flash-exp (빠른 응답, 균형잡힌 성능)
• `/model 2.5` - Gemini 2.5-flash (최고 정확도, 상세한 분석)
• `/model gpt` - GPT-4o (창의적 답변, 다양한 관점)

☀️ **태양광 전문 기능:**
• `/solar` - 태양광 계산 가이드
• `/calc [용량]kW [지역] [각도]` - 즉시 계산
  예: `/calc 100kW 서울`, `/calc 50kW 부산 25도`

🧠 **AI 대화 특징:**
• 일반 메시지 → 선택한 AI 모델로 자동 응답
• 태양광 키워드 감지 → 전문 분석 제공
• 프롬프트 관련 질문 → 맞춤 가이드 제공
• 사용자별 개별 모델 설정 저장

🔧 **시스템 기능:**
• `/status` - AI 엔진 상태 및 사용량
• `/commands` - 모든 명령어 목록
• `/next` - 다음 주차로 진행 (관리자용)

⚙️ **관리자 기능:**
• `/admin` - 관리자 대시보드 (관리자 전용)
• `/admin_report` - 일일 사용량 리포트
• `/admin_backup` - 데이터 백업

💡 **사용 팁:**
• 구체적으로 질문할수록 더 정확한 답변
• 태양광 계산 시 지역, 용량, 각도 명시
• 과제 제출 시 프롬프트와 결과 모두 포함
• AI 모델은 언제든 변경 가능 (`/model` 사용)

궁금한 점이 있으면 언제든 물어보세요! 🙋‍♂️"""
    await update.message.reply_text(help_text)

async def homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """과제 관련 명령어 (클라우드 기반)"""
    try:
        # 명령어 추적
        await track_command(update, "homework")
        
        user_id = str(update.effective_user.id)
        
        # 사용자 인증 확인
        if not user_auth_manager.is_authenticated(user_id):
            response = """🔐 **드라이브 연결이 필요합니다**

과제 관리 기능을 사용하려면 먼저 구글 드라이브를 연결해주세요!

📱 **연결 방법:**
1. `/connect_drive` 명령어 실행
2. 제공된 링크로 구글 인증
3. 인증 코드 입력

연결 후 개인 드라이브에서 과제를 관리할 수 있습니다! 🚀"""
            await update.message.reply_text(response)
            return
        
        # 클라우드 과제 관리자에서 현재 과제 가져오기
        homework_result = cloud_homework_manager.get_current_homework(user_id)
        
        if homework_result["success"]:
            response = homework_result["message"]
            
            # AI 자동 검토 기준 추가 안내
            if "ai_review_criteria" in homework_result.get("homework", {}):
                criteria = homework_result["homework"]["ai_review_criteria"]
                response += f"\n\n🤖 **AI 자동 검토 기준:**\n"
                for criterion in criteria:
                    response += f"• {criterion}\n"
                response += "\n💡 제출 후 AI가 자동으로 검토하고 피드백을 제공합니다!"
        else:
            response = f"❌ {homework_result['error']}"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Homework command error: {e}")
        await update.message.reply_text("❌ 과제 정보를 가져오는 중 오류가 발생했습니다.")

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
    """과제 제출 명령어 (클라우드 기반)"""
    try:
        # 명령어 추적
        await track_command(update, "submit")
        
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name
        
        # 사용자 인증 확인
        if not user_auth_manager.is_authenticated(user_id):
            response = """🔐 **드라이브 연결이 필요합니다**

과제 제출을 위해서는 먼저 구글 드라이브를 연결해주세요!

📱 **연결 방법:**
1. `/connect_drive` 명령어 실행
2. 제공된 링크로 구글 인증
3. 인증 코드 입력

연결 후 과제를 개인 드라이브에 자동 저장합니다! 🚀"""
            await update.message.reply_text(response)
            return
        
        message_parts = update.message.text.split(' ', 1)
        
        if len(message_parts) < 2:
            await update.message.reply_text("""📤 **클라우드 과제 제출 방법**

**사용법:** `/submit [과제내용]`

**예시:**
```
/submit 
프롬프트: "마케팅 매니저로서 월간 보고서를 작성해줘"
결과: [ChatGPT 응답 내용]
느낀점: 역할 설정으로 더 구체적인 답변을 얻을 수 있었음
```

**클라우드 제출의 장점:**
• 📁 구글 드라이브에 자동 저장
• 🤖 AI 자동 검토 및 피드백
• 📊 실시간 진도 관리
• 🔗 웹에서 언제든 확인 가능

**주의사항:**
• 사용한 프롬프트와 결과를 모두 포함해주세요
• 한 번에 모든 내용을 보내주세요
• 제출 후 AI 피드백을 확인하세요!""")
            return
        
        homework_content = message_parts[1]
        
        # 클라우드 과제 제출
        submit_result = cloud_homework_manager.submit_homework(user_id, user_name, homework_content)
        
        if submit_result["success"]:
            # 제출 성공 시 AI 자동 검토 실행
            current_homework = cloud_homework_manager.get_current_homework(user_id)
            if current_homework["success"]:
                ai_review = cloud_homework_manager.get_ai_homework_review(
                    user_id, homework_content, current_homework["homework"]
                )
                
                response = submit_result["message"]
                if ai_review["success"]:
                    response += f"\n\n{ai_review['feedback']}"
            else:
                response = submit_result["message"]
        else:
            response = f"❌ {submit_result['error']}"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Submit command error: {e}")
        await update.message.reply_text("❌ 과제 제출 중 오류가 발생했습니다.")

async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """진도 확인 명령어 (클라우드 기반)"""
    try:
        # 명령어 추적
        await track_command(update, "progress")
        
        user_id = str(update.effective_user.id)
        
        # 사용자 인증 확인
        if not user_auth_manager.is_authenticated(user_id):
            response = """🔐 **드라이브 연결이 필요합니다**

진도 확인을 위해서는 먼저 구글 드라이브를 연결해주세요!

📱 **연결 방법:**
1. `/connect_drive` 명령어 실행
2. 제공된 링크로 구글 인증
3. 인증 코드 입력

연결 후 클라우드에서 진도를 관리할 수 있습니다! 🚀"""
            await update.message.reply_text(response)
            return
        
        # 클라우드에서 진도 데이터 가져오기
        progress_result = cloud_homework_manager.get_student_progress(user_id)
        
        if progress_result["success"]:
            response = progress_result["message"]
            response += "\n\n📁 **클라우드 진도 관리의 장점:**\n"
            response += "• 실시간 동기화\n"
            response += "• 웹에서 언제든 확인\n"
            response += "• AI 자동 분석\n"
            response += "• 강사와 실시간 공유\n"
            response += "\n🎯 **현재 과제:** `/homework` 명령어로 확인"
        else:
            response = f"""📊 **클라우드 학습 진도**

❌ {progress_result['error']}

🚀 **시작 방법:**
1. `/homework` - 현재 과제 확인
2. 과제 실습 후 `/submit`으로 제출
3. `/progress`로 진도 확인

📚 **현재 과제:** `/homework` 명령어로 확인하세요!"""
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Progress command error: {e}")
        await update.message.reply_text("❌ 진도 확인 중 오류가 발생했습니다.")

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

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI 모델 선택 명령어"""
    message_parts = update.message.text.split(' ', 1)
    user_id = str(update.effective_user.id)
    
    if len(message_parts) < 2:
        # 현재 모델과 사용 가능한 모델 목록 표시
        current_model = ai_handler.get_user_model(user_id)
        available_models = ai_handler.get_available_models()
        
        response = f"🤖 **AI 모델 선택**\n\n"
        response += f"**현재 선택된 모델:** {available_models.get(current_model, current_model)}\n\n"
        response += "**사용 가능한 모델들:**\n"
        
        for model_key, model_desc in available_models.items():
            status = "✅ **현재 사용 중**" if model_key == current_model else ""
            response += f"• `/model {model_key.split('-')[1]}` - {model_desc} {status}\n"
        
        response += "\n**사용법:**\n"
        response += "• `/model 2.0` - padiem 2.0으로 변경\n"
        response += "• `/model 2.5` - padiem 2.5로 변경\n"
        response += "• `/model gpt` - padiem GPT로 변경\n\n"
        response += "**모델별 특징:**\n"
        response += "🧠 **padiem 2.0**: 빠른 응답, 균형잡힌 성능\n"
        response += "🧠 **padiem 2.5**: 최고 정확도, 생각 모드 포함\n"
        response += "🧠 **padiem GPT**: OpenAI 최신 모델, 창의적 답변"
        
        await update.message.reply_text(response)
        return
    
    # 모델 변경 처리
    model_input = message_parts[1].strip().lower()
    
    # 입력값을 실제 모델명으로 변환
    model_mapping = {
        '2.0': 'gemini-2.0-flash-exp',
        '20': 'gemini-2.0-flash-exp',
        'gemini2.0': 'gemini-2.0-flash-exp',
        '2.5': 'gemini-2.5-flash',
        '25': 'gemini-2.5-flash',
        'gemini2.5': 'gemini-2.5-flash',
        'gpt': 'gpt-4o',
        'gpt4': 'gpt-4o',
        'gpt-4o': 'gpt-4o',
        'chatgpt': 'gpt-4o'
    }
    
    selected_model = model_mapping.get(model_input)
    
    if selected_model:
        success = ai_handler.set_user_model(user_id, selected_model)
        if success:
            available_models = ai_handler.get_available_models()
            model_desc = available_models.get(selected_model, selected_model)
            await update.message.reply_text(f"✅ **AI 모델이 변경되었습니다!**\n\n새로운 모델: {model_desc}\n\n이제 이 모델로 대화해보세요! 💬")
        else:
            await update.message.reply_text("❌ 모델 변경에 실패했습니다.")
    else:
        await update.message.reply_text(f"❌ **'{model_input}'은(는) 유효하지 않은 모델입니다.**\n\n**사용 가능한 옵션:**\n• `2.0` - padiem 2.0\n• `2.5` - padiem 2.5\n• `gpt` - padiem GPT\n\n**예시:** `/model 2.5`")

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
    user_id = str(update.effective_user.id)
    
    # 업무보고 진행 중인지 확인
    active_report = report_manager.get_active_report(user_id)
    if active_report:
        # 보고서 응답 처리
        result = report_manager.add_response(user_id, user_message)
        
        if 'error' in result:
            response = f"❌ {result['error']}"
        elif result.get('completed'):
            # 보고서 완료
            response = f"""🎉 **보고서 작성 완료!**

✅ **{result['message']}**

📋 **완료된 보고서:** {result['report']['template']['name']}
🆔 **보고서 ID:** {result['report']['report_id']}

**다음 단계:**
• `/report_complete` - 관리자에게 전송
• `/report_list` - 내 보고서 목록 확인"""
        else:
            # 다음 질문
            next_question = result['next_question']
            progress = result['progress']
            
            response = f"""✅ **답변이 저장되었습니다!**

📊 **진행률:** {progress}

❓ **다음 질문:**
{next_question}

💡 위 질문에 답변을 입력해주세요!"""
        
        await update.message.reply_text(response)
        return
    
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
    response, ai_model = await ai_handler.chat_with_ai(user_message, user_name, user_id)
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
    
    # 구글 드라이브에서 과제 파일 검색
    search_patterns = [
        f"{homework_name}과제",
        f"{homework_name}",
        homework_name.replace("주차", "주").replace("번째", "")
    ]
    
    found_content = None
    file_info = None
    
    # 구글 드라이브에서 과제 파일 찾기
    for pattern in search_patterns:
        try:
            files = drive_handler.search_files(pattern)
            if files:
                # 첫 번째 검색 결과 사용
                file_id = files[0]['id']
                result = drive_handler.read_file_content(file_id)
                
                if 'error' not in result:
                    found_content = result['content']
                    file_info = {
                        'name': result['file_name'],
                        'id': file_id,
                        'size': len(found_content)
                    }
                    break
        except Exception:
            continue
    
    if found_content and file_info:
        try:
            if file_info['size'] > 50000:  # 50KB 이상이면 요약
                await update.message.reply_text(f"""📁 **과제 파일 발견**: `{homework_name}`

📊 **파일 정보:**
• 이름: {file_info['name']}
• 크기: {file_info['size']:,} bytes
• 상태: ✅ 분석 가능

⚠️ **파일이 큽니다** (50KB 초과)
전체 내용 대신 **요약본**을 제공할까요?

**선택사항:**
• /upload_homework """ + homework_name + """ full - 전체 내용
• /upload_homework """ + homework_name + """ summary - 요약본만
• /upload_homework """ + homework_name + """ structure - 구조만""")
            else:
                message_text = f"📋 **{homework_name} 과제**\n\n"
                message_text += f"📁 **구글 드라이브 파일**: {file_info['name']}\n\n"
                message_text += found_content[:3000]
                if len(found_content) > 3000:
                    message_text += "...\n\n*[내용이 길어 일부만 표시됩니다]*"
                message_text += "\n\n💡 **추가 명령어:**\n"
                message_text += "• /homework - 현재 과제 확인\n"
                message_text += "• /submit [답안] - 과제 제출\n"
                message_text += "• /template [주제] - 관련 템플릿 생성"
                
                await update.message.reply_text(message_text)
                
        except Exception as e:
            await update.message.reply_text(f"❌ 파일 처리 오류: {str(e)}")
    else:
        error_message = f"❌ **'{homework_name}' 과제 파일을 찾을 수 없습니다**\n\n"
        error_message += "🔍 **검색 위치:** 구글 드라이브\n"
        error_message += f"🔍 **검색 패턴:** {', '.join(search_patterns)}\n\n"
        error_message += "💡 **해결 방법:**\n"
        error_message += "• `/connect_drive`로 개인 드라이브 연결\n"
        error_message += "• 팜솔라 교과서 폴더가 드라이브에 있는지 확인\n"
        error_message += "• `/drive_list`로 사용 가능한 파일 확인\n"
        error_message += "• `/homework`로 현재 과제 목록 확인\n\n"
        error_message += "🌟 **클라우드 전용**: 모든 과제는 구글 드라이브에서 관리됩니다"
        
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
    
    # 구글 드라이브에서 과제 내용 찾기 시도
    homework_content = homework_input  # 기본값: 입력된 텍스트
    found_file = None
    
    # 구글 드라이브에서 과제 파일 검색
    search_patterns = [
        f"{homework_input}과제",
        f"{homework_input}",
        homework_input.replace("주차", "주").replace("번째", "")
    ]
    
    for pattern in search_patterns:
        try:
            files = drive_handler.search_files(pattern)
            if files:
                file_id = files[0]['id']
                result = drive_handler.read_file_content(file_id)
                
                if 'error' not in result:
                    file_content = result['content']
                    # HTML에서 텍스트 추출 (간단한 방법)
                    import re
                    text_content = re.sub(r'<[^>]+>', '', file_content)
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    homework_content = text_content[:2000]  # 처음 2000자만
                    found_file = result['file_name']
                    break
        except Exception:
            continue
    
    await update.message.reply_text(f"🔄 '{homework_input}' 과제를 분석하고 설명을 생성하고 있습니다...")
    
    explanation, ai_model = await ai_handler.explain_homework(homework_content, user_name)
    
    response = f"📚 **{homework_input} 과제 설명**\n\n"
    if found_file:
        response += f"📁 **구글 드라이브 파일**: {found_file}\n\n"
    else:
        response += "📝 **분석 내용**: 입력된 텍스트\n\n"
    response += explanation + "\n\n"
    response += "💡 **추가 도움말:**\n"
    response += "• /template [주제] - 관련 프롬프트 템플릿\n"
    response += "• /submit [답안] - 과제 제출\n"
    response += "• /practice - 연습 과제\n\n"
    response += "\n\n📚 Generated by 🧠 " + ai_model
    
    await update.message.reply_text(response)

async def email_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """이메일 기능 안내"""
    email_help = """📧 **이메일 관리 시스템**

🔗 **연결 및 설정:**
• `/email_connect` - Gmail 계정 연결
• `/email_disconnect` - 이메일 모니터링 해제

📬 **이메일 확인:**
• `/email_check` - 새 이메일 확인
• `/email_list` - 최근 이메일 목록

✉️ **답장 기능:**
• `/email_reply [내용]` - 직접 답장 작성
• `/email_ai_reply` - AI가 답장 자동 생성

⚙️ **자동화 기능:**
• `/email_monitor on` - 실시간 이메일 알림 켜기
• `/email_monitor off` - 실시간 이메일 알림 끄기

💡 **사용 예시:**
1. `/email_connect` → Gmail 연결
2. `/email_monitor on` → 자동 알림 활성화
3. 이메일 도착 시 봇이 자동 알림
4. `/email_ai_reply` → AI가 답장 생성
5. 확인 후 전송

🔒 **보안:** 각 사용자별 개별 Gmail 계정 연결"""
    await update.message.reply_text(email_help)

async def email_connect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gmail 계정 연결"""
    user_id = str(update.effective_user.id)
    
    try:
        if email_manager.authenticate_gmail(user_id):
            user_email = email_manager.get_user_email(user_id)
            response = f"""✅ **Gmail 연결 성공!**

📧 **연결된 계정:** {user_email}

🔔 **다음 단계:**
• `/email_monitor on` - 실시간 알림 활성화
• `/email_check` - 새 이메일 확인
• `/email_list` - 이메일 목록 보기

💡 **팁:** 이제 새 이메일이 오면 자동으로 알림을 받을 수 있어요!"""
        else:
            response = """❌ **Gmail 연결 실패**

📋 **필요한 설정:**
1. Google Cloud Console에서 프로젝트 생성
2. Gmail API 활성화
3. OAuth 2.0 클라이언트 ID 생성
4. credentials.json 파일 설정

🔧 **관리자에게 문의하여 Gmail API 설정을 완료해주세요.**"""
            
    except Exception as e:
        response = f"❌ Gmail 연결 중 오류 발생: {str(e)}"
    
    await update.message.reply_text(response)

async def email_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """새 이메일 확인"""
    user_id = str(update.effective_user.id)
    
    try:
        new_emails = email_manager.check_new_emails(user_id)
        
        if not new_emails:
            response = "📭 **새 이메일이 없습니다.**"
        else:
            response = f"📬 **새 이메일 {len(new_emails)}개 발견!**\n\n"
            
            for i, email_data in enumerate(new_emails[:5], 1):  # 최대 5개만 표시
                response += f"**{i}. {email_data['subject']}**\n"
                response += f"👤 발신자: {email_data['sender']}\n"
                response += f"📅 날짜: {email_data['date']}\n"
                response += f"📄 내용: {email_data['body']}\n"
                response += f"🔗 ID: `{email_data['id']}`\n\n"
                
                # 답장 대기 상태로 설정
                user_email_states[user_id] = {
                    'pending_reply': email_data,
                    'awaiting_reply': True
                }
            
            response += "💬 **답장하려면:**\n"
            response += "• `/email_reply [내용]` - 직접 작성\n"
            response += "• `/email_ai_reply` - AI 자동 생성"
            
    except Exception as e:
        response = f"❌ 이메일 확인 중 오류: {str(e)}"
    
    await update.message.reply_text(response)

async def email_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """이메일 답장 보내기"""
    user_id = str(update.effective_user.id)
    
    # 답장할 내용 추출
    message_parts = update.message.text.split(' ', 1)
    if len(message_parts) < 2:
        await update.message.reply_text("❌ 답장 내용을 입력해주세요.\n예: `/email_reply 안녕하세요. 메일 잘 받았습니다.`")
        return
    
    reply_content = message_parts[1]
    
    # 답장 대기 중인 이메일 확인
    if user_id not in user_email_states or not user_email_states[user_id].get('awaiting_reply'):
        await update.message.reply_text("❌ 답장할 이메일이 없습니다. 먼저 `/email_check`로 이메일을 확인해주세요.")
        return
    
    try:
        email_data = user_email_states[user_id]['pending_reply']
        
        # 답장 전송
        success = email_manager.send_reply(email_data['id'], reply_content, user_id)
        
        if success:
            response = f"""✅ **답장 전송 완료!**

📧 **수신자:** {email_data['sender']}
📝 **제목:** Re: {email_data['subject']}
💬 **내용:** {reply_content[:100]}{'...' if len(reply_content) > 100 else ''}

🎉 답장이 성공적으로 전송되었습니다!"""
            
            # 답장 상태 초기화
            user_email_states[user_id]['awaiting_reply'] = False
        else:
            response = "❌ 답장 전송에 실패했습니다. 다시 시도해주세요."
            
    except Exception as e:
        response = f"❌ 답장 전송 중 오류: {str(e)}"
    
    await update.message.reply_text(response)

async def email_ai_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI 자동 답장 생성"""
    user_id = str(update.effective_user.id)
    
    # 답장 대기 중인 이메일 확인
    if user_id not in user_email_states or not user_email_states[user_id].get('awaiting_reply'):
        await update.message.reply_text("❌ 답장할 이메일이 없습니다. 먼저 `/email_check`로 이메일을 확인해주세요.")
        return
    
    try:
        email_data = user_email_states[user_id]['pending_reply']
        
        # AI 답장 생성
        ai_reply = email_manager.generate_ai_reply(email_data['full_body'], ai_handler, user_id)
        
        response = f"""🤖 **AI 답장 생성 완료!**

📧 **원본 제목:** {email_data['subject']}
👤 **발신자:** {email_data['sender']}

💬 **AI 생성 답장:**
{ai_reply}

✅ **전송하시겠습니까?**
• `/email_send_ai` - 이 답장 전송
• `/email_ai_reply` - 다시 생성
• `/email_reply [내용]` - 직접 수정하여 전송"""
        
        # AI 생성 답장 임시 저장
        user_email_states[user_id]['ai_reply'] = ai_reply
        
    except Exception as e:
        response = f"❌ AI 답장 생성 중 오류: {str(e)}"
    
    await update.message.reply_text(response)

async def email_send_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI 생성 답장 전송"""
    user_id = str(update.effective_user.id)
    
    # AI 답장 확인
    if user_id not in user_email_states or 'ai_reply' not in user_email_states[user_id]:
        await update.message.reply_text("❌ AI 생성 답장이 없습니다. 먼저 `/email_ai_reply`로 답장을 생성해주세요.")
        return
    
    try:
        email_data = user_email_states[user_id]['pending_reply']
        ai_reply = user_email_states[user_id]['ai_reply']
        
        # 답장 전송
        success = email_manager.send_reply(email_data['id'], ai_reply, user_id)
        
        if success:
            response = f"""✅ **AI 답장 전송 완료!**

📧 **수신자:** {email_data['sender']}
📝 **제목:** Re: {email_data['subject']}
🤖 **AI 답장이 성공적으로 전송되었습니다!**

💬 **전송된 내용:**
{ai_reply[:200]}{'...' if len(ai_reply) > 200 else ''}"""
            
            # 상태 초기화
            user_email_states[user_id]['awaiting_reply'] = False
            if 'ai_reply' in user_email_states[user_id]:
                del user_email_states[user_id]['ai_reply']
        else:
            response = "❌ AI 답장 전송에 실패했습니다. 다시 시도해주세요."
            
    except Exception as e:
        response = f"❌ AI 답장 전송 중 오류: {str(e)}"
    
    await update.message.reply_text(response)

async def drive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """구글 드라이브 기능 안내"""
    drive_help = """📁 **구글 드라이브 관리 시스템**

📋 **파일 관리:**
• `/drive_list` - 파일 목록 보기
• `/drive_search [키워드]` - 파일 검색
• `/drive_info [파일ID]` - 파일 정보 보기

📖 **파일 읽기:**
• `/drive_read [파일명]` - 파일 내용 읽기
• `/drive_read_id [파일ID]` - ID로 파일 읽기

✏️ **파일 생성/수정:**
• `/drive_create [파일명] [내용]` - 텍스트 파일 생성
• `/drive_update [파일ID] [새내용]` - 파일 내용 수정
• `/drive_folder [폴더명]` - 새 폴더 생성

🤖 **AI 연동:**
• `/drive_analyze [파일명]` - AI로 파일 분석
• `/drive_code [파일명] [요청]` - 코드 파일 수정 요청

💡 **사용 예시:**
1. `/drive_create report.txt 오늘 업무 보고서` → 파일 생성
2. `/drive_read report.txt` → 파일 내용 확인
3. `/drive_analyze report.txt` → AI가 내용 분석
4. `/drive_update [ID] 수정된 내용` → 파일 업데이트

🔒 **보안:** 개인별 폴더 관리 및 권한 제어"""
    await update.message.reply_text(drive_help)

async def drive_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """드라이브 파일 목록"""
    try:
        files = drive_handler.list_files(max_files=20)
        
        if not files:
            response = "📭 **파일이 없습니다.**"
        else:
            response = f"📁 **구글 드라이브 파일 목록** ({len(files)}개)\n\n"
            
            for file in files:
                file_name = file.get('name', '이름 없음')
                file_id = file.get('id', '')
                file_size = file.get('size', '0')
                mime_type = file.get('mimeType', '')
                
                # 파일 크기 포맷팅
                if file_size and file_size.isdigit():
                    size_kb = int(file_size) // 1024
                    size_display = f"{size_kb}KB" if size_kb > 0 else f"{file_size}B"
                else:
                    size_display = "폴더"
                
                # 파일 타입 아이콘
                if 'folder' in mime_type:
                    icon = "📁"
                elif 'document' in mime_type:
                    icon = "📄"
                elif 'spreadsheet' in mime_type:
                    icon = "📊"
                elif 'text' in mime_type:
                    icon = "📝"
                else:
                    icon = "📎"
                
                response += f"{icon} **{file_name}**\n"
                response += f"🆔 `{file_id}`\n"
                response += f"📏 {size_display}\n\n"
                
                if len(response) > 3500:  # 메시지 길이 제한
                    response += "... (더 많은 파일이 있습니다)"
                    break
            
            response += "\n💡 **사용법:**\n"
            response += "• `/drive_read [파일명]` - 파일 읽기\n"
            response += "• `/drive_read_id [파일ID]` - ID로 읽기"
            
    except Exception as e:
        response = f"❌ 파일 목록 조회 중 오류: {str(e)}"
    
    await update.message.reply_text(response)

async def drive_read_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """구글 드라이브 파일 내용 읽기"""
    message_parts = update.message.text.split(' ', 1)
    if len(message_parts) < 2:
        await update.message.reply_text("❌ 파일명을 입력해주세요.\n예: `/drive_read report.txt` 또는 `/drive_read test/sample.txt`")
        return
    
    file_name = message_parts[1]
    
    try:
        # 구글 드라이브에서 파일 검색
        files = drive_handler.search_files(file_name)
        
        if not files:
            response = f"""❌ **'{file_name}' 파일을 찾을 수 없습니다.**

🔍 **검색 위치:** 구글 드라이브

💡 **파일을 찾으려면:**
• `/drive_list` - 사용 가능한 파일 목록 확인
• `/drive_read [정확한파일명]` - 정확한 파일명으로 검색
• 먼저 `/connect_drive`로 개인 드라이브를 연결하세요

🌟 **클라우드 전용 봇**: 모든 파일은 구글 드라이브에서 관리됩니다."""
        else:
            # 첫 번째 검색 결과 사용
            file_id = files[0]['id']
            
            # 파일 내용 읽기
            result = drive_handler.read_file_content(file_id)
            
            if 'error' in result:
                response = f"❌ 구글 드라이브 파일 읽기 실패: {result['error']}"
            else:
                content = result['content']
                file_info = result['file_name']
                
                response = f"📄 **구글 드라이브 파일: {file_info}**\n\n"
                
                # 내용이 너무 길면 요약
                if len(content) > 2000:
                    response += f"📝 **내용 (처음 2000자):**\n```\n{content[:2000]}...\n```\n\n"
                    response += f"📊 **전체 길이:** {len(content)}자\n"
                    response += "💡 **전체 내용을 보려면 웹 링크를 확인하세요.**"
                else:
                    response += f"📝 **내용:**\n```\n{content}\n```"
                
                response += f"\n\n🆔 **파일 ID:** `{file_id}`"
                
    except Exception as e:
        response = f"❌ 파일 읽기 중 오류: {str(e)}"
    
    await update.message.reply_text(response)

async def drive_create_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """파일 생성"""
    message_parts = update.message.text.split(' ', 2)
    if len(message_parts) < 3:
        await update.message.reply_text("❌ 파일명과 내용을 입력해주세요.\n예: `/drive_create report.txt 오늘 업무 보고서 내용`")
        return
    
    file_name = message_parts[1]
    content = message_parts[2]
    
    try:
        result = drive_handler.create_text_file(content, file_name)
        
        if 'error' in result:
            response = f"❌ 파일 생성 실패: {result['error']}"
        else:
            response = f"""✅ **파일 생성 완료!**

📄 **파일명:** {result['file_name']}
🆔 **파일 ID:** `{result['file_id']}`
📏 **크기:** {result['size']}바이트
🔗 **링크:** {result['web_link']}

💡 **다음 단계:**
• `/drive_read {file_name}` - 파일 내용 확인
• `/drive_update {result['file_id']} [새내용]` - 파일 수정"""
            
    except Exception as e:
        response = f"❌ 파일 생성 중 오류: {str(e)}"
    
    await update.message.reply_text(response)

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """업무보고 시작"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name or "사용자"
    
    # 명령어 파라미터 확인
    args = context.args
    report_type = args[0] if args else "daily"
    
    # 진행 중인 보고서 확인
    active_report = report_manager.get_active_report(user_id)
    if active_report:
        current_step = active_report["current_step"]
        total_steps = len(active_report["template"]["checklist"])
        
        response = f"""⚠️ **이미 진행 중인 보고서가 있습니다!**

📋 **현재 보고서:** {active_report['template']['name']}
📊 **진행률:** {current_step}/{total_steps}

**선택사항:**
• `/report_status` - 현재 진행 상황 확인
• `/report_cancel` - 현재 보고서 취소하고 새로 시작
• 그냥 답변 입력 - 현재 보고서 계속 작성"""
        
        await update.message.reply_text(response)
        return
    
    # 새 보고서 시작
    result = report_manager.start_report(user_id, report_type)
    
    if 'error' in result:
        available_templates = report_manager.get_available_templates()
        template_list = "\n".join([f"• `{t['key']}` - {t['name']}" for t in available_templates['templates']])
        
        response = f"""❌ {result['error']}

📋 **사용 가능한 보고서 타입:**
{template_list}

**사용법:** `/report [타입]`
**예시:** `/report daily` 또는 `/report weekly`"""
        
        await update.message.reply_text(response)
        return
    
    template = result['template']
    first_question = result['first_question']
    
    response = f"""📋 **{template['name']} 작성 시작!**

👤 **작성자:** {user_name}
📝 **체크리스트:** {len(template['checklist'])}개 항목
⭐ **필수 항목:** {len(template.get('required_fields', []))}개

**첫 번째 질문:**
❓ **{first_question}**

💡 **작성 방법:**
• 각 질문에 대해 자세히 답변해주세요
• 답변을 입력하면 자동으로 다음 질문으로 넘어갑니다
• `/report_status` - 진행 상황 확인
• `/report_cancel` - 작성 취소

지금 첫 번째 질문에 답변해주세요! 👆"""
    
    await update.message.reply_text(response)

async def report_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """보고서 진행 상황 확인"""
    user_id = str(update.effective_user.id)
    
    active_report = report_manager.get_active_report(user_id)
    if not active_report:
        # 최근 완료된 보고서 확인
        user_reports = report_manager.get_user_reports(user_id, limit=1)
        if user_reports['reports']:
            last_report = user_reports['reports'][0]
            response = f"""📋 **보고서 상태**

✅ **최근 완료된 보고서:**
• {last_report['template_name']}
• 완료 시간: {last_report['completed_at'][:16].replace('T', ' ')}

💡 **새 보고서 시작:** `/report [타입]`
📖 **보고서 목록:** `/report_list`"""
        else:
            response = """📋 **보고서 상태**

❌ **진행 중인 보고서가 없습니다.**

💡 **새 보고서 시작:**
• `/report` - 일일 업무보고서
• `/report weekly` - 주간 업무보고서  
• `/report project` - 프로젝트 진행보고서"""
        
        await update.message.reply_text(response)
        return
    
    template = active_report["template"]
    current_step = active_report["current_step"]
    checklist = template["checklist"]
    completed_fields = active_report["completed_fields"]
    
    response = f"""📋 **{template['name']} 진행 상황**

📊 **진행률:** {current_step}/{len(checklist)} ({int(current_step/len(checklist)*100)}%)

✅ **완료된 항목:**
"""
    
    for field in completed_fields:
        response += f"• {field}\n"
    
    if current_step < len(checklist):
        next_question = checklist[current_step]
        response += f"\n❓ **다음 질문:**\n{next_question}\n"
        response += "\n💡 위 질문에 답변을 입력해주세요!"
    else:
        response += "\n🎉 **모든 항목이 완료되었습니다!**\n"
        response += "• `/report_complete` - 보고서 완료 및 전송"
    
    await update.message.reply_text(response)

async def report_complete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """보고서 완료 및 전송"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name or "직원"
    
    active_report = report_manager.get_active_report(user_id)
    if not active_report:
        await update.message.reply_text("❌ 진행 중인 보고서가 없습니다. `/report`로 새 보고서를 시작하세요.")
        return
    
    # 완료 확인
    completion_result = report_manager._check_completion(user_id, active_report)
    
    if not completion_result.get('completed', False):
        missing_fields = completion_result.get('missing_fields', [])
        if missing_fields:
            response = f"""❌ **필수 항목이 누락되었습니다:**

⚠️ **누락된 항목:**
"""
            for field in missing_fields:
                response += f"• {field}\n"
            
            response += f"\n💡 **해결 방법:**\n"
            response += "• `/report_status` - 현재 상황 확인\n"
            response += "• 누락된 항목에 대한 답변 추가 입력\n"
            response += "• 모든 필수 항목 완료 후 다시 `/report_complete` 실행"
        else:
            response = "❌ 보고서가 아직 완료되지 않았습니다. `/report_status`로 진행 상황을 확인하세요."
        
        await update.message.reply_text(response)
        return
    
    # 보고서 완료 처리
    completed_report = completion_result['report']
    
    # 관리자에게 전송할 포맷 생성
    formatted_report = report_manager.format_report_for_manager(completed_report, user_name)
    
    # 사용자에게 완료 알림
    response = f"""✅ **보고서 작성 완료!**

📋 **{completed_report['template']['name']}**
👤 **작성자:** {user_name}
🆔 **보고서 ID:** {completed_report['report_id']}

📤 **관리자에게 자동 전송되었습니다!**

💡 **추가 기능:**
• `/report_list` - 내 보고서 목록
• `/report` - 새 보고서 작성
• `/drive_create report_{completed_report['report_id']}.txt [내용]` - 드라이브에 저장"""
    
    await update.message.reply_text(response)
    
    # 관리자에게 보고서 전송
    admin_id = os.getenv('ADMIN_USER_ID')
    if admin_id:
        try:
            # 관리자용 포맷으로 보고서 전송
            admin_message = f"""📋 **새 업무보고서 접수**

👤 **작성자:** {user_name} ({user_id})
📅 **완료 시간:** {completed_report.get('completed_at', '방금')}
🆔 **보고서 ID:** {completed_report['report_id']}

{formatted_report}

💡 **관리자 기능:**
• `/admin` - 관리자 대시보드
• `/admin_report` - 전체 보고서 현황"""
            
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message
            )
            logger.info(f"보고서 관리자 전송 완료: {user_name} ({user_id}) -> 관리자({admin_id})")
            
        except Exception as e:
            logger.error(f"관리자에게 보고서 전송 실패: {str(e)}")
    else:
        logger.info(f"보고서 완료 (관리자 ID 미설정): {user_name} ({user_id}) - {completed_report['report_id']}")

async def report_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """보고서 작성 취소"""
    user_id = str(update.effective_user.id)
    
    result = report_manager.cancel_report(user_id)
    
    if 'error' in result:
        response = f"❌ {result['error']}"
    else:
        response = f"""✅ {result['message']}

💡 **새 보고서 시작:**
• `/report` - 일일 업무보고서
• `/report weekly` - 주간 업무보고서
• `/report project` - 프로젝트 진행보고서"""
    
    await update.message.reply_text(response)

async def report_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자 보고서 목록"""
    user_id = str(update.effective_user.id)
    
    user_reports = report_manager.get_user_reports(user_id, limit=10)
    reports = user_reports['reports']
    
    if not reports:
        response = """📋 **내 보고서 목록**

❌ **작성된 보고서가 없습니다.**

💡 **새 보고서 시작:**
• `/report` - 일일 업무보고서 작성
• `/report weekly` - 주간 업무보고서 작성
• `/report project` - 프로젝트 진행보고서 작성"""
    else:
        response = f"📋 **내 보고서 목록** ({len(reports)}개)\n\n"
        
        for i, report in enumerate(reports, 1):
            completed_date = report['completed_at'][:16].replace('T', ' ') if report['completed_at'] else "진행중"
            response += f"**{i}. {report['template_name']}**\n"
            response += f"📅 {completed_date}\n"
            response += f"🆔 `{report['report_id']}`\n\n"
        
        response += "💡 **사용법:**\n"
        response += "• `/report_view [ID]` - 특정 보고서 보기\n"
        response += "• `/report` - 새 보고서 작성"
    
    await update.message.reply_text(response)

async def report_view_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """특정 보고서 상세 보기"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ 보고서 ID를 입력해주세요.\n예: `/report_view REPORT_20250101_001`")
        return
    
    report_id = context.args[0]
    
    # 사용자의 보고서 목록에서 검색
    user_reports = report_manager.get_user_reports(user_id, limit=50)
    target_report = None
    
    for report in user_reports['reports']:
        if report['report_id'] == report_id:
            target_report = report
            break
    
    if not target_report:
        await update.message.reply_text(f"❌ 보고서 ID '{report_id}'를 찾을 수 없습니다.\n\n💡 `/report_list`로 내 보고서 목록을 확인하세요.")
        return
    
    # 보고서 상세 정보 표시
    completed_date = target_report['completed_at'][:16].replace('T', ' ') if target_report['completed_at'] else "진행중"
    
    response = f"""📋 **보고서 상세 정보**

📄 **제목:** {target_report['template_name']}
🆔 **ID:** `{target_report['report_id']}`
📅 **완료일:** {completed_date}

📝 **내용:**
{target_report.get('formatted_content', '내용 없음')}

💡 **기능:**
• `/report_list` - 내 보고서 목록
• `/report` - 새 보고서 작성"""
    
    await update.message.reply_text(response)

async def connect_drive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자별 구글 드라이브 연결"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    # 이미 연결되어 있는지 확인
    if user_auth_manager.is_user_connected(user_id):
        await update.message.reply_text(f"""✅ **{user_name}님의 구글 드라이브가 이미 연결되어 있습니다!**

🔧 **사용 가능한 명령어:**
• `/drive_status` - 연결 상태 확인
• `/tree` - 파일 트리 보기
• `/mkdir [폴더명]` - 폴더 생성
• `/edit [파일명]` - 파일 편집
• `/run [파일명]` - 코드 실행
• `/disconnect_drive` - 연결 해제

💡 **클라우드 IDE 기능을 즐겨보세요!**""")
        return
    
    # OAuth 인증 URL 생성
    redirect_uri = "https://your-webhook-url.com/oauth/callback"  # 실제 웹훅 URL로 교체 필요
    
    auth_result = user_auth_manager.generate_auth_url(user_id, redirect_uri)
    
    if "error" in auth_result:
        if "setup_guide" in auth_result:
            await update.message.reply_text(f"""❌ **구글 API 설정이 필요합니다**

{auth_result['setup_guide']}

설정 완료 후 다시 시도해주세요.""")
        else:
            await update.message.reply_text(f"❌ 오류: {auth_result['error']}")
        return
    
    await update.message.reply_text(f"""🔗 **구글 드라이브 연결**

{user_name}님의 개인 구글 드라이브를 연결합니다.

**1단계:** 아래 링크를 클릭하여 구글 계정으로 로그인하세요.
{auth_result['auth_url']}

**2단계:** 권한을 승인하면 자동으로 연결됩니다.

⏰ **만료 시간:** {auth_result['expires_in']//60}분
🔒 **보안:** 토큰은 암호화되어 안전하게 저장됩니다.

**연결 후 사용 가능한 기능:**
• 📁 개인 워크스페이스 생성
• 💻 텔레그램에서 직접 코딩
• ☁️ 실시간 클라우드 동기화
• 🤝 팀 프로젝트 협업

🚀 **진정한 클라우드 IDE 경험을 시작하세요!**""")

async def drive_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """구글 드라이브 연결 상태 확인"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    is_connected = user_auth_manager.is_user_connected(user_id)
    
    if is_connected:
        # 드라이브 서비스 테스트
        try:
            drive_service = user_auth_manager.get_user_drive_service(user_id)
            if drive_service:
                # 간단한 API 호출로 연결 테스트
                about = drive_service.about().get(fields="user").execute()
                user_email = about.get('user', {}).get('emailAddress', '알 수 없음')
                
                await update.message.reply_text(f"""✅ **구글 드라이브 연결 상태: 정상**

👤 **연결된 계정:** {user_email}
🔗 **사용자:** {user_name}
⚡ **상태:** 활성화

🛠️ **사용 가능한 명령어:**
• `/tree` - 📁 파일 트리 보기
• `/mkdir [폴더명]` - 📁 새 폴더 생성
• `/edit [파일명]` - ✏️ 파일 편집
• `/upload [파일명]` - 📤 파일 업로드
• `/download [파일명]` - 📥 파일 다운로드
• `/run [파일명]` - 🏃‍♂️ 코드 실행
• `/share [파일명]` - 🔗 공유 링크 생성

🌟 **클라우드 IDE 모드 활성화!**""")
            else:
                await update.message.reply_text("⚠️ 드라이브 서비스 연결에 문제가 있습니다. `/connect_drive`로 다시 연결해주세요.")
        except Exception as e:
            await update.message.reply_text(f"❌ 드라이브 연결 테스트 실패: {str(e)}\n\n`/connect_drive`로 다시 연결해주세요.")
    else:
        await update.message.reply_text(f"""❌ **구글 드라이브가 연결되지 않았습니다**

{user_name}님의 개인 드라이브를 연결하여 클라우드 IDE 기능을 사용하세요!

🚀 **연결 방법:**
`/connect_drive` 명령어를 사용하세요.

💡 **연결 후 가능한 기능:**
• 📱 모바일에서 코딩
• ☁️ 실시간 파일 동기화  
• 🤝 팀 프로젝트 협업
• 🧠 AI 코드 분석
• 🏃‍♂️ 코드 실행 및 테스트

지금 바로 시작해보세요!""")

async def disconnect_drive_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """구글 드라이브 연결 해제"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    if not user_auth_manager.is_user_connected(user_id):
        await update.message.reply_text("❌ 연결된 구글 드라이브가 없습니다.")
        return
    
    success = user_auth_manager.disconnect_user(user_id)
    
    if success:
        await update.message.reply_text(f"""✅ **구글 드라이브 연결이 해제되었습니다**

{user_name}님의 드라이브 연결이 안전하게 해제되었습니다.

🔒 **보안 정보:**
• 저장된 토큰이 완전히 삭제되었습니다
• 구글 계정 접근 권한이 해제되었습니다

🔄 **다시 연결하려면:**
`/connect_drive` 명령어를 사용하세요.

감사합니다! 🙏""")
    else:
        await update.message.reply_text("❌ 연결 해제 중 오류가 발생했습니다.")

async def tree_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """파일 트리 보기 (클라우드 IDE)"""
    user_id = str(update.effective_user.id)
    
    if not user_auth_manager.is_user_connected(user_id):
        await update.message.reply_text("""❌ **구글 드라이브가 연결되지 않았습니다**

클라우드 IDE 기능을 사용하려면 먼저 드라이브를 연결하세요:
`/connect_drive`""")
        return
    
    try:
        drive_service = user_auth_manager.get_user_drive_service(user_id)
        
        # 루트 폴더의 파일 목록 가져오기
        results = drive_service.files().list(
            q="'root' in parents and trashed=false",
            fields="files(id, name, mimeType, size, modifiedTime)",
            orderBy="folder,name"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            await update.message.reply_text("""📁 **워크스페이스가 비어있습니다**

새 프로젝트를 시작해보세요:
• `/mkdir 내프로젝트` - 새 폴더 생성
• `/edit main.py` - 새 파일 생성
• `/template 파이썬` - 템플릿 생성""")
            return
        
        tree_text = "📁 **내 워크스페이스**\n\n"
        
        folders = []
        files_list = []
        
        for file in files:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                folders.append(file)
            else:
                files_list.append(file)
        
        # 폴더 먼저 표시
        for folder in folders:
            tree_text += f"📁 {folder['name']}/\n"
        
        # 파일 표시
        for file in files_list:
            size = int(file.get('size', 0)) if file.get('size') else 0
            if size > 0:
                size_str = f" ({size:,} bytes)"
            else:
                size_str = ""
            
            # 파일 타입에 따른 아이콘
            name = file['name']
            if name.endswith('.py'):
                icon = "🐍"
            elif name.endswith('.js'):
                icon = "📜"
            elif name.endswith('.html'):
                icon = "🌐"
            elif name.endswith('.css'):
                icon = "🎨"
            elif name.endswith('.md'):
                icon = "📝"
            elif name.endswith('.json'):
                icon = "📋"
            else:
                icon = "📄"
            
            tree_text += f"{icon} {name}{size_str}\n"
        
        tree_text += f"\n📊 **총 {len(folders)}개 폴더, {len(files_list)}개 파일**\n\n"
        tree_text += "🛠️ **명령어:**\n"
        tree_text += "• `/edit [파일명]` - 파일 편집\n"
        tree_text += "• `/mkdir [폴더명]` - 폴더 생성\n"
        tree_text += "• `/run [파일명]` - 코드 실행\n"
        tree_text += "• `/share [파일명]` - 공유 링크"
        
        await update.message.reply_text(tree_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 파일 목록 로드 실패: {str(e)}")

async def mkdir_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """새 폴더 생성 (클라우드 IDE)"""
    user_id = str(update.effective_user.id)
    
    if not user_auth_manager.is_user_connected(user_id):
        await update.message.reply_text("❌ 구글 드라이브가 연결되지 않았습니다. `/connect_drive`를 사용하세요.")
        return
    
    message_parts = update.message.text.split(' ', 1)
    if len(message_parts) < 2:
        await update.message.reply_text("""❌ 폴더명을 입력해주세요.

**사용법:** `/mkdir [폴더명]`
**예시:** `/mkdir 내프로젝트`""")
        return
    
    folder_name = message_parts[1].strip()
    
    try:
        drive_service = user_auth_manager.get_user_drive_service(user_id)
        
        # 폴더 생성
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': ['root']
        }
        
        folder = drive_service.files().create(body=folder_metadata).execute()
        
        await update.message.reply_text(f"""✅ **폴더가 생성되었습니다!**

📁 **폴더명:** {folder_name}
🆔 **ID:** {folder['id']}

**다음 단계:**
• `/tree` - 업데이트된 파일 트리 보기
• `/edit {folder_name}/main.py` - 새 파일 생성
• `/cd {folder_name}` - 폴더로 이동 (추후 구현)

🚀 **프로젝트를 시작해보세요!**""")
        
    except Exception as e:
        await update.message.reply_text(f"❌ 폴더 생성 실패: {str(e)}")

async def drive_update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """파일 내용 수정"""
    message_parts = update.message.text.split(' ', 2)
    if len(message_parts) < 3:
        await update.message.reply_text("❌ 파일 ID와 새 내용을 입력해주세요.\n예: `/drive_update [파일ID] 새로운 내용`")
        return
    
    file_id = message_parts[1]
    new_content = message_parts[2]
    
    try:
        result = drive_handler.update_file_content(file_id, new_content)
        
        if 'error' in result:
            response = f"❌ 파일 수정 실패: {result['error']}"
        else:
            response = f"""✅ **파일 수정 완료!**

📄 **파일명:** {result['file_name']}
🆔 **파일 ID:** `{result['file_id']}`
📏 **새 크기:** {result['size']}바이트
🔗 **링크:** {result['web_link']}

💡 **다음 단계:**
• `/drive_read {file_id}` - 수정된 내용 확인
• `/drive_list` - 파일 목록 보기"""
            
    except Exception as e:
        response = f"❌ 파일 수정 중 오류: {str(e)}"
    
    await update.message.reply_text(response)

async def workspace_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """워크스페이스 상태 확인"""
    user_id = str(update.effective_user.id)
    
    if not user_auth_manager.is_authenticated(user_id):
        await update.message.reply_text("""🔐 **드라이브 연결이 필요합니다!**
        
먼저 `/connect_drive` 명령어로 개인 구글 드라이브를 연결해주세요.
연결 후 자동으로 팜솔라 워크스페이스가 생성됩니다! 🎓""")
        return
    
    try:
        # 사용자 폴더 정보 확인
        user_name = update.effective_user.first_name or "사용자"
        from user_drive_manager import user_drive_manager
        
        folder_info = user_drive_manager.get_user_folder(user_id, user_name)
        
        if folder_info.get('error'):
            await update.message.reply_text(f"❌ 오류: {folder_info['error']}")
            return
        
        # 워크스페이스 상태 확인
        stats = user_drive_manager.get_user_stats(user_id)
        
        if stats.get('error'):
            await update.message.reply_text(f"❌ 통계 조회 실패: {stats['error']}")
            return
        
        workspace_info = stats.get('workspace_info', {})
        
        status_text = f"""🎓 **팜솔라 워크스페이스 상태**

👤 **사용자:** {user_name}
📁 **폴더명:** {stats['folder_name']}
🔗 **링크:** [구글 드라이브에서 보기]({stats['folder_link']})

📊 **파일 통계:**
• 총 파일 수: {stats['file_count']}개
• 총 용량: {stats['total_size_mb']}MB

🎯 **워크스페이스 정보:**
• 생성 상태: {'✅ 생성됨' if workspace_info.get('created') else '❌ 미생성'}
• 템플릿 파일: {workspace_info.get('files', 0)}개

📁 **폴더 구조:**
```
팜솔라_교과서/
├── 12주과정/
├── 1년과정/
├── 6주과정/
├── 과제제출/
└── 프로젝트/
```

💡 **사용 가능한 명령어:**
• `/tree` - 파일 트리 보기
• `/mkdir [폴더명]` - 새 폴더 생성
• `/create_workspace` - 워크스페이스 재생성"""

        if not workspace_info.get('created'):
            status_text += "\n\n🚀 **워크스페이스가 아직 생성되지 않았습니다!**\n`/create_workspace` 명령어로 생성해보세요."
        
        await update.message.reply_text(status_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 워크스페이스 상태 확인 실패: {str(e)}")

async def create_workspace_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """워크스페이스 생성 명령어 (진행상황 표시 강화)"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    if not user_auth_manager.is_user_connected(user_id):
        await update.message.reply_text("""❌ **구글 드라이브가 연결되지 않았습니다**

워크스페이스를 생성하려면 먼저 드라이브를 연결하세요:
`/connect_drive`""")
        return
    
    # 초기 메시지
    progress_message = await update.message.reply_text(
        "🚀 **팜솔라 워크스페이스 생성을 시작합니다!**\n\n" +
        "📊 진행상황: 0% - 준비 중..."
    )
    
    try:
        # 사용자 폴더 정보 가져오기
        user_folder_info = user_drive_manager.get_user_folder(user_id, user_name)
        if not user_folder_info.get('success'):
            await progress_message.edit_text(
                "❌ **워크스페이스 생성 실패**\n\n" +
                f"오류: {user_folder_info.get('error', '사용자 폴더를 찾을 수 없습니다')}"
            )
            return
        
        folder_id = user_folder_info['folder_id']
        
        # 진행상황 업데이트 콜백 함수
        async def progress_callback(message: str, percentage: int):
            try:
                progress_bar = "█" * (percentage // 5) + "░" * (20 - percentage // 5)
                await progress_message.edit_text(
                    f"🚀 **팜솔라 워크스페이스 생성 중**\n\n" +
                    f"📊 진행상황: {percentage}%\n" +
                    f"`{progress_bar}`\n\n" +
                    f"🔄 현재 작업: {message}"
                )
            except Exception as e:
                print(f"진행상황 업데이트 오류: {e}")
        
        # 워크스페이스 생성 (진행상황 콜백 포함)
        await progress_callback("워크스페이스 구조 분석 중...", 5)
        
        # UserDriveManager의 create_workspace_structure 메서드에 콜백 전달
        # (실제로는 비동기 콜백을 동기 함수에서 사용할 수 없으므로 다른 방식 사용)
        result = user_drive_manager.create_workspace_structure(folder_id, user_name)
        
        if result.get('success'):
            # 성공 메시지
            success_rate = result.get('success_rate', 100)
            created_folders = result.get('created_folders', 0)
            created_files = result.get('created_files', 0)
            failed_operations = result.get('failed_operations', 0)
            
            success_message = f"""✅ **워크스페이스 생성 완료!**

📊 **생성 결과**:
• 성공률: {success_rate}%
• 생성된 폴더: {created_folders}개
• 생성된 파일: {created_files}개
• 실패한 작업: {failed_operations}개

🔗 **워크스페이스 링크**: [바로가기]({result.get('main_folder_link', '#')})

📋 **생성된 구조**:
```
팜솔라_교과서/
├── 📚 12주과정/ (3주차까지 생성)
├── 📚 1년과정/ (4주차까지 생성)  
├── 📚 6주과정/ (전체 생성)
├── 📤 과제제출/
├── 🚀 프로젝트/
├── 📖 리소스/
└── 📝 개인노트/
```

🎯 **다음 단계**:
• `/tree` - 파일 구조 확인
• `/homework` - 과제 시스템 사용
• 자연어로 파일 편집 (예: "1주차 1교시 교과서를 열어줘")"""

            # 복구 시도 정보 추가
            if failed_operations > 0:
                recovery_info = result.get('recovery_attempted', {})
                if recovery_info:
                    success_message += f"\n\n🔧 **자동 복구**: {recovery_info.get('successful', 0)}/{recovery_info.get('attempted', 0)} 성공"
            
            await progress_message.edit_text(success_message)
            
            # 사용자 폴더 정보 업데이트
            user_drive_manager.user_folders[user_id]['workspace_created'] = True
            user_drive_manager.user_folders[user_id]['workspace_files'] = created_files
            user_drive_manager.save_user_folders()
            
        else:
            # 실패 메시지
            error_message = f"""❌ **워크스페이스 생성 실패**

🚨 **오류 내용**: {result.get('error', '알 수 없는 오류')}"""
            
            # 롤백 정보 추가
            if result.get('rollback_attempted'):
                rollback_success = result.get('rollback_success', False)
                partial_cleanup = result.get('partial_cleanup', [])
                
                error_message += f"\n\n🔄 **자동 롤백**: {'✅ 성공' if rollback_success else '❌ 부분 실패'}"
                if partial_cleanup:
                    error_message += f"\n📋 **정리된 항목**: {len(partial_cleanup)}개"
            
            error_message += "\n\n💡 **해결 방법**:\n• 잠시 후 다시 시도해보세요\n• 구글 드라이브 용량을 확인해보세요\n• `/disconnect_drive` 후 다시 연결해보세요"
            
            await progress_message.edit_text(error_message)
    
    except Exception as e:
        await progress_message.edit_text(
            f"❌ **워크스페이스 생성 중 오류 발생**\n\n" +
            f"오류: {str(e)}\n\n" +
            "💡 잠시 후 다시 시도해주세요."
        )

async def handle_natural_ide_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """자연어 기반 IDE 요청 처리 - 처리 여부를 반환"""
    user_id = str(update.effective_user.id)
    message_text = update.message.text
    
    # 명령어가 아닌 일반 메시지만 처리
    if message_text.startswith('/'):
        return False
    
    # 파일 관련 키워드가 포함된 경우만 처리
    file_keywords = ['파일', '만들', '생성', '수정', '편집', '보여', '삭제', '복사', '이동', 
                     'file', 'create', 'edit', 'show', 'delete', 'copy', 'move',
                     '.py', '.js', '.html', '.css', '.md', '.txt', '.json']
    
    if not any(keyword in message_text.lower() for keyword in file_keywords):
        return False
    
    try:
        # 자연어 처리
        result = natural_ide.process_natural_request(user_id, message_text)
        
        if result.get('error'):
            await update.message.reply_text(result['error'])
            return True  # 처리 완료
        elif result.get('suggestion'):
            await update.message.reply_text(result['suggestion'])
            return True  # 처리 완료
        elif result.get('success') or result.get('edit_mode'):
            await update.message.reply_text(result['message'], parse_mode='Markdown')
            return True  # 처리 완료
        else:
            # 처리되지 않은 경우
            return False
            
    except Exception as e:
        # 오류 발생 시
        print(f"Natural IDE error: {e}")
        return False

async def sync_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """실시간 동기화 상태 확인"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    if not user_auth_manager.is_user_connected(user_id):
        await update.message.reply_text("""❌ **구글 드라이브가 연결되지 않았습니다**

동기화 기능을 사용하려면 먼저 드라이브를 연결하세요:
`/connect_drive`""")
        return
    
    sync_manager = get_polling_sync_manager()
    if not sync_manager:
        await update.message.reply_text("❌ 동기화 시스템이 초기화되지 않았습니다.")
        return
    
    try:
        user_status = sync_manager.get_sync_status(user_id)
        system_status = sync_manager.get_sync_status()
        
        if user_status.get('error'):
            await update.message.reply_text(f"❌ 동기화 상태 조회 오류: {user_status['error']}")
            return
        
        is_active = user_status.get('is_active', False)
        file_count = user_status.get('file_count', 0)
        poll_interval = user_status.get('poll_interval', 30)
        
        status_emoji = "✅" if is_active else "⚠️"
        status_text = "활성화" if is_active else "비활성화"
        
        message = f"""🔄 **실시간 동기화 상태**

👤 **사용자:** {user_name}
{status_emoji} **동기화 상태:** {status_text}
📁 **감시 중인 파일:** {file_count}개
⏰ **폴링 간격:** {poll_interval}초

📊 **시스템 전체 상태:**
👥 **활성 사용자:** {system_status.get('active_users', 0)}명
📄 **전체 파일:** {system_status.get('total_files', 0)}개

📈 **동기화 통계:**
🔄 **총 동기화:** {system_status.get('stats', {}).get('total_syncs', 0)}회
🆕 **파일 생성:** {system_status.get('stats', {}).get('files_created', 0)}개
✏️ **파일 수정:** {system_status.get('stats', {}).get('files_modified', 0)}개
🗑️ **파일 삭제:** {system_status.get('stats', {}).get('files_deleted', 0)}개

🛠️ **관리 명령어:**
• `/sync_force` - 강제 동기화 실행
• `/sync_interval [초]` - 폴링 간격 변경

💡 **동기화 작동 방식:**
파일을 구글 드라이브에서 직접 편집하면 자동으로 감지되어 텔레그램으로 알림이 전송됩니다!"""
        
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 동기화 상태 확인 오류: {str(e)}")

async def sync_force_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """강제 동기화 실행"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    if not user_auth_manager.is_user_connected(user_id):
        await update.message.reply_text("""❌ **구글 드라이브가 연결되지 않았습니다**

동기화 기능을 사용하려면 먼저 드라이브를 연결하세요:
`/connect_drive`""")
        return
    
    sync_manager = get_polling_sync_manager()
    if not sync_manager:
        await update.message.reply_text("❌ 동기화 시스템이 초기화되지 않았습니다.")
        return
    
    try:
        await update.message.reply_text("🔄 **강제 동기화 실행 중...**\n\n파일 변경사항을 확인하고 있습니다...")
        
        success = sync_manager.force_sync(user_id)
        
        if success:
            await update.message.reply_text(f"""✅ **강제 동기화 완료!**

{user_name}님의 워크스페이스가 성공적으로 동기화되었습니다.

🔍 **확인된 변경사항이 있다면 곧 알림이 전송됩니다.**

💡 **참고:** 정기 동기화는 계속 백그라운드에서 실행됩니다.""")
        else:
            await update.message.reply_text("❌ 강제 동기화 실행 실패. 사용자가 동기화 시스템에 등록되지 않았습니다.")
    
    except Exception as e:
        await update.message.reply_text(f"❌ 강제 동기화 오류: {str(e)}")

async def sync_interval_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """폴링 간격 설정"""
    user_id = str(update.effective_user.id)
    
    if not user_auth_manager.is_user_connected(user_id):
        await update.message.reply_text("""❌ **구글 드라이브가 연결되지 않았습니다**

동기화 기능을 사용하려면 먼저 드라이브를 연결하세요:
`/connect_drive`""")
        return
    
    sync_manager = get_polling_sync_manager()
    if not sync_manager:
        await update.message.reply_text("❌ 동기화 시스템이 초기화되지 않았습니다.")
        return
    
    try:
        args = context.args
        if not args:
            current_interval = sync_manager.poll_interval
            await update.message.reply_text(f"""⏰ **현재 폴링 간격: {current_interval}초**

🔧 **간격 변경 방법:**
`/sync_interval [초]`

📝 **예시:**
• `/sync_interval 10` - 10초마다 확인 (빠름)
• `/sync_interval 60` - 60초마다 확인 (표준)
• `/sync_interval 300` - 5분마다 확인 (절약)

⚠️ **주의:** 간격이 짧을수록 배터리 소모가 클 수 있습니다.
💡 **권장:** 30-60초 간격이 적절합니다.""")
            return
        
        try:
            new_interval = int(args[0])
            if new_interval < 5:
                await update.message.reply_text("❌ 폴링 간격은 최소 5초 이상이어야 합니다.")
                return
            if new_interval > 3600:
                await update.message.reply_text("❌ 폴링 간격은 최대 1시간(3600초) 이하여야 합니다.")
                return
            
            sync_manager.set_poll_interval(new_interval)
            
            await update.message.reply_text(f"""✅ **폴링 간격이 변경되었습니다!**

⏰ **새 간격:** {new_interval}초
🔄 **적용 시점:** 다음 동기화 사이클부터

💡 **참고:**
• 짧은 간격: 더 빠른 동기화, 더 많은 리소스 사용
• 긴 간격: 리소스 절약, 동기화 지연 가능

현재 설정이 모든 사용자에게 적용됩니다.""")
            
        except ValueError:
            await update.message.reply_text("❌ 올바른 숫자를 입력해주세요. 예: `/sync_interval 30`")
    
    except Exception as e:
        await update.message.reply_text(f"❌ 폴링 간격 설정 오류: {str(e)}")

async def test_sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """동기화 시스템 실제 동작 테스트"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    if not user_auth_manager.is_user_connected(user_id):
        await update.message.reply_text("""❌ **구글 드라이브가 연결되지 않았습니다**

테스트를 위해 먼저 드라이브를 연결하세요:
`/connect_drive`""")
        return
    
    try:
        # 1. 폴링 동기화 시스템 테스트
        sync_manager = get_polling_sync_manager()
        if sync_manager:
            sync_status = sync_manager.get_sync_status(user_id)
            sync_test_result = "✅ 폴링 동기화 시스템 정상 작동"
        else:
            sync_test_result = "❌ 폴링 동기화 시스템 오류"
        
        # 2. Apps Script 대체 시스템 테스트
        apps_script_alt = get_apps_script_alternative()
        if apps_script_alt:
            apps_test_result = "✅ Apps Script 대체 시스템 정상 작동"
        else:
            apps_test_result = "❌ Apps Script 대체 시스템 오류"
        
        # 3. 구글 드라이브 API 연결 테스트
        credentials = user_auth_manager.get_user_credentials(user_id)
        service = build('drive', 'v3', credentials=credentials)
        
        # 간단한 API 호출 테스트
        results = service.files().list(pageSize=1, fields='files(id,name)').execute()
        if results:
            drive_test_result = "✅ 구글 드라이브 API 연결 정상"
        else:
            drive_test_result = "❌ 구글 드라이브 API 연결 오류"
        
        # 4. 종합 테스트 결과
        test_report = f"""🧪 **6단계 동기화 시스템 종합 테스트 결과**

**👤 사용자**: {user_name} (`{user_id}`)
**⏰ 테스트 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**📋 테스트 항목**:
1. {sync_test_result}
2. {apps_test_result}
3. {drive_test_result}

**🎯 종합 점수**: {"**100점** 🎉" if all("✅" in result for result in [sync_test_result, apps_test_result, drive_test_result]) else "**개선 필요** ⚠️"}

**📝 세부 정보**:
• 폴링 간격: {sync_manager.poll_interval if sync_manager else 'N/A'}초
• 활성 사용자: {len(sync_manager.active_users) if sync_manager else 0}명
• 동기화 통계: {sync_manager.sync_stats if sync_manager else 'N/A'}"""

        await update.message.reply_text(test_report)
        
    except Exception as e:
        await update.message.reply_text(f"""❌ **테스트 실행 중 오류 발생**

오류 내용: `{str(e)}`

다시 시도하거나 관리자에게 문의하세요.""")

# 7단계: 협업 및 공유 기능 명령어들

async def team_create_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """팀 워크스페이스 생성"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    # 인수 확인
    if not context.args:
        await update.message.reply_text("""🤝 **팀 워크스페이스 생성**

사용법: `/team_create [팀명] [코스타입]`

**예시:**
• `/team_create 프로젝트A` - 12주 코스 팀 생성
• `/team_create 태양광팀 6주` - 6주 코스 팀 생성

**코스 타입:**
• `12주` (기본값) - 12주차 과제 폴더 생성
• `6주` - 6주차 과제 폴더 생성""")
        return
    
    team_name = context.args[0]
    course_type = context.args[1] if len(context.args) > 1 else "12주"
    
    if course_type not in ["12주", "6주"]:
        await update.message.reply_text("❌ 코스 타입은 '12주' 또는 '6주'만 가능합니다.")
        return
    
    try:
        # 팀 워크스페이스 생성
        result = collaboration_manager.create_team_workspace(
            team_name=team_name,
            creator_id=user_id,
            creator_name=user_name,
            course_type=course_type
        )
        
        if result.get('success'):
            team_info = result['team_info']
            message = f"""✅ **팀 워크스페이스 생성 완료!**

🏷️ **팀명**: {team_info['team_name']}
👤 **팀장**: {user_name}
📅 **코스**: {course_type}
🆔 **팀 ID**: `{team_info['team_id']}`

📁 **생성된 구조**:
• 📋 프로젝트 계획
• 💻 소스코드
• 📊 과제 제출 ({course_type} 폴더)
• 🔄 버전 관리
• 💬 팀 커뮤니케이션
• 📈 진도 관리

🔗 **드라이브 링크**: [팀 폴더 열기]({team_info['folder_link']})

**다음 단계:**
• `/team_invite {team_info['team_id']} @사용자명` - 팀원 초대
• `/team_info {team_info['team_id']}` - 팀 정보 확인"""
            
            await update.message.reply_text(message)
        else:
            await update.message.reply_text(f"❌ 팀 워크스페이스 생성 실패: {result.get('error')}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ 오류 발생: {str(e)}")

async def team_invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """팀원 초대"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    if len(context.args) < 2:
        await update.message.reply_text("""👥 **팀원 초대**

사용법: `/team_invite [팀ID] [멤버ID] [역할]`

**예시:**
• `/team_invite team_12345 987654321` - 일반 멤버로 초대
• `/team_invite team_12345 987654321 leader` - 리더로 초대

**역할:**
• `member` (기본값) - 읽기/쓰기 권한
• `leader` - 모든 권한 (초대/관리 포함)""")
        return
    
    team_id = context.args[0]
    member_id = context.args[1]
    role = context.args[2] if len(context.args) > 2 else "member"
    
    try:
        # 멤버 이름 가져오기 (실제로는 텔레그램 API에서 가져와야 함)
        member_name = f"사용자_{member_id}"  # 간단한 플레이스홀더
        
        result = collaboration_manager.invite_member(
            team_id=team_id,
            inviter_id=user_id,
            member_id=member_id,
            member_name=member_name,
            role=role
        )
        
        if result.get('success'):
            await update.message.reply_text(result['message'])
        else:
            await update.message.reply_text(f"❌ 초대 실패: {result.get('error')}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ 오류 발생: {str(e)}")

async def team_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사용자가 속한 팀 목록"""
    user_id = str(update.effective_user.id)
    
    try:
        result = collaboration_manager.get_team_list(user_id)
        
        if result.get('success'):
            teams = result['teams']
            
            if not teams:
                await update.message.reply_text("""📝 **내 팀 목록**

아직 속한 팀이 없습니다.

**팀 만들기**: `/team_create [팀명]`
**팀 찾기**: 팀장에게 초대를 요청하세요.""")
                return
            
            team_list = "📝 **내 팀 목록**\n\n"
            for i, team in enumerate(teams, 1):
                progress_bar = "█" * (team['progress'] // 10) + "░" * (10 - team['progress'] // 10)
                team_list += f"""**{i}. {team['team_name']}**
🏷️ 역할: {team['role']}
👥 멤버: {team['member_count']}명
📈 진행률: [{progress_bar}] {team['progress']}%
🔗 [폴더 열기]({team['folder_link']})

"""
            
            team_list += f"\n**총 {len(teams)}개 팀**"
            await update.message.reply_text(team_list)
        else:
            await update.message.reply_text(f"❌ 팀 목록 조회 실패: {result.get('error')}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ 오류 발생: {str(e)}")

async def team_comment_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """파일에 댓글 추가"""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    if len(context.args) < 3:
        await update.message.reply_text("""💬 **파일 댓글 추가**

사용법: `/team_comment [팀ID] [파일경로] [댓글내용]`

**예시:**
• `/team_comment team_12345 "소스코드/main.py" "이 부분 수정 필요"`
• `/team_comment team_12345 "프로젝트_계획서.md" "일정 조정하자"`

**팁**: 파일 경로에 공백이 있으면 따옴표로 감싸세요.""")
        return
    
    team_id = context.args[0]
    file_path = context.args[1]
    comment = " ".join(context.args[2:])
    
    try:
        result = collaboration_manager.add_comment(
            team_id=team_id,
            file_path=file_path,
            user_id=user_id,
            user_name=user_name,
            comment=comment
        )
        
        if result.get('success'):
            await update.message.reply_text(f"""✅ **댓글이 추가되었습니다!**

📁 **파일**: {file_path}
👤 **작성자**: {user_name}
💬 **댓글**: {comment}

**댓글 보기**: `/team_comments {team_id} "{file_path}"`""")
        else:
            await update.message.reply_text(f"❌ 댓글 추가 실패: {result.get('error')}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ 오류 발생: {str(e)}")

async def team_comments_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """파일의 모든 댓글 조회"""
    if len(context.args) < 2:
        await update.message.reply_text("""📖 **파일 댓글 조회**

사용법: `/team_comments [팀ID] [파일경로]`

**예시:**
• `/team_comments team_12345 "소스코드/main.py"`
• `/team_comments team_12345 "프로젝트_계획서.md"`""")
        return
    
    team_id = context.args[0]
    file_path = context.args[1]
    
    try:
        result = collaboration_manager.get_file_comments(team_id, file_path)
        
        if result.get('success'):
            comments = result['comments']
            
            if not comments:
                await update.message.reply_text(f"""📖 **파일 댓글**

📁 **파일**: {file_path}
💬 **댓글**: 아직 댓글이 없습니다.

**댓글 추가**: `/team_comment {team_id} "{file_path}" [댓글내용]`""")
                return
            
            comments_text = f"📖 **파일 댓글** ({len(comments)}개)\n\n📁 **파일**: {file_path}\n\n"
            
            for i, comment in enumerate(comments, 1):
                timestamp = comment['timestamp'][:16].replace('T', ' ')  # 날짜 포맷팅
                comments_text += f"""**{i}. {comment['user_name']}** ({timestamp})
💬 {comment['comment']}

"""
            
            await update.message.reply_text(comments_text)
        else:
            await update.message.reply_text(f"❌ 댓글 조회 실패: {result.get('error')}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ 오류 발생: {str(e)}")

async def team_activity_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """팀 활동 내역 조회"""
    if not context.args:
        await update.message.reply_text("""📊 **팀 활동 내역**

사용법: `/team_activity [팀ID] [일수]`

**예시:**
• `/team_activity team_12345` - 최근 7일 활동
• `/team_activity team_12345 14` - 최근 14일 활동""")
        return
    
    team_id = context.args[0]
    days = int(context.args[1]) if len(context.args) > 1 else 7
    
    try:
        result = collaboration_manager.get_team_activity(team_id, days)
        
        if result.get('success'):
            activities = result['activities']
            
            if not activities:
                await update.message.reply_text(f"""📊 **팀 활동 내역**

🗓️ **기간**: 최근 {days}일
📈 **활동**: 활동 내역이 없습니다.

팀원들과 함께 프로젝트를 시작해보세요! 🚀""")
                return
            
            activity_text = f"📊 **팀 활동 내역** (최근 {days}일)\n\n"
            
            for activity in activities[:10]:  # 최근 10개만 표시
                timestamp = activity['timestamp'][:16].replace('T', ' ')
                action_map = {
                    'team_created': '🏗️ 팀 생성',
                    'member_invited': '👥 멤버 초대',
                    'comment_added': '💬 댓글 추가',
                    'file_shared': '📎 파일 공유',
                    'file_created': '📄 파일 생성',
                    'file_updated': '✏️ 파일 수정'
                }
                action_name = action_map.get(activity['action_type'], activity['action_type'])
                
                activity_text += f"**{timestamp}** - {action_name}\n"
                
                # 상세 정보 추가
                details = activity.get('details', {})
                if 'member_name' in details:
                    activity_text += f"   👤 {details['member_name']}\n"
                elif 'file_name' in details:
                    activity_text += f"   📁 {details['file_name']}\n"
                elif 'comment_preview' in details:
                    activity_text += f"   💬 {details['comment_preview']}\n"
                
                activity_text += "\n"
            
            activity_text += f"**총 {len(activities)}개 활동**"
            await update.message.reply_text(activity_text)
        else:
            await update.message.reply_text(f"❌ 활동 내역 조회 실패: {result.get('error')}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ 오류 발생: {str(e)}")

async def instructor_dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """강사용 모니터링 대시보드 (관리자 전용)"""
    user_id = str(update.effective_user.id)
    
    # 관리자 권한 확인 (실제로는 관리자 ID 목록으로 체크)
    ADMIN_IDS = ["123456789", "987654321"]  # 실제 관리자 ID로 변경 필요
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ 강사/관리자만 사용할 수 있는 명령어입니다.")
        return
    
    try:
        result = collaboration_manager.get_instructor_dashboard(user_id)
        
        if result.get('success'):
            summary = result['summary']
            teams = result['teams']
            
            dashboard_text = f"""👨‍🏫 **강사 대시보드**

📊 **전체 현황**:
• 🏷️ 총 팀 수: {summary['total_teams']}개
• 👥 총 학생 수: {summary['total_students']}명
• 🔥 활성 팀: {summary['active_teams']}개
• 📈 평균 팀 크기: {summary['average_team_size']:.1f}명

📋 **팀별 상세**:
"""
            
            for i, team in enumerate(teams, 1):
                progress_bar = "█" * (team['progress'] // 10) + "░" * (10 - team['progress'] // 10)
                dashboard_text += f"""
**{i}. {team['team_name']}**
👥 {team['member_count']}명 | 📈 [{progress_bar}] {team['progress']}%
🔥 최근 활동: {team['recent_activity']}회
🔗 [폴더 열기]({team['folder_link']})"""
            
            dashboard_text += f"\n\n**팀 상세 보기**: `/team_activity [팀ID]`"
            await update.message.reply_text(dashboard_text)
        else:
            await update.message.reply_text(f"❌ 대시보드 조회 실패: {result.get('error')}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ 오류 발생: {str(e)}")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """웹 검색 명령어"""
    user_id = str(update.effective_user.id)
    
    if not user_auth_manager.is_authenticated(user_id):
        await update.message.reply_text(
            "🔐 **드라이브 연결이 필요합니다!**\n\n"
            "/connect_drive 명령어로 개인 구글 드라이브를 먼저 연결해주세요."
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔍 **웹 검색 사용법:**\n\n"
            "`/search [검색어]`\n\n"
            "**예시:**\n"
            "• `/search python pandas merge`\n"
            "• `/search react hooks tutorial`\n"
            "• `/search javascript async await error`\n\n"
            "💡 **팁:** 프로그래밍 언어와 구체적인 키워드를 포함하면 더 정확한 결과를 얻을 수 있습니다!",
            parse_mode='Markdown'
        )
        return
    
    query = ' '.join(context.args)
    
    # 검색 타입 자동 감지
    search_type = 'code'
    query_lower = query.lower()
    if any(word in query_lower for word in ['error', 'exception', '에러', '오류']):
        search_type = 'error'
    elif any(word in query_lower for word in ['tutorial', 'guide', '튜토리얼', '가이드']):
        search_type = 'tutorial'
    elif any(word in query_lower for word in ['api', 'documentation', 'docs', '문서']):
        search_type = 'api'
    
    await update.message.reply_text(f"🔍 **'{query}' 검색 중...**\n\n검색 타입: {search_type}")
    
    try:
        result = web_search_ide.web_search(user_id, query, search_type)
        
        if result.get('success'):
            results = result.get('results', [])
            tips = result.get('search_tips', [])
            
            message = f"🔍 **'{query}' 검색 결과**\n\n"
            message += f"📊 **검색 정보:**\n"
            message += f"• 최적화된 검색어: {result.get('optimized_query')}\n"
            message += f"• 총 결과: {result.get('total_results')}개\n"
            message += f"• 검색 타입: {search_type}\n\n"
            
            message += "🌐 **상위 검색 결과:**\n"
            for i, res in enumerate(results[:5], 1):
                title = res.get('title', 'No Title')[:60]
                snippet = res.get('snippet', 'No description')[:80]
                site = res.get('site', 'Unknown site')
                message += f"{i}. **{title}**\n"
                message += f"   📝 {snippet}...\n"
                message += f"   🌍 {site}\n\n"
            
            if tips:
                message += "💡 **검색 팁:**\n"
                for tip in tips[:3]:
                    message += f"• {tip}\n"
            
            message += "\n🚀 **다음 작업:**\n"
            message += f"• 사이트 방문: `/visit [URL]`\n"
            message += f"• 검색+방문: `/search_visit {query}`\n"
            message += f"• 자연어: '{query} 검색해서 사이트도 접속해줘'"
            
            await update.message.reply_text(safe_markdown(message), parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ 검색 실패: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Search command error: {e}")
        await update.message.reply_text(f"❌ 검색 중 오류 발생: {str(e)}")

async def visit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """사이트 방문 명령어"""
    user_id = str(update.effective_user.id)
    
    if not user_auth_manager.is_authenticated(user_id):
        await update.message.reply_text(
            "🔐 **드라이브 연결이 필요합니다!**\n\n"
            "/connect_drive 명령어로 개인 구글 드라이브를 먼저 연결해주세요."
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "🌐 **사이트 방문 사용법:**\n\n"
            "`/visit [URL]`\n\n"
            "**예시:**\n"
            "• `/visit https://github.com/microsoft/vscode`\n"
            "• `/visit https://stackoverflow.com/questions/12345`\n"
            "• `/visit https://docs.python.org/3/`\n\n"
            "💡 **기능:** 사이트 내용을 분석하고 코드 스니펫을 자동으로 추출합니다!",
            parse_mode='Markdown'
        )
        return
    
    url = context.args[0]
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ 올바른 URL 형식이 아닙니다.\n예: `https://github.com`", parse_mode='Markdown')
        return
    
    await update.message.reply_text(f"🌐 **사이트 방문 중...**\n\n{url}")
    
    try:
        result = web_search_ide.visit_site(user_id, url, extract_code=True)
        
        if result.get('success'):
            message = f"🌐 **사이트 방문 완료!**\n\n"
            message += f"📊 **사이트 정보:**\n"
            message += f"• 제목: {result.get('title', 'No Title')[:60]}\n"
            message += f"• URL: {result.get('url')}\n"
            message += f"• 타입: {result.get('site_type', 'general')}\n"
            message += f"• 방문 시간: {result.get('timestamp')}\n\n"
            
            content_preview = result.get('content_preview', '')
            if content_preview:
                message += f"📄 **내용 미리보기:**\n```\n{content_preview[:300]}...\n```\n\n"
            
            code_snippets = result.get('code_snippets', [])
            if code_snippets:
                message += f"💻 **발견된 코드 스니펫 ({len(code_snippets)}개):**\n"
                for i, snippet in enumerate(code_snippets[:2], 1):
                    language = snippet.get('language', 'unknown')
                    code = snippet.get('code', '')[:150]
                    message += f"{i}. **{language}** 코드:\n```{language}\n{code}...\n```\n\n"
            
            related_links = result.get('related_links', [])
            if related_links:
                message += f"🔗 **관련 링크 ({len(related_links)}개):**\n"
                for i, link in enumerate(related_links[:3], 1):
                    link_text = link.get('text', 'Link')[:40]
                    message += f"{i}. {link_text}...\n"
            
            message += "\n🚀 **다음 작업:**\n"
            message += f"• 코드 테스트: `/test_code [코드]`\n"
            message += f"• 스니펫 확인: `/snippets`\n"
            message += f"• 자연어: '첫 번째 코드를 실행해줘'"
            
            await update.message.reply_text(safe_markdown(message), parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ 사이트 방문 실패: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Visit command error: {e}")
        await update.message.reply_text(f"❌ 사이트 방문 중 오류 발생: {str(e)}")

async def search_visit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """검색 후 자동 사이트 방문 명령어"""
    user_id = str(update.effective_user.id)
    
    if not user_auth_manager.is_authenticated(user_id):
        await update.message.reply_text(
            "🔐 **드라이브 연결이 필요합니다!**\n\n"
            "/connect_drive 명령어로 개인 구글 드라이브를 먼저 연결해주세요."
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔍🌐 **검색+방문 사용법:**\n\n"
            "`/search_visit [검색어]`\n\n"
            "**예시:**\n"
            "• `/search_visit python async await`\n"
            "• `/search_visit react hooks useEffect`\n"
            "• `/search_visit javascript fetch api error`\n\n"
            "💡 **기능:** 검색 후 상위 3개 사이트를 자동으로 방문하여 코드 스니펫을 수집합니다!",
            parse_mode='Markdown'
        )
        return
    
    query = ' '.join(context.args)
    
    await update.message.reply_text(f"🔍🌐 **'{query}' 검색 및 사이트 방문 중...**\n\n이 작업은 시간이 조금 걸릴 수 있습니다.")
    
    try:
        result = web_search_ide.search_and_visit(user_id, query, auto_visit_count=3)
        
        if result.get('success'):
            visited_sites = result.get('visited_sites', [])
            search_summary = result.get('search_summary', {})
            
            message = f"🔍🌐 **'{query}' 검색 + 사이트 방문 완료!**\n\n"
            message += f"📊 **작업 요약:**\n"
            message += f"• 총 검색 결과: {search_summary.get('total_results', 0)}개\n"
            message += f"• 방문한 사이트: {search_summary.get('visited_count', 0)}개\n\n"
            
            for i, site_data in enumerate(visited_sites, 1):
                search_result = site_data.get('search_result', {})
                visit_result = site_data.get('visit_result', {})
                
                title = search_result.get('title', 'No Title')[:50]
                message += f"🌐 **{i}. {title}**\n"
                message += f"• URL: {visit_result.get('url')}\n"
                message += f"• 타입: {visit_result.get('site_type', 'general')}\n"
                
                code_snippets = visit_result.get('code_snippets', [])
                if code_snippets:
                    message += f"• 코드 스니펫: {len(code_snippets)}개 발견\n"
                    for j, snippet in enumerate(code_snippets[:2], 1):
                        language = snippet.get('language', 'unknown')
                        message += f"  {j}) {language} 코드 수집됨\n"
                
                message += "\n"
            
            message += "🚀 **다음 작업:**\n"
            message += f"• 모든 스니펫: `/snippets`\n"
            message += f"• 코드 테스트: `/test_code [코드]`\n"
            message += f"• 자연어: '수집된 python 코드를 보여줘'"
            
            await update.message.reply_text(safe_markdown(message), parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ 검색 및 방문 실패: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Search visit command error: {e}")
        await update.message.reply_text(f"❌ 검색 및 방문 중 오류 발생: {str(e)}")

async def test_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """코드 테스트 명령어"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text(
            "🚀 **코드 테스트 사용법:**\n\n"
            "`/test_code [코드]`\n\n"
            "**예시:**\n"
            "• `/test_code print('Hello World')`\n"
            "• `/test_code for i in range(5): print(i)`\n\n"
            "💡 **지원 언어:** Python (기본), JavaScript, HTML, CSS\n"
            "💡 **자연어로도 가능:** '이 코드를 실행해줘'",
            parse_mode='Markdown'
        )
        return
    
    code = ' '.join(context.args)
    language = 'python'  # 기본값
    
    # 언어 감지
    if any(word in code.lower() for word in ['console.log', 'function', 'var ', 'let ', 'const ']):
        language = 'javascript'
    elif any(word in code.lower() for word in ['<html>', '<div>', '<script>']):
        language = 'html'
    
    await update.message.reply_text(f"🚀 **{language.title()} 코드 실행 중...**\n\n```{language}\n{code}\n```", parse_mode='Markdown')
    
    try:
        result = web_search_ide.test_code_online(code, language)
        
        if result.get('success'):
            output = result.get('output', '').strip()
            error = result.get('error', '').strip()
            return_code = result.get('return_code', 0)
            
            message = f"🚀 **{language.title()} 코드 실행 완료!**\n\n"
            message += f"📝 **실행한 코드:**\n```{language}\n{code}\n```\n\n"
            
            if return_code == 0:
                message += "✅ **실행 성공!**\n"
                if output:
                    message += f"📤 **출력 결과:**\n```\n{output}\n```\n"
                else:
                    message += "📤 **출력:** (출력 없음)\n"
            else:
                message += "❌ **실행 실패!**\n"
                if error:
                    message += f"🚨 **에러 메시지:**\n```\n{error}\n```\n"
            
            message += f"\n⏱️ **실행 시간:** {result.get('execution_time', 'N/A')}\n"
            message += f"🔢 **종료 코드:** {return_code}\n\n"
            
            if error:
                message += "🔍 **다음 작업:**\n"
                message += f"• 에러 해결: `/search {error.split()[0] if error else 'error'} 해결방법`\n"
                message += "• 자연어: '코드를 수정해줘'\n"
            else:
                message += "🎉 **성공! 다음 작업:**\n"
                message += "• 파일 저장: 'result.py 파일로 저장해줘'\n"
                message += "• 개선: '더 좋은 코드 예제 검색해줘'\n"
            
            await update.message.reply_text(safe_markdown(message), parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ 코드 실행 실패: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Test code command error: {e}")
        await update.message.reply_text(f"❌ 코드 실행 중 오류 발생: {str(e)}")

async def snippets_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """수집된 코드 스니펫 조회 명령어"""
    user_id = str(update.effective_user.id)
    
    if not user_auth_manager.is_authenticated(user_id):
        await update.message.reply_text(
            "🔐 **드라이브 연결이 필요합니다!**\n\n"
            "/connect_drive 명령어로 개인 구글 드라이브를 먼저 연결해주세요."
        )
        return
    
    language = context.args[0] if context.args else None
    limit = 10
    
    try:
        result = web_search_ide.get_code_snippets(user_id, language, limit)
        
        if result.get('success'):
            snippets = result.get('snippets', [])
            total_count = result.get('total_count', 0)
            filtered_count = result.get('filtered_count', 0)
            
            if not snippets:
                message = "📝 **수집된 코드 스니펫이 없습니다.**\n\n"
                message += "💡 **스니펫을 수집하려면:**\n"
                message += "• 웹 검색: `/search python pandas`\n"
                message += "• 사이트 방문: `/visit https://github.com`\n"
                message += "• 검색+방문: `/search_visit react hooks`"
                
                await update.message.reply_text(message)
                return
            
            language_filter = f" ({language})" if language else ""
            message = f"💻 **수집된 코드 스니펫{language_filter}**\n\n"
            message += f"📊 **스니펫 정보:**\n"
            message += f"• 전체 수집량: {total_count}개\n"
            message += f"• 표시 중: {filtered_count}개\n"
            if language:
                message += f"• 필터: {language} 언어만\n"
            message += "\n"
            
            for i, snippet in enumerate(snippets[:3], 1):  # 텔레그램 메시지 길이 제한으로 3개만
                snippet_language = snippet.get('language', 'unknown')
                source_url = snippet.get('source_url', '')
                title = snippet.get('title', 'Unknown source')[:40]
                code = snippet.get('code', '')[:200]
                timestamp = snippet.get('timestamp', '')
                
                message += f"**{i}. {snippet_language.title()} 코드**\n"
                message += f"📅 수집일: {timestamp.split('T')[0] if 'T' in timestamp else timestamp}\n"
                message += f"🌐 출처: {title}...\n"
                message += f"```{snippet_language}\n{code}{'...' if len(snippet.get('code', '')) > 200 else ''}\n```\n\n"
            
            if len(snippets) > 3:
                message += f"... 그리고 {len(snippets) - 3}개 더\n\n"
            
            message += "🚀 **다음 작업:**\n"
            message += f"• 코드 실행: `/test_code [코드]`\n"
            message += f"• 특정 언어: `/snippets python`\n"
            message += f"• 자연어: '첫 번째 코드를 실행해줘'"
            
            await update.message.reply_text(safe_markdown(message), parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ 스니펫 조회 실패: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Snippets command error: {e}")
        await update.message.reply_text(f"❌ 스니펫 조회 중 오류 발생: {str(e)}")

async def search_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """검색 기록 조회 명령어"""
    user_id = str(update.effective_user.id)
    
    if not user_auth_manager.is_authenticated(user_id):
        await update.message.reply_text(
            "🔐 **드라이브 연결이 필요합니다!**\n\n"
            "/connect_drive 명령어로 개인 구글 드라이브를 먼저 연결해주세요."
        )
        return
    
    try:
        result = web_search_ide.get_search_history(user_id, limit=10)
        
        if result.get('success'):
            history = result.get('history', [])
            
            if not history:
                await update.message.reply_text(
                    "📝 **검색 기록이 없습니다.**\n\n"
                    "💡 `/search [검색어]` 명령어로 검색을 시작해보세요!"
                )
                return
            
            message = f"📚 **검색 기록 (최근 {len(history)}개)**\n\n"
            
            for i, item in enumerate(history, 1):
                query = item.get('query', 'Unknown query')
                search_type = item.get('search_type', 'code')
                timestamp = item.get('timestamp', '')
                results_count = item.get('results_count', 0)
                
                message += f"**{i}. {query}**\n"
                message += f"📅 {timestamp.split('T')[0] if 'T' in timestamp else timestamp}\n"
                message += f"🔍 타입: {search_type} | 결과: {results_count}개\n\n"
            
            message += "🚀 **다음 작업:**\n"
            message += "• 재검색: `/search [이전 검색어]`\n"
            message += "• 새 검색: `/search [새로운 검색어]`"
            
            await update.message.reply_text(safe_markdown(message), parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ 검색 기록 조회 실패: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Search history command error: {e}")
        await update.message.reply_text(f"❌ 검색 기록 조회 중 오류 발생: {str(e)}")

async def team_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """팀 기능 안내"""
    help_text = """🤝 **팀 협업 기능**

**🏗️ 팀 관리:**
• `/team_create [팀명]` - 새 팀 워크스페이스 생성
• `/team_invite [팀ID] [멤버ID]` - 팀원 초대
• `/team_list` - 내가 속한 팀 목록

**💬 협업 기능:**
• `/team_comment [팀ID] [파일경로] [댓글]` - 파일에 댓글 추가
• `/team_comments [팀ID] [파일경로]` - 파일 댓글 보기
• `/team_activity [팀ID]` - 팀 활동 내역

**👨‍🏫 강사 전용:**
• `/instructor_dashboard` - 전체 팀 모니터링

**📁 팀 워크스페이스 구조:**
• 📋 프로젝트 계획 (계획서, 역할분담, 일정관리)
• 💻 소스코드 (main, modules, tests, docs)
• 📊 과제 제출 (주차별 폴더)
• 🔄 버전 관리 (변경이력, 릴리즈노트)
• 💬 팀 커뮤니케이션 (회의록, Q&A, 피드백)
• 📈 진도 관리 (진도현황, 개인별 진도)

**💡 사용 예시:**
1. `/team_create 프로젝트A` - 팀 생성
2. `/team_invite team_12345 987654321` - 팀원 초대
3. `/team_comment team_12345 "main.py" "코드 리뷰 완료"` - 댓글 추가

팀워크로 더 나은 결과를 만들어보세요! 🚀"""
    
    await update.message.reply_text(help_text)

# 비동기 크롤링 시스템 명령어들 (2단계 업그레이드)
async def async_crawl_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """비동기 크롤링 명령어 - 다중 URL 동시 크롤링"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        help_text = """🚀 **비동기 크롤링 시스템**

**사용법:** `/async_crawl [URL1] [URL2] [URL3] ...`

**예시:**
• `/async_crawl https://stackoverflow.com https://github.com`
• `/async_crawl https://docs.python.org https://developer.mozilla.org https://w3schools.com`

**특징:**
• 3-5배 빠른 속도 🚀
• 동시 다중 사이트 처리 ⚡
• 자동 재시도 및 에러 복구 🔄
• 코드 스니펫 자동 추출 📝

**제한:** 최대 10개 URL까지 동시 처리 가능"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    # URL 목록 추출
    urls = context.args
    if len(urls) > 10:
        await update.message.reply_text("⚠️ 최대 10개 URL까지만 처리할 수 있습니다.")
        return
    
    # 진행 상황 메시지
    progress_msg = await update.message.reply_text("🚀 비동기 크롤링을 시작합니다...")
    
    try:
        # 비동기 크롤링 import
        from web_search_ide import AsyncWebCrawler
        
        # 비동기 크롤링 실행
        async with AsyncWebCrawler(max_concurrent=5, requests_per_second=3) as crawler:
            # 진행 상황 콜백 함수
            async def progress_callback(url: str, result: dict):
                await progress_msg.edit_text(f"🔄 크롤링 진행 중... {url}")
            
            # 다중 URL 크롤링
            results = await crawler.crawl_multiple_urls(urls, progress_callback)
        
        # 결과 정리
        success_count = results['successful_count']
        failed_count = results['failed_count']
        total_time = results['total_time']
        success_rate = results['success_rate']
        
        # 성공한 결과들에서 주요 정보 추출
        summary_text = f"""✅ **비동기 크롤링 완료!**

📊 **성능 통계:**
• 처리된 URL: {results['total_urls']}개
• 성공: {success_count}개 ({success_rate:.1f}%)
• 실패: {failed_count}개
• 총 소요시간: {total_time:.2f}초
• URL당 평균: {results['average_time_per_url']:.2f}초
• 초당 처리: {results['performance_stats']['urls_per_second']:.1f} URLs/sec

🎯 **수집된 콘텐츠:**"""
        
        # 성공한 결과들의 요약 정보
        for i, result in enumerate(results['successful_results'][:5]):  # 최대 5개만 표시
            title = result.get('title', '제목 없음')[:50]
            code_count = len(result.get('code_blocks', []))
            link_count = len(result.get('links', []))
            
            summary_text += f"""
{i+1}. **{title}**
   • 코드 블록: {code_count}개
   • 링크: {link_count}개
   • 크기: {result.get('content_length', 0):,} bytes"""
        
        if len(results['successful_results']) > 5:
            remaining = len(results['successful_results']) - 5
            summary_text += f"\n... 외 {remaining}개 사이트 더"
        
        # 실패한 URL들 표시
        if failed_count > 0:
            summary_text += "\n\n❌ **실패한 URL들:**"
            for result in results['failed_results'][:3]:  # 최대 3개만 표시
                url = result.get('url', '')
                error = result.get('error', '알 수 없는 오류')
                summary_text += f"\n• {url}: {error}"
        
        summary_text += "\n\n💡 `/async_search [검색어]`로 검색 기반 크롤링도 가능합니다!"
        
        await progress_msg.edit_text(summary_text, parse_mode='Markdown')
        
    except Exception as e:
        await progress_msg.edit_text(f"❌ 비동기 크롤링 실패: {str(e)}")

async def async_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """비동기 검색 크롤링 명령어"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        help_text = """🔍 **비동기 검색 크롤링**

**사용법:** `/async_search [검색어] [최대결과수]`

**예시:**
• `/async_search python async programming`
• `/async_search react hooks 5`
• `/async_search machine learning tutorial`

**특징:**
• 개발 관련 사이트 우선 검색 🎯
• 관련성 점수로 결과 필터링 📊
• 코드 스니펫 자동 추출 📝
• 3-5배 빠른 병렬 처리 ⚡

**기본값:** 최대 5개 사이트 검색"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    # 검색어와 최대 결과 수 추출
    search_query = ' '.join(context.args[:-1]) if context.args[-1].isdigit() else ' '.join(context.args)
    max_results = int(context.args[-1]) if context.args[-1].isdigit() else 5
    
    if max_results > 10:
        max_results = 10
        await update.message.reply_text("⚠️ 최대 10개 결과로 제한됩니다.")
    
    # 진행 상황 메시지
    progress_msg = await update.message.reply_text(f"🔍 '{search_query}' 검색 및 크롤링 시작...")
    
    try:
        # 비동기 크롤링 import
        from web_search_ide import AsyncWebCrawler
        
        # 비동기 검색 크롤링 실행
        async with AsyncWebCrawler(max_concurrent=3, requests_per_second=2) as crawler:
            results = await crawler.search_and_crawl(search_query, max_results)
        
        if not results['success']:
            await progress_msg.edit_text(f"❌ 검색 실패: {results.get('error', '알 수 없는 오류')}")
            return
        
        # 결과 정리
        relevant_count = results['relevant_count']
        total_crawled = results['total_crawled']
        crawl_stats = results['crawl_stats']
        
        summary_text = f"""🎯 **검색 크롤링 완료!**

📊 **검색 결과:**
• 검색어: "{search_query}"
• 크롤링한 사이트: {total_crawled}개
• 관련성 높은 결과: {relevant_count}개
• 처리 속도: {crawl_stats['urls_per_second']:.1f} URLs/sec

🏆 **관련성 높은 콘텐츠:**"""
        
        # 관련성 높은 결과들 표시
        for i, result in enumerate(results['relevant_results'][:5]):
            title = result.get('title', '제목 없음')[:50]
            relevance = result.get('relevance_score', 0)
            code_count = len(result.get('code_blocks', []))
            url = result.get('url', '')
            
            summary_text += f"""
{i+1}. **{title}** (관련성: {relevance}점)
   • URL: {url}
   • 코드 블록: {code_count}개"""
            
            # 코드 블록이 있으면 첫 번째 코드 스니펫 미리보기
            if code_count > 0:
                first_code = result['code_blocks'][0]
                code_preview = first_code['code'][:100] + "..." if len(first_code['code']) > 100 else first_code['code']
                summary_text += f"\n   • 코드 미리보기 ({first_code['language']}): `{code_preview}`"
        
        if relevant_count == 0:
            summary_text += "\n\n⚠️ 관련성 높은 결과를 찾지 못했습니다. 다른 검색어를 시도해보세요."
        
        summary_text += "\n\n💡 `/visit [URL]`로 특정 사이트를 자세히 탐색할 수 있습니다!"
        
        await progress_msg.edit_text(summary_text, parse_mode='Markdown')
        
    except Exception as e:
        await progress_msg.edit_text(f"❌ 검색 크롤링 실패: {str(e)}")

async def crawl_performance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """크롤링 성능 비교 명령어"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        help_text = """⚡ **크롤링 성능 비교**

**사용법:** `/crawl_performance [URL1] [URL2] [URL3]`

**기능:**
• 동기 vs 비동기 크롤링 성능 비교
• 실시간 속도 측정
• 메모리 사용량 모니터링
• 에러 복구율 분석

**예시:**
• `/crawl_performance https://stackoverflow.com https://github.com https://docs.python.org`

이 명령어로 비동기 크롤링의 성능 향상을 직접 확인하세요! 🚀"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    urls = context.args[:5]  # 최대 5개 URL
    
    progress_msg = await update.message.reply_text("⚡ 성능 비교 테스트를 시작합니다...")
    
    try:
        import time
        import asyncio
        from web_search_ide import AsyncWebCrawler, web_search_ide
        
        # 1. 동기식 크롤링 (기존 방식)
        await progress_msg.edit_text("🐌 동기식 크롤링 테스트 중...")
        sync_start = time.time()
        sync_results = []
        sync_errors = 0
        
        for url in urls:
            try:
                result = web_search_ide.visit_site(user_id, url, extract_code=True)
                if result.get('success'):
                    sync_results.append(result)
                else:
                    sync_errors += 1
            except:
                sync_errors += 1
        
        sync_time = time.time() - sync_start
        
        # 2. 비동기 크롤링 (새로운 방식)
        await progress_msg.edit_text("🚀 비동기 크롤링 테스트 중...")
        async_start = time.time()
        
        async with AsyncWebCrawler(max_concurrent=len(urls), requests_per_second=5) as crawler:
            async_result = await crawler.crawl_multiple_urls(urls)
        
        async_time = time.time() - async_start
        
        # 성능 비교 결과
        speed_improvement = sync_time / async_time if async_time > 0 else 0
        
        comparison_text = f"""⚡ **크롤링 성능 비교 결과**

🐌 **동기식 크롤링:**
• 소요시간: {sync_time:.2f}초
• 성공: {len(sync_results)}개
• 실패: {sync_errors}개
• 평균 속도: {len(urls)/sync_time:.2f} URLs/sec

🚀 **비동기 크롤링:**
• 소요시간: {async_time:.2f}초
• 성공: {async_result['successful_count']}개
• 실패: {async_result['failed_count']}개
• 평균 속도: {async_result['performance_stats']['urls_per_second']:.2f} URLs/sec

📊 **성능 향상:**
• 속도 개선: **{speed_improvement:.1f}배** 빨라짐! 🎯
• 성공률 비교: {async_result['success_rate']:.1f}% vs {(len(sync_results)/len(urls)*100):.1f}%
• 시간 절약: {sync_time - async_time:.2f}초

💡 **결론:** 비동기 크롤링이 {speed_improvement:.1f}배 더 효율적입니다!"""
        
        await progress_msg.edit_text(comparison_text, parse_mode='Markdown')
        
    except Exception as e:
        await progress_msg.edit_text(f"❌ 성능 비교 테스트 실패: {str(e)}")

# ==================== 최신 기술 정보 업데이트 명령어들 (3단계) ====================

async def tech_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """전체 기술 정보 요약"""
    try:
        await update.message.reply_text("🔄 최신 기술 정보를 수집하고 있습니다...")
        
        # 카테고리 파라미터 확인
        category = 'all'
        if context.args:
            category = context.args[0].lower()
            if category not in ['all', 'github', 'news', 'stackoverflow', 'packages']:
                category = 'all'
        
        # 기술 정보 수집
        summary = await tech_updater.get_tech_summary(category)
        
        if 'error' in summary:
            await update.message.reply_text(f"❌ 기술 정보 수집 실패: {summary['error']}")
            return
        
        # 메시지 포맷팅 및 전송
        formatted_message = tech_updater.format_tech_summary_message(summary)
        
        # 메시지가 너무 길면 분할 전송
        if len(formatted_message) > 4000:
            # GitHub 트렌딩만 먼저 전송
            github_summary = await tech_updater.get_tech_summary('github')
            github_message = tech_updater.format_tech_summary_message(github_summary)
            await update.message.reply_text(github_message, parse_mode='Markdown')
            
            # 기술 뉴스 전송
            news_summary = await tech_updater.get_tech_summary('news')
            news_message = tech_updater.format_tech_summary_message(news_summary)
            await update.message.reply_text(news_message, parse_mode='Markdown')
            
            # 패키지 정보 전송
            package_summary = await tech_updater.get_tech_summary('packages')
            package_message = tech_updater.format_tech_summary_message(package_summary)
            await update.message.reply_text(package_message, parse_mode='Markdown')
        else:
            await update.message.reply_text(formatted_message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ 기술 정보 요약 실패: {str(e)}")

async def github_trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """GitHub 트렌딩 리포지토리"""
    try:
        await update.message.reply_text("🔥 GitHub 트렌딩 리포지토리를 검색하고 있습니다...")
        
        # 언어 파라미터 확인
        language = ''
        time_range = 'daily'
        
        if context.args:
            if len(context.args) >= 1:
                language = context.args[0].lower()
            if len(context.args) >= 2:
                time_range = context.args[1].lower()
                if time_range not in ['daily', 'weekly', 'monthly']:
                    time_range = 'daily'
        
        # GitHub 트렌딩 정보 수집
        repositories = await tech_updater.get_github_trending(language, time_range)
        
        if not repositories:
            await update.message.reply_text("❌ GitHub 트렌딩 정보를 가져올 수 없습니다.")
            return
        
        # 메시지 생성
        message = f"🔥 **GitHub 트렌딩 리포지토리**\n"
        if language:
            message += f"📝 언어: {language.title()}\n"
        message += f"📅 기간: {time_range.title()}\n\n"
        
        for i, repo in enumerate(repositories[:10], 1):
            message += f"**{i}. [{repo['name']}]({repo['url']})**\n"
            message += f"⭐ {repo['stars']} | 🍴 {repo['forks']}"
            if repo['language']:
                message += f" | 💻 {repo['language']}"
            message += "\n"
            
            if repo['description']:
                description = repo['description'][:100] + "..." if len(repo['description']) > 100 else repo['description']
                message += f"📖 {description}\n"
            
            if repo['topics']:
                topics = ", ".join(repo['topics'][:5])
                message += f"🏷️ {topics}\n"
            
            message += "\n"
        
        message += f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ GitHub 트렌딩 검색 실패: {str(e)}")

async def tech_news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """최신 기술 뉴스 (RSS 피드)"""
    try:
        await update.message.reply_text("📰 최신 기술 뉴스를 수집하고 있습니다...")
        
        # RSS 피드에서 뉴스 수집
        news_list = tech_updater.parse_rss_feeds()
        
        if not news_list:
            await update.message.reply_text("❌ 기술 뉴스를 가져올 수 없습니다.")
            return
        
        # 메시지 생성
        message = "📰 **최신 기술 뉴스**\n\n"
        
        for i, news in enumerate(news_list[:15], 1):
            title = news.title[:60] + "..." if len(news.title) > 60 else news.title
            message += f"**{i}. [{title}]({news.url})**\n"
            message += f"📅 {news.source} | 🎯 점수: {news.score:.1f}\n"
            
            if news.description:
                desc = news.description[:80] + "..." if len(news.description) > 80 else news.description
                message += f"📝 {desc}\n"
            
            if news.tags:
                tags = ", ".join(news.tags[:3])
                message += f"🏷️ {tags}\n"
            
            message += "\n"
        
        message += f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ 기술 뉴스 수집 실패: {str(e)}")

async def stackoverflow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stack Overflow 인기 질문"""
    try:
        await update.message.reply_text("❓ Stack Overflow 인기 질문을 검색하고 있습니다...")
        
        # 태그 파라미터 확인
        tags = ['python', 'javascript']  # 기본 태그
        sort_option = 'activity'
        
        if context.args:
            if context.args[0] in ['python', 'javascript', 'react', 'node', 'django', 'flask', 'vue', 'angular']:
                tags = [context.args[0]]
            elif ',' in context.args[0]:
                tags = [tag.strip() for tag in context.args[0].split(',')]
            
            if len(context.args) >= 2:
                if context.args[1] in ['activity', 'votes', 'creation', 'relevance']:
                    sort_option = context.args[1]
        
        # Stack Overflow 질문 수집
        questions = await tech_updater.get_stackoverflow_questions(tags, sort_option)
        
        if not questions:
            await update.message.reply_text("❌ Stack Overflow 질문을 가져올 수 없습니다.")
            return
        
        # 메시지 생성
        message = f"❓ **Stack Overflow 인기 질문**\n"
        message += f"🏷️ 태그: {', '.join(tags)}\n"
        message += f"📊 정렬: {sort_option.title()}\n\n"
        
        for i, q in enumerate(questions[:10], 1):
            title = q['title'][:70] + "..." if len(q['title']) > 70 else q['title']
            message += f"**{i}. [{title}]({q['url']})**\n"
            message += f"👍 {q['score']} | 👀 {q['view_count']} | 💬 {q['answer_count']}"
            
            if q['is_answered']:
                message += " ✅"
            
            message += "\n"
            message += f"🏷️ {', '.join(q['tags'][:5])}\n"
            message += f"📅 {q['creation_date'][:10]}\n\n"
        
        message += f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Stack Overflow 검색 실패: {str(e)}")

async def package_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """패키지 최신 정보"""
    try:
        if not context.args:
            await update.message.reply_text("""📦 **패키지 정보 명령어 사용법:**

`/package_info [패키지명] [npm/pypi]`

**예시:**
• `/package_info react npm` - React NPM 패키지 정보
• `/package_info django pypi` - Django PyPI 패키지 정보
• `/package_info express` - Express 패키지 정보 (자동 감지)

**인기 패키지 예시:**
• NPM: react, vue, express, lodash, axios
• PyPI: requests, numpy, pandas, django, flask""")
            return
        
        package_name = context.args[0]
        ecosystem = None
        
        if len(context.args) >= 2:
            ecosystem = context.args[1].lower()
            if ecosystem not in ['npm', 'pypi']:
                ecosystem = None
        
        await update.message.reply_text(f"📦 {package_name} 패키지 정보를 검색하고 있습니다...")
        
        # 패키지 정보 수집
        package_info = None
        
        if ecosystem == 'npm':
            package_info = await tech_updater.get_npm_package_info(package_name)
        elif ecosystem == 'pypi':
            package_info = await tech_updater.get_pypi_package_info(package_name)
        else:
            # 자동 감지 - NPM 먼저 시도
            package_info = await tech_updater.get_npm_package_info(package_name)
            if not package_info:
                package_info = await tech_updater.get_pypi_package_info(package_name)
        
        if not package_info:
            await update.message.reply_text(f"❌ '{package_name}' 패키지 정보를 찾을 수 없습니다.")
            return
        
        # 메시지 생성
        ecosystem_emoji = "🟨" if package_info.ecosystem == 'npm' else "🐍"
        message = f"📦 **{package_info.name}** {ecosystem_emoji}\n\n"
        message += f"🔢 **버전:** {package_info.version}\n"
        message += f"🌐 **생태계:** {package_info.ecosystem.upper()}\n"
        
        if package_info.description:
            desc = package_info.description[:200] + "..." if len(package_info.description) > 200 else package_info.description
            message += f"📝 **설명:** {desc}\n"
        
        if package_info.homepage:
            message += f"🏠 **홈페이지:** {package_info.homepage}\n"
        
        if package_info.repository:
            message += f"📁 **저장소:** {package_info.repository}\n"
        
        if package_info.downloads > 0:
            message += f"⬇️ **다운로드:** {package_info.downloads:,}회/월\n"
        
        if package_info.last_updated:
            update_date = package_info.last_updated[:10] if len(package_info.last_updated) > 10 else package_info.last_updated
            message += f"📅 **마지막 업데이트:** {update_date}\n"
        
        message += f"\n🕐 조회 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ 패키지 정보 검색 실패: {str(e)}")

async def tech_auto_update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """자동 업데이트 설정"""
    try:
        message = """🔄 **최신 기술 정보 자동 업데이트**

현재 시스템에서 지원하는 자동 업데이트 기능:

📊 **실시간 캐싱:**
• 1시간 TTL 캐시로 빠른 응답
• API 호출 제한 자동 관리
• 중복 요청 방지

🔍 **지원 데이터 소스:**
• GitHub API - 트렌딩 리포지토리
• NPM Registry - 패키지 정보
• PyPI API - Python 패키지
• RSS 피드 - 기술 뉴스 (7개 소스)
• Stack Exchange API - Q&A

⚙️ **설정 옵션:**
• `/tech_summary` - 전체 요약 (추천)
• `/github_trending python daily` - 특정 언어/기간
• `/tech_news` - 최신 뉴스만
• `/stackoverflow python,javascript` - 특정 태그

💡 **팁:**
• API 키가 설정되면 더 많은 정보 제공
• 캐시로 인해 두 번째 요청부터 빠른 응답
• 카테고리별 조회로 원하는 정보만 확인 가능

🔧 **API 키 설정 필요:**
• GITHUB_TOKEN - GitHub API 제한 해제
• STACK_EXCHANGE_KEY - Stack Overflow 더 많은 요청"""

        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ 자동 업데이트 설정 실패: {str(e)}")

def main() -> None:
    """메인 함수"""
    if not BOT_TOKEN:
        print("ERROR: 봇 토큰이 설정되지 않았습니다!")
        return
    
    print(f"Starting {BOT_USERNAME} bot with Gemini + ChatGPT...")
    
    # 애플리케이션 생성
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 실시간 동기화 시스템 초기화
    print("🔄 실시간 동기화 시스템 초기화 중...")
    sync_manager = initialize_polling_sync(bot_instance=application, poll_interval=30)
    print("✅ 실시간 동기화 시스템 준비 완료")
    
    # Apps Script 대체 시스템 초기화
    print("🚀 Apps Script 대체 시스템 초기화 중...")
    apps_script_alt = initialize_apps_script_alternative(bot_instance=application)
    print("✅ Apps Script 대체 시스템 준비 완료")
    
    # 기본 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", track_command(start)))
    application.add_handler(CommandHandler("commands", track_command(commands_command)))
    application.add_handler(CommandHandler("help", track_command(help_command)))
    application.add_handler(CommandHandler("homework", track_command(homework_command)))
    application.add_handler(CommandHandler("submit", track_command(submit_command)))
    application.add_handler(CommandHandler("progress", track_command(progress_command)))
    application.add_handler(CommandHandler("practice", track_command(practice_command)))
    application.add_handler(CommandHandler("template", track_command(template_command)))
    application.add_handler(CommandHandler("solar", track_command(solar_calculator)))
    application.add_handler(CommandHandler("calc", track_command(quick_calc_command)))
    application.add_handler(CommandHandler("status", track_command(status_command)))
    application.add_handler(CommandHandler("model", track_command(model_command)))
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
    
    # 통합 메시지 핸들러 (자연어 IDE + 일반 AI)
    async def unified_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # 먼저 자연어 IDE 처리 시도
        ide_processed = await handle_natural_ide_request(update, context)
        # IDE에서 처리되지 않았으면 일반 AI로 처리
        if not ide_processed:
            await handle_message(update, context)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unified_message_handler))
    
    # 과제 파일 업로드 명령어 추가
    application.add_handler(CommandHandler("upload_homework", track_command(upload_homework_command)))
    application.add_handler(CommandHandler("upload", track_command(upload_homework_command)))  # 단축 명령어
    
    # 과제 설명 명령어 추가
    application.add_handler(CommandHandler("explain_homework", track_command(explain_homework_command)))
    application.add_handler(CommandHandler("explain", track_command(explain_homework_command)))  # 단축 명령어
    
    # 이메일 관련 명령어 추가
    application.add_handler(CommandHandler("email", track_command(email_command)))
    application.add_handler(CommandHandler("email_connect", track_command(email_connect_command)))
    application.add_handler(CommandHandler("email_check", track_command(email_check_command)))
    application.add_handler(CommandHandler("email_reply", track_command(email_reply_command)))
    application.add_handler(CommandHandler("email_ai_reply", track_command(email_ai_reply_command)))
    application.add_handler(CommandHandler("email_send_ai", track_command(email_send_ai_command)))
    
    # 구글 드라이브 관련 명령어 추가
    application.add_handler(CommandHandler("drive", track_command(drive_command)))
    application.add_handler(CommandHandler("drive_list", track_command(drive_list_command)))
    application.add_handler(CommandHandler("drive_read", track_command(drive_read_command)))
    application.add_handler(CommandHandler("drive_create", track_command(drive_create_command)))
    application.add_handler(CommandHandler("drive_update", track_command(drive_update_command)))
    
    # 사용자별 구글 드라이브 연동 (클라우드 IDE)
    application.add_handler(CommandHandler("connect_drive", track_command(connect_drive_command)))
    application.add_handler(CommandHandler("drive_status", track_command(drive_status_command)))
    application.add_handler(CommandHandler("disconnect_drive", track_command(disconnect_drive_command)))
    application.add_handler(CommandHandler("tree", track_command(tree_command)))
    application.add_handler(CommandHandler("mkdir", track_command(mkdir_command)))
    application.add_handler(CommandHandler("workspace", track_command(workspace_command)))
    application.add_handler(CommandHandler("create_workspace", track_command(create_workspace_command)))
    
    # 실시간 동기화 관련 명령어
    application.add_handler(CommandHandler("sync_status", track_command(sync_status_command)))
    application.add_handler(CommandHandler("sync_force", track_command(sync_force_command)))
    application.add_handler(CommandHandler("sync_interval", track_command(sync_interval_command)))
    application.add_handler(CommandHandler("test_sync", track_command(test_sync_command)))
    
    # 웹 검색 & 코드 테스트 기능 명령어 (4단계 업그레이드)
    application.add_handler(CommandHandler("search", track_command(search_command)))
    application.add_handler(CommandHandler("visit", track_command(visit_command)))
    application.add_handler(CommandHandler("search_visit", track_command(search_visit_command)))
    application.add_handler(CommandHandler("test_code", track_command(test_code_command)))
    application.add_handler(CommandHandler("snippets", track_command(snippets_command)))
    application.add_handler(CommandHandler("search_history", track_command(search_history_command)))
    
    # 고급 웹 자동화 명령어 (1단계 업그레이드)
    from advanced_web_commands import (
        auto_visit_command, screenshot_command, click_command, 
        type_command, extract_command, js_command, close_browser_command
    )
    application.add_handler(CommandHandler("auto_visit", track_command(auto_visit_command)))
    application.add_handler(CommandHandler("screenshot", track_command(screenshot_command)))
    application.add_handler(CommandHandler("click", track_command(click_command)))
    application.add_handler(CommandHandler("type", track_command(type_command)))
    application.add_handler(CommandHandler("extract", track_command(extract_command)))
    application.add_handler(CommandHandler("js", track_command(js_command)))
    application.add_handler(CommandHandler("close_browser", track_command(close_browser_command)))
    
    # 비동기 크롤링 시스템 명령어 (2단계 업그레이드)
    application.add_handler(CommandHandler("async_crawl", track_command(async_crawl_command)))
    application.add_handler(CommandHandler("async_search", track_command(async_search_command)))
    application.add_handler(CommandHandler("crawl_performance", track_command(crawl_performance_command)))
    
    # 최신 기술 정보 업데이트 명령어 (3단계 업그레이드)
    application.add_handler(CommandHandler("tech_summary", track_command(tech_summary_command)))
    application.add_handler(CommandHandler("github_trending", track_command(github_trending_command)))
    application.add_handler(CommandHandler("tech_news", track_command(tech_news_command)))
    application.add_handler(CommandHandler("stackoverflow", track_command(stackoverflow_command)))
    application.add_handler(CommandHandler("package_info", track_command(package_info_command)))
    application.add_handler(CommandHandler("tech_auto_update", track_command(tech_auto_update_command)))
    
    # 협업 및 공유 기능 명령어 (7단계)
    application.add_handler(CommandHandler("team", track_command(team_command)))
    application.add_handler(CommandHandler("team_create", track_command(team_create_command)))
    application.add_handler(CommandHandler("team_invite", track_command(team_invite_command)))
    application.add_handler(CommandHandler("team_list", track_command(team_list_command)))
    application.add_handler(CommandHandler("team_comment", track_command(team_comment_command)))
    application.add_handler(CommandHandler("team_comments", track_command(team_comments_command)))
    application.add_handler(CommandHandler("team_activity", track_command(team_activity_command)))
    application.add_handler(CommandHandler("instructor_dashboard", track_command(instructor_dashboard_command)))
    
    # 업무보고 관련 명령어 추가
    application.add_handler(CommandHandler("report", track_command(report_command)))
    application.add_handler(CommandHandler("report_status", track_command(report_status_command)))
    application.add_handler(CommandHandler("report_complete", track_command(report_complete_command)))
    application.add_handler(CommandHandler("report_cancel", track_command(report_cancel_command)))
    application.add_handler(CommandHandler("report_list", track_command(report_list_command)))
    application.add_handler(CommandHandler("report_view", track_command(report_view_command)))
    
    # 봇 실행
    print(f"SUCCESS: {BOT_USERNAME} bot is ready with full AI integration!")
    print("Bot URL: https://t.me/AI_Solarbot")
    print("Features: Gemini + ChatGPT, Solar Calculator, Homework System")
    print("Press Ctrl+C to stop.")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
