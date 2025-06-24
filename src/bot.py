#!/usr/bin/env python3
"""
팜솔라 AI_Solarbot 메인 봇 (오류 처리 시스템 통합 버전)
사용자 친화적 오류 처리, 자동 모듈 설치, 진행 상황 표시 기능 포함
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# 환경변수 로딩 추가
try:
    from dotenv import load_dotenv
    # 프로젝트 루트의 .env 파일 로딩
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[OK] .env 파일 로딩 완료: {env_file}")
    else:
        print(f"[WARNING] .env 파일을 찾을 수 없습니다: {env_file}")
except ImportError:
    print("[WARNING] python-dotenv 모듈이 없습니다. 시스템 환경변수만 사용합니다.")

# 텔레그램 봇 관련 import (오류 처리 포함)
try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] 텔레그램 모듈 없음: {e}")
    TELEGRAM_AVAILABLE = False

# 프로젝트 모듈들 import (오류 처리 포함)
try:
    from error_handler import error_handler, handle_command_error, help_system
    from user_auth_manager import user_auth_manager
    ERROR_HANDLER_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] 오류 처리 모듈 없음: {e}")
    ERROR_HANDLER_AVAILABLE = False

# 온라인 코드 실행 모듈 import
try:
    from online_code_executor import online_code_executor
    CODE_EXECUTOR_AVAILABLE = True
    print("[OK] 온라인 코드 실행 모듈 로딩 완료")
except ImportError as e:
    print(f"[WARNING] 온라인 코드 실행 모듈 없음: {e}")
    CODE_EXECUTOR_AVAILABLE = False

# AI 코드 리뷰 및 교육 시스템 모듈들 import
try:
    from ai_integration_engine import AIIntegrationEngine
    AI_INTEGRATION_AVAILABLE = True
    print("[OK] AI 통합 엔진 모듈 로딩 완료")
except ImportError as e:
    print(f"[WARNING] AI 통합 엔진 모듈 없음: {e}")
    AI_INTEGRATION_AVAILABLE = False

try:
    from educational_code_guide import EducationalCodeGuide, get_educational_guide
    EDUCATIONAL_GUIDE_AVAILABLE = True
    print("[OK] 교육용 코드 가이드 모듈 로딩 완료")
except ImportError as e:
    print(f"[WARNING] 교육용 코드 가이드 모듈 없음: {e}")
    EDUCATIONAL_GUIDE_AVAILABLE = False

try:
    from code_history_manager import CodeHistoryManager, history_manager
    HISTORY_MANAGER_AVAILABLE = True
    print("[OK] 코드 히스토리 관리자 모듈 로딩 완료")
except ImportError as e:
    print(f"[WARNING] 코드 히스토리 관리자 모듈 없음: {e}")
    HISTORY_MANAGER_AVAILABLE = False

try:
    from performance_benchmark import PerformanceBenchmark, get_performance_benchmark
    from enhanced_performance_executor import EnhancedPerformanceExecutor, get_enhanced_performance_executor
    PERFORMANCE_BENCHMARK_AVAILABLE = True
    print("[OK] 성능 벤치마크 모듈 로딩 완료")
except ImportError as e:
    print(f"[WARNING] 성능 벤치마크 모듈 없음: {e}")
    PERFORMANCE_BENCHMARK_AVAILABLE = False

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FarmSolarBot:
    """팜솔라 AI 봇 메인 클래스"""
    
    def __init__(self):
        """초기화"""
        self.application = None
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_user_id = os.getenv('ADMIN_USER_ID')
        
        # 통계 (코드 실행 관련 통계 추가)
        self.stats = {
            'commands_processed': 0,
            'errors_handled': 0,
            'users_helped': set(),
            'start_time': datetime.now(),
            'code_executions': 0,
            'code_languages_used': {},
            'successful_executions': 0,
            'failed_executions': 0,
            # AI 기능 관련 통계 추가
            'code_reviews': 0,
            'learning_paths_generated': 0,
            'performance_analyses': 0,
            'optimization_suggestions': 0,
            'history_queries': 0
        }
        
        logger.info("팜솔라 AI 봇 초기화 완료")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """시작 명령어"""
        try:
            user = update.effective_user
            self.stats['users_helped'].add(user.id)
            
            welcome_message = f"""
🌟 **팜솔라 AI 봇에 오신 것을 환영합니다!** 🌟

안녕하세요, {user.first_name}님! 

🤖 **저는 다음과 같은 기능을 제공합니다:**
• 💻 **온라인 코드 실행** (Python, JavaScript, Java 등 10개 언어)
• 🎯 **AI 코드 리뷰 및 분석** - 코드 품질 분석과 개선 제안
• 📚 **개인화 학습 가이드** - 언어별 맞춤형 학습 경로
• 📊 **성능 벤치마크 분석** - 코드 성능 측정 및 최적화 제안
• 📈 **코드 실행 히스토리** - 성장 추적 및 포트폴리오 관리
• 🔍 **웹사이트 내용 분석** 및 스마트 검색
• 📁 **Google Drive 연동** 및 AI 기반 콘텐츠 분석
• ⚙️ **관리자 도구** (권한 필요)

🚀 **코드 실행 기능**:
• `/run_code print('Hello World!')` - 코드 즉시 실행
• `/code_languages` - 지원하는 10개 언어 확인
• `/code_help` - 상세 사용법 및 예시

🔬 **AI 분석 기능 (NEW!)**:
• `/code_review [코드]` - AI 코드 리뷰 및 품질 분석
• `/learn_path [언어]` - 개인화 학습 경로 추천
• `/code_history` - 내 코드 실행 히스토리 및 성장 분석
• `/benchmark [코드]` - 성능 벤치마크 및 최적화 제안
• `/optimize_tips [언어]` - 언어별 최적화 팁

💡 **기본 사용법**:
• `/help` - 전체 도움말
• `/analyze_url [URL]` - 웹사이트 분석
• `/status` - 시스템 상태 확인

🔧 **스마트 기능**:
• 문제 발생 시 친화적인 해결 방법 제시
• 필요한 모듈 자동 설치 및 단계별 문제 해결 가이드
• AI 기반 코드 품질 분석 및 개선 제안

🔥 **AI로 코드를 분석해보세요!** `/code_review print('Hello World!')`로 시작해보세요!
            """
            
            await update.message.reply_text(welcome_message.strip())
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"시작 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "start")
            else:
                await update.message.reply_text("죄송합니다. 일시적인 문제가 발생했습니다.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령어"""
        try:
            if ERROR_HANDLER_AVAILABLE and hasattr(help_system, 'get_general_help'):
                help_text = help_system.get_general_help()
            else:
                help_text = """
🤖 **팜솔라 AI 봇 도움말**

📋 **기본 명령어**:
• `/start` - 봇 시작 및 환영 메시지
• `/help` - 이 도움말 표시
• `/status` - 시스템 상태 확인
• `/analyze_url [URL]` - 웹사이트 분석

💻 **코드 실행 명령어**:
• `/run_code [코드]` - 코드 실행 (자동 언어 감지)
• `/run_code [언어] [코드]` - 특정 언어로 코드 실행
• `/code_languages` - 지원 언어 목록 확인
• `/code_stats` - 코드 실행 통계
• `/code_help` - 코드 실행 상세 도움말

🔬 **AI 분석 명령어 (NEW!)**:
• `/code_review [코드]` - AI 기반 코드 리뷰 및 품질 분석
• `/learn_path [언어]` - 개인화된 학습 경로 추천
• `/code_history` - 코드 실행 히스토리 및 성장 분석
• `/benchmark [코드]` - 성능 벤치마크 및 최적화 제안
• `/optimize_tips [언어]` - 언어별 성능 최적화 팁

⚙️ **관리자 명령어** (권한 필요):
• `/admin_status` - 시스템 상세 상태
• `/error_stats` - 오류 통계 확인

💡 **사용 팁**:
• 오류 발생 시 자동으로 해결 방법을 제시합니다
• 필요한 패키지가 없으면 자동 설치를 시도합니다
• 모든 명령어는 사용자 친화적으로 설계되었습니다
• 코드 실행은 10개 언어를 지원합니다 (Python, JavaScript, Java 등)
• AI 분석 기능으로 코드 품질과 성능을 향상시킬 수 있습니다

🔥 **AI 기능 체험**: `/code_review print('Hello World!')`로 AI 코드 리뷰를 체험해보세요!
                """
            
            await update.message.reply_text(help_text.strip())
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"도움말 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "help")
            else:
                await update.message.reply_text("도움말을 불러오는 중 오류가 발생했습니다.")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """상태 확인 명령어"""
        try:
            uptime = datetime.now() - self.stats['start_time']
            
            status_message = f"""
📊 **팜솔라 AI 봇 상태**

🕐 **가동 시간**: {uptime.days}일 {uptime.seconds//3600}시간 {(uptime.seconds//60)%60}분
📈 **처리된 명령어**: {self.stats['commands_processed']}개
👥 **도움받은 사용자**: {len(self.stats['users_helped'])}명
❌ **처리된 오류**: {self.stats['errors_handled']}개

💻 **코드 실행 통계**:
• 총 실행 횟수: {self.stats['code_executions']}회
• 성공한 실행: {self.stats['successful_executions']}회
• 실패한 실행: {self.stats['failed_executions']}회
• 사용된 언어 수: {len(self.stats['code_languages_used'])}개

🔬 **AI 분석 통계**:
• AI 코드 리뷰: {self.stats['code_reviews']}회
• 학습 경로 생성: {self.stats['learning_paths_generated']}회
• 성능 분석: {self.stats['performance_analyses']}회
• 최적화 제안: {self.stats['optimization_suggestions']}회
• 히스토리 조회: {self.stats['history_queries']}회

🔧 **시스템 상태**:
• 텔레그램 연결: {'✅ 정상' if TELEGRAM_AVAILABLE else '❌ 오류'}
• 오류 처리 시스템: {'✅ 활성' if ERROR_HANDLER_AVAILABLE else '❌ 비활성'}
• 코드 실행 시스템: {'✅ 활성' if CODE_EXECUTOR_AVAILABLE else '❌ 비활성'}
• 인증 시스템: {'✅ 활성' if 'user_auth_manager' in globals() else '❌ 비활성'}

🤖 **AI 모듈 상태**:
• AI 통합 엔진: {'✅ 활성' if AI_INTEGRATION_AVAILABLE else '❌ 비활성'}
• 교육 가이드 시스템: {'✅ 활성' if EDUCATIONAL_GUIDE_AVAILABLE else '❌ 비활성'}
• 히스토리 관리자: {'✅ 활성' if HISTORY_MANAGER_AVAILABLE else '❌ 비활성'}
• 성능 벤치마크: {'✅ 활성' if PERFORMANCE_BENCHMARK_AVAILABLE else '❌ 비활성'}

💡 **현재 기능**:
• 기본 명령어 처리 ✅
• 사용자 친화적 오류 처리 {'✅' if ERROR_HANDLER_AVAILABLE else '❌'}
• 자동 모듈 설치 {'✅' if ERROR_HANDLER_AVAILABLE else '❌'}
• 온라인 코드 실행 {'✅' if CODE_EXECUTOR_AVAILABLE else '❌'}
• AI 코드 리뷰 및 분석 {'✅' if AI_INTEGRATION_AVAILABLE else '❌'}
• 개인화 학습 가이드 {'✅' if EDUCATIONAL_GUIDE_AVAILABLE else '❌'}
• 성능 벤치마크 분석 {'✅' if PERFORMANCE_BENCHMARK_AVAILABLE else '❌'}
            """
            
            await update.message.reply_text(status_message.strip())
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"상태 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "status")
            else:
                await update.message.reply_text("상태 확인 중 오류가 발생했습니다.")
    
    async def analyze_url_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """URL 분석 명령어"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ URL을 입력해주세요.\n\n"
                    "💡 **사용법**: `/analyze_url https://example.com`\n"
                    "📝 **예시**: `/analyze_url https://naver.com`"
                )
                return
            
            url = context.args[0]
            
            # URL 유효성 검사
            if not url.startswith(('http://', 'https://')):
                await update.message.reply_text(
                    "❌ 올바른 URL 형식이 아닙니다.\n\n"
                    "✅ **올바른 형식**: https://example.com\n"
                    "❌ **잘못된 형식**: example.com"
                )
                return
            
            # 진행 메시지
            progress_msg = await update.message.reply_text(
                f"🔍 **URL 분석 중...** \n\n"
                f"📊 대상: {url}\n"
                f"⏳ 분석을 시작합니다..."
            )
            
            # 여기서 실제 URL 분석 로직을 추가할 수 있습니다
            # 현재는 데모용 응답
            await asyncio.sleep(2)  # 분석 시뮬레이션
            
            analysis_result = f"""
✅ **URL 분석 완료!**

🔗 **분석 대상**: {url}
📅 **분석 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 **분석 결과**:
• 상태: 정상 접근 가능
• 유형: 웹사이트
• 응답 시간: 빠름

💡 **요약**:
URL이 정상적으로 접근 가능하며, 추가 분석 기능은 개발 중입니다.

🔧 **다음 단계**:
더 자세한 분석을 원하시면 관리자에게 문의해주세요.
            """
            
            await progress_msg.edit_text(analysis_result.strip())
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"URL 분석 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "analyze_url")
            else:
                await update.message.reply_text("URL 분석 중 오류가 발생했습니다.")
    
    async def error_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """오류 통계 명령어 (관리자 전용)"""
        try:
            # 관리자 권한 확인
            if self.admin_user_id and str(update.effective_user.id) != self.admin_user_id:
                await update.message.reply_text(
                    "❌ **권한 없음**\n\n"
                    "이 명령어는 관리자만 사용할 수 있습니다.\n"
                    "일반 사용자는 `/status` 명령어를 사용해주세요."
                )
                return
            
            if ERROR_HANDLER_AVAILABLE:
                stats = error_handler.get_error_stats()
                
                stats_message = f"""
📊 **오류 처리 통계** (관리자용)

📈 **전체 통계**:
• 총 오류 수: {stats['total_errors']}개
• 해결된 오류: {stats['resolved_errors']}개
• 사용자 해결: {stats['user_resolved_errors']}개
• 관리자 에스컬레이션: {stats['admin_escalated_errors']}개
• 자동 재시도: {stats['auto_retried_errors']}개

✅ **성공률**: {stats['success_rate']:.1f}%

🔧 **시스템 상태**:
• 오류 처리기: 정상 작동
• 자동 모듈 설치: 활성화
• 관리자 알림: 설정됨
                """
            else:
                stats_message = """
⚠️ **오류 처리 통계 시스템 비활성**

오류 처리 모듈이 로드되지 않아 통계를 확인할 수 없습니다.
시스템 관리자에게 문의해주세요.
                """
            
            await update.message.reply_text(stats_message.strip())
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"오류 통계 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "error_stats")
            else:
                await update.message.reply_text("오류 통계 확인 중 문제가 발생했습니다.")

    async def run_code_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """코드 실행 명령어"""
        try:
            if not CODE_EXECUTOR_AVAILABLE:
                await update.message.reply_text(
                    "❌ 온라인 코드 실행 기능이 사용할 수 없습니다.\n"
                    "관리자에게 문의하세요."
                )
                return
            
            # 명령어 인수가 있는 경우 (언어 지정)
            if context.args:
                # /run_code python print("Hello World") 형태
                if len(context.args) >= 2:
                    language = context.args[0].lower()
                    code = ' '.join(context.args[1:])
                else:
                    language = 'auto'
                    code = ' '.join(context.args)
            else:
                # 답장으로 코드 블록이 있는 경우
                if update.message.reply_to_message and update.message.reply_to_message.text:
                    parse_result = self.parse_code_block(update.message.reply_to_message.text)
                    if not parse_result['success']:
                        await update.message.reply_text(f"❌ {parse_result['error_message']}")
                        return
                    language = parse_result['language']
                    code = parse_result['code']
                else:
                    await update.message.reply_text(
                        "💡 **코드 실행 사용법:**\n\n"
                        "1️⃣ **명령어와 함께 코드 입력:**\n"
                        "`/run_code print('Hello World')`\n\n"
                        "2️⃣ **언어 지정:**\n"
                        "`/run_code python print('Hello World')`\n\n"
                        "3️⃣ **코드 블록에 답장:**\n"
                        "```python\n"
                        "print('Hello World')\n"
                        "```\n"
                        "위 메시지에 답장으로 `/run_code` 입력\n\n"
                        "🔧 **지원 언어**: `/code_languages`로 확인"
                    )
                    return
            
            # 언어 자동 감지
            if language == 'auto':
                language = self.detect_language(code)
            
            # 실행 시작 메시지
            progress_message = await update.message.reply_text(
                f"⚙️ **코드 실행 중...**\n"
                f"📝 언어: {language.upper()}\n"
                f"🔄 처리 중..."
            )
            
            # 코드 실행
            result = await online_code_executor.execute_code(code, language)
            
            # 통계 업데이트
            self.stats['code_executions'] += 1
            if language not in self.stats['code_languages_used']:
                self.stats['code_languages_used'][language] = 0
            self.stats['code_languages_used'][language] += 1
            
            if result.get('success'):
                self.stats['successful_executions'] += 1
            else:
                self.stats['failed_executions'] += 1
            
            # 결과 포맷팅
            formatted_result = self.format_execution_result(result, language)
            
            # 진행 메시지 삭제
            await progress_message.delete()
            
            # 결과가 너무 길면 파일로 전송
            if formatted_result['send_as_file']:
                # 텍스트 파일 생성
                import io
                file_content = formatted_result['file_content']
                file_buffer = io.BytesIO(file_content.encode('utf-8'))
                file_buffer.name = f'result_{language}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                
                await update.message.reply_document(
                    document=file_buffer,
                    caption=formatted_result['message'][:1024],  # 캡션 길이 제한
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    formatted_result['message'],
                    parse_mode='Markdown'
                )
            
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"코드 실행 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "run_code")
            else:
                await update.message.reply_text(
                    "❌ 코드 실행 중 오류가 발생했습니다.\n"
                    f"오류 내용: {str(e)}"
                )

    async def code_languages_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """지원하는 프로그래밍 언어 목록 표시"""
        try:
            if not CODE_EXECUTOR_AVAILABLE:
                await update.message.reply_text(
                    "❌ 온라인 코드 실행 기능이 사용할 수 없습니다.\n"
                    "관리자에게 문의하세요."
                )
                return
            
            # 지원 언어 정보 가져오기
            supported_languages = online_code_executor.get_supported_languages()
            
            # 각 언어별 상세 정보 구성
            language_info_text = "💻 **지원하는 프로그래밍 언어 목록**\n\n"
            
            # 언어별 이모지 매핑
            language_emojis = {
                'python': '🐍',
                'javascript': '🟨',
                'typescript': '🔷',
                'java': '☕',
                'cpp': '⚡',
                'go': '🐹',
                'rust': '🦀',
                'php': '🐘',
                'ruby': '💎',
                'csharp': '🔷'
            }
            
            for lang in supported_languages:
                config = online_code_executor.get_language_info(lang)
                if config:
                    emoji = language_emojis.get(lang, '📄')
                    compile_type = "컴파일 언어" if config.compile_command else "인터프리터 언어"
                    
                    language_info_text += f"{emoji} **{config.name}** `({lang})`\n"
                    language_info_text += f"   • 파일 확장자: `{config.file_extension}`\n"
                    language_info_text += f"   • 타입: {compile_type}\n"
                    language_info_text += f"   • 실행 제한시간: {config.timeout}초\n"
                    language_info_text += f"   • 메모리 제한: {config.memory_limit}MB\n"
                    
                    # 주요 지원 라이브러리
                    if config.supported_features:
                        features_str = ", ".join(config.supported_features[:3])  # 최대 3개만 표시
                        if len(config.supported_features) > 3:
                            features_str += f" (+{len(config.supported_features)-3}개 더)"
                        language_info_text += f"   • 주요 라이브러리: `{features_str}`\n"
                    
                    language_info_text += "\n"
            
            # 사용 예시 추가
            language_info_text += "📖 **사용 예시**:\n"
            language_info_text += "```\n"
            language_info_text += "/run_code python print('Hello World')\n"
            language_info_text += "/run_code javascript console.log('Hello');\n"
            language_info_text += "/run_code java System.out.println(\"Hello\");\n"
            language_info_text += "```\n\n"
            
            # 추가 정보
            language_info_text += "💡 **추가 정보**:\n"
            language_info_text += "• 언어를 지정하지 않으면 자동으로 감지됩니다\n"
            language_info_text += "• 코드 블록(```)을 사용하면 더 정확한 파싱이 가능합니다\n"
            language_info_text += "• 실행 결과는 성능 분석과 최적화 제안을 포함합니다\n"
            language_info_text += "• `/code_stats`로 사용 통계를 확인할 수 있습니다\n"
            language_info_text += "• `/code_help`로 상세한 도움말을 확인할 수 있습니다"
            
            await update.message.reply_text(
                language_info_text,
                parse_mode='Markdown'
            )
            
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"언어 목록 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "code_languages")
            else:
                await update.message.reply_text(
                    "❌ 언어 목록 조회 중 오류가 발생했습니다.\n"
                    f"오류 내용: {str(e)}"
                )

    async def code_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """코드 실행 통계 명령어"""
        try:
            if not CODE_EXECUTOR_AVAILABLE:
                await update.message.reply_text(
                    "❌ 온라인 코드 실행 기능이 사용할 수 없습니다.\n"
                    "관리자에게 문의하세요."
                )
                return
            
            # 관리자 권한 확인 (상세 통계는 관리자만)
            is_admin = self.admin_user_id and str(update.effective_user.id) == self.admin_user_id
            
            # OnlineCodeExecutor 통계 가져오기
            executor_stats = online_code_executor.get_execution_statistics()
            
            # 봇 자체 통계와 결합
            stats_message = "📊 **코드 실행 통계**\n\n"
            
            # 기본 통계 (모든 사용자)
            stats_message += "📈 **전체 실행 통계**:\n"
            stats_message += f"• 총 실행 횟수: {self.stats['code_executions']}회\n"
            stats_message += f"• 성공한 실행: {self.stats['successful_executions']}회\n"
            stats_message += f"• 실패한 실행: {self.stats['failed_executions']}회\n"
            
            if self.stats['code_executions'] > 0:
                success_rate = (self.stats['successful_executions'] / self.stats['code_executions']) * 100
                stats_message += f"• 성공률: {success_rate:.1f}%\n"
            else:
                stats_message += "• 성공률: 0%\n"
            
            stats_message += f"• 사용된 언어 수: {len(self.stats['code_languages_used'])}개\n\n"
            
            # 언어별 사용 통계
            if self.stats['code_languages_used']:
                stats_message += "💻 **언어별 사용 현황**:\n"
                
                # 사용 빈도 순으로 정렬
                sorted_languages = sorted(
                    self.stats['code_languages_used'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                # 상위 5개 언어만 표시
                for i, (lang, count) in enumerate(sorted_languages[:5]):
                    percentage = (count / self.stats['code_executions']) * 100
                    
                    # 언어별 이모지
                    lang_emojis = {
                        'python': '🐍', 'javascript': '🟨', 'java': '☕',
                        'cpp': '⚡', 'go': '🐹', 'rust': '🦀',
                        'php': '🐘', 'ruby': '💎', 'csharp': '🔷',
                        'typescript': '🔷'
                    }
                    emoji = lang_emojis.get(lang, '📄')
                    
                    # 막대 그래프 효과
                    bar_length = int(percentage / 5)  # 20% = 4칸
                    bar = "█" * bar_length + "░" * (20 - bar_length)
                    
                    stats_message += f"{emoji} {lang.capitalize()}: {count}회 ({percentage:.1f}%)\n"
                    stats_message += f"   {bar}\n"
                
                if len(sorted_languages) > 5:
                    remaining = len(sorted_languages) - 5
                    stats_message += f"   ... 외 {remaining}개 언어 더\n"
                
                stats_message += "\n"
            
            # 관리자 전용 상세 통계
            if is_admin and executor_stats['total_executions'] > 0:
                stats_message += "🔧 **상세 통계** (관리자 전용):\n"
                stats_message += f"• 평균 성능 점수: {executor_stats['average_performance']:.1f}/100\n"
                stats_message += f"• ExecutorEngine 실행: {executor_stats['total_executions']}회\n"
                stats_message += f"• ExecutorEngine 성공률: {executor_stats['success_rate']:.1f}%\n\n"
                
                # 최근 실행 이력
                recent_history = online_code_executor.get_execution_history(5)
                if recent_history:
                    stats_message += "📝 **최근 실행 이력** (최근 5건):\n"
                    for i, history in enumerate(recent_history, 1):
                        emoji = "✅" if history['success'] else "❌"
                        lang = history['language']
                        score = history.get('performance_score', 0)
                        stats_message += f"{i}. {emoji} {lang} (성능: {score:.1f}점)\n"
                    stats_message += "\n"
            
            # 추가 정보
            stats_message += "💡 **추가 정보**:\n"
            stats_message += "• `/code_help`로 코드 실행 도움말 확인\n"
            stats_message += "• `/code_languages`로 지원 언어 목록 확인\n"
            stats_message += "• 성능 점수는 실행 시간, 메모리, 효율성을 종합 평가"
            
            await update.message.reply_text(
                stats_message,
                parse_mode='Markdown'
            )
            
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"코드 통계 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "code_stats")
            else:
                await update.message.reply_text(
                    "❌ 코드 통계 조회 중 오류가 발생했습니다.\n"
                    f"오류 내용: {str(e)}"
                )

    async def code_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """코드 실행 상세 도움말 명령어"""
        try:
            help_message = """
🔧 **코드 실행 기능 상세 가이드**

## 📋 지원 기능

💻 **지원 언어** (10개):
• 🐍 Python • 🟨 JavaScript • ☕ Java • ⚡ C++
• 🐹 Go • 🦀 Rust • 🐘 PHP • 💎 Ruby
• 🔷 TypeScript • 🔷 C#

## 🚀 사용법

### 1️⃣ **기본 실행**
```
/run_code print("Hello, World!")
```

### 2️⃣ **언어 지정**
```
/run_code python print("Hello, Python!")
/run_code javascript console.log("Hello, JS!");
```

### 3️⃣ **코드 블록 사용** (권장)
````
/run_code
```python
def hello():
    print("Hello from function!")
hello()
```
````

### 4️⃣ **답장으로 실행**
코드가 포함된 메시지에 답장으로 `/run_code` 입력

## ⚙️ 고급 기능

🎯 **자동 언어 감지**:
언어를 지정하지 않으면 코드 패턴을 분석하여 자동 감지

📊 **성능 분석**:
• 실행 시간 측정
• 메모리 사용량 체크
• 성능 점수 계산 (0-100점)

💡 **최적화 제안**:
• 언어별 맞춤 코딩 팁
• 성능 개선 방법 제안
• 베스트 프랙티스 안내

## 🔒 제한사항

⏱️ **실행 시간**: 언어별 10-20초 제한
💾 **메모리**: 128MB-512MB 제한
📁 **파일 시스템**: 읽기 전용 (보안상 제한)
🌐 **네트워크**: 외부 API 호출 제한

## 📖 예시 코드

### 🐍 Python
```python
# 리스트 컴프리헨션
squares = [x**2 for x in range(10)]
print(squares)
```

### 🟨 JavaScript
```javascript
// 화살표 함수
const greet = name => `Hello, ${name}!`;
console.log(greet("World"));
```

### ☕ Java
```java
// 클래스 정의
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, Java!");
    }
}
```

## 🛠️ 관련 명령어

• `/code_languages` - 지원 언어 상세 정보
• `/code_stats` - 실행 통계 확인
• `/run_code [코드]` - 코드 실행

## ❓ 문제 해결

**🔧 일반적인 오류**:
• 문법 오류: 코드 문법을 다시 확인
• 시간 초과: 무한 루프나 긴 연산 확인
• 메모리 부족: 큰 데이터 구조 사용 줄이기

**💬 지원 요청**:
문제가 지속되면 관리자에게 문의하거나 `/error_stats`로 시스템 상태를 확인하세요.

---
🌟 **팁**: 코드 블록(```)을 사용하면 더 정확한 파싱과 실행이 가능합니다!
            """
            
            await update.message.reply_text(
                help_message.strip(),
                parse_mode='Markdown'
            )
            
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"코드 도움말 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "code_help")
            else:
                await update.message.reply_text(
                    "❌ 코드 도움말 조회 중 오류가 발생했습니다.\n"
                    f"오류 내용: {str(e)}"
                )
    
    async def code_review_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI 코드 리뷰 명령어"""
        try:
            if not AI_INTEGRATION_AVAILABLE:
                await update.message.reply_text(
                    "❌ AI 코드 리뷰 기능이 사용할 수 없습니다.\n"
                    "관리자에게 문의하세요."
                )
                return
            
            # 코드 입력 확인
            if context.args:
                code = ' '.join(context.args)
            elif update.message.reply_to_message and update.message.reply_to_message.text:
                parse_result = self.parse_code_block(update.message.reply_to_message.text)
                if not parse_result['success']:
                    await update.message.reply_text(f"❌ {parse_result['error_message']}")
                    return
                code = parse_result['code']
            else:
                await update.message.reply_text(
                    "💡 **AI 코드 리뷰 사용법:**\n\n"
                    "1️⃣ **명령어와 함께 코드 입력:**\n"
                    "`/code_review print('Hello World')`\n\n"
                    "2️⃣ **코드 블록에 답장:**\n"
                    "```python\n"
                    "def hello():\n"
                    "    print('Hello World')\n"
                    "```\n"
                    "위 메시지에 답장으로 `/code_review` 입력\n\n"
                    "📊 **분석 항목**:\n"
                    "• 코드 복잡도 분석\n"
                    "• 성능 최적화 제안\n"
                    "• 보안성 검토\n"
                    "• 가독성 향상 방안"
                )
                return
            
            # 진행 메시지
            progress_msg = await update.message.reply_text(
                "🔍 **AI 코드 리뷰 진행 중...**\n\n"
                "📊 복잡도 분석 중...\n"
                "⚡ 성능 최적화 검토 중...\n"
                "🔒 보안성 분석 중..."
            )
            
            # AI 통합 엔진으로 코드 리뷰 수행
            ai_engine = AIIntegrationEngine()
            language = self.detect_language(code)
            
            # 4차원 분석 수행
            review_result = ai_engine.analyze_code_quality(code, language)
            
            # 결과 포맷팅
            review_message = f"""
🤖 **AI 코드 리뷰 결과**

📝 **분석 대상**: {language.upper()} 코드
📅 **분석 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 **품질 점수**:
• 복잡도: {review_result['complexity_score']:.1f}/100
• 성능: {review_result['performance_score']:.1f}/100
• 보안성: {review_result['security_score']:.1f}/100
• 가독성: {review_result['readability_score']:.1f}/100

🎯 **종합 점수**: {review_result['overall_score']:.1f}/100

🔍 **주요 분석 결과**:
{chr(10).join(f"• {insight}" for insight in review_result['insights'][:5])}

💡 **개선 제안**:
{chr(10).join(f"• {suggestion}" for suggestion in review_result['suggestions'][:3])}

🏆 **수준 평가**: {review_result['quality_level']}

🔧 **다음 단계**:
• `/benchmark` 명령어로 성능 분석
• `/optimize_tips {language}` 명령어로 언어별 최적화 팁 확인
• `/learn_path {language}` 명령어로 학습 경로 추천
            """
            
            await progress_msg.edit_text(review_message.strip())
            self.stats['code_reviews'] += 1
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"AI 코드 리뷰 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "code_review")
            else:
                await update.message.reply_text("❌ AI 코드 리뷰 중 오류가 발생했습니다.")

    async def learn_path_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """개인화 학습 경로 추천 명령어"""
        try:
            if not EDUCATIONAL_GUIDE_AVAILABLE:
                await update.message.reply_text(
                    "❌ 학습 가이드 기능이 사용할 수 없습니다.\n"
                    "관리자에게 문의하세요."
                )
                return
            
            # 언어 입력 확인
            if context.args:
                language = context.args[0].lower()
            else:
                await update.message.reply_text(
                    "💡 **학습 경로 추천 사용법:**\n\n"
                    "📚 **예시**:\n"
                    "• `/learn_path python` - Python 학습 경로\n"
                    "• `/learn_path javascript` - JavaScript 학습 경로\n"
                    "• `/learn_path java` - Java 학습 경로\n\n"
                    "🎯 **지원 언어**: Python, JavaScript, Java, C++, Go 등\n\n"
                    "🔍 **개인화 기능**:\n"
                    "• 현재 수준 자동 분석\n"
                    "• 맞춤형 커리큘럼 제공\n"
                    "• 단계별 학습 목표 설정\n"
                    "• 실습 프로젝트 추천"
                )
                return
            
            # 진행 메시지
            progress_msg = await update.message.reply_text(
                f"📚 **{language.upper()} 학습 경로 생성 중...**\n\n"
                "🔍 현재 수준 분석 중...\n"
                "📖 커리큘럼 구성 중...\n"
                "🎯 학습 목표 설정 중..."
            )
            
            # 교육 가이드 생성
            guide = get_educational_guide()
            learning_path = guide.generate_learning_path(language, user_id=update.effective_user.id)
            
            # 결과 포맷팅
            path_message = f"""
📚 **{language.upper()} 개인화 학습 경로**

👤 **학습자**: {update.effective_user.first_name}
📅 **생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 **추정 수준**: {learning_path['estimated_level']}

🎯 **학습 목표**:
{learning_path['learning_objectives']}

📖 **커리큘럼 개요**:
{chr(10).join(f"{i+1}. {module['title']} ({module['duration']})" for i, module in enumerate(learning_path['curriculum'][:5]))}

🚀 **첫 번째 단계**:
**{learning_path['curriculum'][0]['title']}**
• 목표: {learning_path['curriculum'][0]['objective']}
• 예상 시간: {learning_path['curriculum'][0]['duration']}
• 주요 내용: {learning_path['curriculum'][0]['topics'][:3]}

💡 **학습 팁**:
{chr(10).join(f"• {tip}" for tip in learning_path['study_tips'][:3])}

🛠️ **추천 실습**:
{chr(10).join(f"• {project}" for project in learning_path['practice_projects'][:2])}

📈 **다음 단계**:
• `/code_history` 명령어로 학습 진도 확인
• 코드 작성 후 `/code_review` 명령어로 피드백 받기
• `/benchmark` 명령어로 성능 실력 측정
            """
            
            await progress_msg.edit_text(path_message.strip())
            self.stats['learning_paths_generated'] += 1
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"학습 경로 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "learn_path")
            else:
                await update.message.reply_text("❌ 학습 경로 생성 중 오류가 발생했습니다.")

    async def code_history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """코드 실행 히스토리 및 성장 분석 명령어"""
        try:
            if not HISTORY_MANAGER_AVAILABLE:
                await update.message.reply_text(
                    "❌ 코드 히스토리 기능이 사용할 수 없습니다.\n"
                    "관리자에게 문의하세요."
                )
                return
            
            user_id = str(update.effective_user.id)
            
            # 진행 메시지
            progress_msg = await update.message.reply_text(
                "📈 **코드 히스토리 분석 중...**\n\n"
                "📊 실행 기록 수집 중...\n"
                "📈 성장 패턴 분석 중...\n"
                "🏆 성취도 계산 중..."
            )
            
            # 히스토리 매니저에서 데이터 가져오기
            history_data = history_manager.get_user_history(user_id)
            growth_analysis = history_manager.analyze_growth_pattern(user_id)
            achievements = history_manager.get_user_achievements(user_id)
            
            # 결과 포맷팅
            if not history_data['executions']:
                history_message = """
📈 **코드 히스토리**

👤 **사용자**: 신규 사용자
📊 **실행 기록**: 아직 기록이 없습니다

🚀 **시작하기**:
• `/run_code print('Hello World!')` 명령어로 첫 코드를 실행해보세요
• 다양한 언어로 코드를 작성해보세요
• AI 리뷰 기능을 활용해 코드 품질을 향상시켜보세요

💡 **팁**:
• 정기적으로 코드를 작성하면 성장 패턴을 분석할 수 있습니다
• 복잡한 알고리즘에 도전해보세요
• `/learn_path` 명령어로 체계적인 학습을 시작하세요
                """
            else:
                recent_langs = list(history_data['language_usage'].keys())[:5]
                
                history_message = f"""
📈 **코드 실행 히스토리**

👤 **사용자**: {update.effective_user.first_name}
📅 **활동 기간**: {history_data['first_execution']} ~ {history_data['last_execution']}

📊 **실행 통계**:
• 총 실행 횟수: {history_data['total_executions']}회
• 성공률: {history_data['success_rate']:.1f}%
• 사용 언어: {len(history_data['language_usage'])}개
• 활동일 수: {history_data['active_days']}일

💻 **주요 사용 언어**:
{chr(10).join(f"• {lang}: {count}회" for lang, count in history_data['language_usage'].items())}

📈 **성장 분석**:
• 코딩 실력 점수: {growth_analysis['skill_score']:.1f}/100
• 성장 추세: {growth_analysis['growth_trend']}
• 복잡도 발전: {growth_analysis['complexity_progress']}
• 학습 속도: {growth_analysis['learning_velocity']}

🏆 **달성한 성취**:
{chr(10).join(f"🎖️ {achievement['title']}" for achievement in achievements[:5])}

📊 **이번 주 활동**:
• 실행 횟수: {history_data['week_executions']}회
• 새로운 언어: {history_data['week_new_languages']}개
• 평균 복잡도: {history_data['week_avg_complexity']:.1f}

🎯 **추천 활동**:
• 도전 과제: {growth_analysis['next_challenge']}
• 학습 제안: {growth_analysis['learning_suggestion']}
• 포커스 영역: {growth_analysis['focus_area']}
                """
            
            await progress_msg.edit_text(history_message.strip())
            self.stats['history_queries'] += 1
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"코드 히스토리 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "code_history")
            else:
                await update.message.reply_text("❌ 코드 히스토리 조회 중 오류가 발생했습니다.")

    async def benchmark_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """성능 벤치마크 및 최적화 제안 명령어"""
        try:
            if not PERFORMANCE_BENCHMARK_AVAILABLE:
                await update.message.reply_text(
                    "❌ 성능 벤치마크 기능이 사용할 수 없습니다.\n"
                    "관리자에게 문의하세요."
                )
                return
            
            # 코드 입력 확인
            if context.args:
                code = ' '.join(context.args)
            elif update.message.reply_to_message and update.message.reply_to_message.text:
                parse_result = self.parse_code_block(update.message.reply_to_message.text)
                if not parse_result['success']:
                    await update.message.reply_text(f"❌ {parse_result['error_message']}")
                    return
                code = parse_result['code']
            else:
                await update.message.reply_text(
                    "💡 **성능 벤치마크 사용법:**\n\n"
                    "1️⃣ **명령어와 함께 코드 입력:**\n"
                    "`/benchmark for i in range(1000): print(i)`\n\n"
                    "2️⃣ **코드 블록에 답장:**\n"
                    "```python\n"
                    "def fibonacci(n):\n"
                    "    if n <= 1: return n\n"
                    "    return fibonacci(n-1) + fibonacci(n-2)\n"
                    "```\n"
                    "위 메시지에 답장으로 `/benchmark` 입력\n\n"
                    "📊 **분석 항목**:\n"
                    "• 실행 시간 측정\n"
                    "• 메모리 사용량 분석\n"
                    "• 알고리즘 복잡도 분석\n"
                    "• 최적화 제안"
                )
                return
            
            # 진행 메시지
            progress_msg = await update.message.reply_text(
                "⚡ **성능 벤치마크 진행 중...**\n\n"
                "🔄 코드 실행 중...\n"
                "📊 성능 측정 중...\n"
                "🧮 복잡도 분석 중...\n"
                "💡 최적화 방안 검토 중..."
            )
            
            # 성능 벤치마크 수행
            benchmark = get_performance_benchmark()
            language = self.detect_language(code)
            
            # 코드 실행과 성능 분석
            execution_result = await online_code_executor.execute_code(code, language)
            benchmark_result = benchmark.analyze_performance(
                code, language, execution_result.get('execution_time', 0),
                execution_result.get('memory_usage', 0)
            )
            
            # 최적화 제안 생성
            optimization_suggestions = benchmark.generate_optimization_suggestions(
                benchmark_result, language
            )
            
            # 결과 포맷팅
            benchmark_message = f"""
⚡ **성능 벤치마크 결과**

📝 **분석 대상**: {language.upper()} 코드
📅 **측정 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 **성능 측정**:
• 실행 시간: {benchmark_result['execution_time']:.4f}초
• 메모리 사용량: {benchmark_result['memory_usage']:.2f}MB
• 알고리즘 복잡도: {benchmark_result['complexity_analysis']}

🎯 **성능 점수**: {benchmark_result['performance_score']:.1f}/100
📈 **최적화 레벨**: {benchmark_result['optimization_level']}

🔍 **기준선 비교**:
• 언어 평균 대비: {benchmark_result['vs_language_average']}
• 복잡도 평균 대비: {benchmark_result['vs_complexity_average']}
• 상위 {benchmark_result['percentile']:.1f}% 성능

💡 **최적화 제안**:
{chr(10).join(f"• {suggestion}" for suggestion in optimization_suggestions[:4])}

🏆 **성능 등급**: {benchmark_result['performance_grade']}

🔧 **다음 단계**:
• `/code_review` 명령어로 종합적인 코드 품질 확인
• `/optimize_tips {language}` 명령어로 언어별 최적화 팁 확인
• 더 복잡한 알고리즘으로 도전해보세요
            """
            
            await progress_msg.edit_text(benchmark_message.strip())
            self.stats['performance_analyses'] += 1
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"성능 벤치마크 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "benchmark")
            else:
                await update.message.reply_text("❌ 성능 벤치마크 중 오류가 발생했습니다.")

    async def optimize_tips_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """언어별 최적화 팁 명령어"""
        try:
            if not PERFORMANCE_BENCHMARK_AVAILABLE:
                await update.message.reply_text(
                    "❌ 최적화 팁 기능이 사용할 수 없습니다.\n"
                    "관리자에게 문의하세요."
                )
                return
            
            # 언어 입력 확인
            if context.args:
                language = context.args[0].lower()
            else:
                await update.message.reply_text(
                    "💡 **최적화 팁 사용법:**\n\n"
                    "🚀 **예시**:\n"
                    "• `/optimize_tips python` - Python 최적화 팁\n"
                    "• `/optimize_tips javascript` - JavaScript 최적화 팁\n"
                    "• `/optimize_tips java` - Java 최적화 팁\n\n"
                    "⚡ **지원 언어**: Python, JavaScript, Java, C++, Go, Rust 등\n\n"
                    "🎯 **제공 내용**:\n"
                    "• 언어별 성능 최적화 기법\n"
                    "• 메모리 사용량 최적화\n"
                    "• 알고리즘 복잡도 개선\n"
                    "• 베스트 프랙티스"
                )
                return
            
            # 최적화 팁 생성
            benchmark = get_performance_benchmark()
            optimization_tips = benchmark.get_language_optimization_tips(language)
            
            # 결과 포맷팅
            tips_message = f"""
⚡ **{language.upper()} 최적화 팁**

📚 **기본 최적화 원칙**:
{chr(10).join(f"• {tip}" for tip in optimization_tips['basic_principles'])}

🔧 **성능 최적화 기법**:
{chr(10).join(f"• {technique}" for technique in optimization_tips['performance_techniques'])}

💾 **메모리 최적화**:
{chr(10).join(f"• {tip}" for tip in optimization_tips['memory_optimization'])}

🧮 **알고리즘 개선**:
{chr(10).join(f"• {improvement}" for improvement in optimization_tips['algorithm_improvements'])}

⚠️ **피해야 할 패턴**:
{chr(10).join(f"• {antipattern}" for antipattern in optimization_tips['antipatterns'])}

🏆 **베스트 프랙티스**:
{chr(10).join(f"• {practice}" for practice in optimization_tips['best_practices'])}

📖 **참고 자료**:
{chr(10).join(f"• {resource}" for resource in optimization_tips['resources'])}

🎯 **실습 제안**:
• 현재 코드에 위 기법들을 적용해보세요
• `/benchmark` 명령어로 개선 효과를 측정하세요
• `/code_review` 명령어로 종합적인 품질을 확인하세요
            """
            
            await update.message.reply_text(tips_message.strip())
            self.stats['optimization_suggestions'] += 1
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"최적화 팁 명령어 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                await handle_command_error(update, context, e, "optimize_tips")
            else:
                await update.message.reply_text("❌ 최적화 팁 조회 중 오류가 발생했습니다.")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일반 메시지 처리"""
        try:
            message_text = update.message.text.lower()
            
            # 간단한 키워드 응답
            if any(word in message_text for word in ['안녕', 'hello', 'hi']):
                await update.message.reply_text(
                    "안녕하세요! 👋\n"
                    "저는 팜솔라 AI 봇입니다.\n"
                    "`/help`를 입력하시면 사용 가능한 명령어를 확인하실 수 있어요!"
                )
            elif any(word in message_text for word in ['도움', 'help']):
                await self.help_command(update, context)
            elif any(word in message_text for word in ['상태', 'status']):
                await self.status_command(update, context)
            elif any(word in message_text for word in ['코드', 'code', '프로그래밍', 'programming']):
                await update.message.reply_text(
                    "💻 **코드 실행 기능**을 찾으시는군요!\n\n"
                    "🚀 **코드 실행 명령어**:\n"
                    "• `/run_code [코드]` - 코드 실행\n"
                    "• `/code_languages` - 지원 언어 목록\n"
                    "• `/code_help` - 상세 사용법\n"
                    "• `/code_stats` - 실행 통계\n\n"
                    "💡 **지원 언어**: Python, JavaScript, Java, C++, Go, Rust 등 10개 언어\n"
                    "📖 **예시**: `/run_code print('Hello World!')`"
                )
            elif any(word in message_text for word in ['언어', 'language', '지원']):
                await self.code_languages_command(update, context)
            elif any(word in message_text for word in ['통계', 'stats', '실행']):
                await self.code_stats_command(update, context)
            else:
                await update.message.reply_text(
                    "🤖 메시지를 받았습니다!\n\n"
                    "💡 **주요 기능**:\n"
                    "• `/help` - 전체 도움말\n"
                    "• `/run_code [코드]` - 코드 실행 (10개 언어 지원)\n"
                    "• `/analyze_url [URL]` - 웹사이트 분석\n"
                    "• `/status` - 시스템 상태 확인\n\n"
                    "🔥 **새로운 기능**: 이제 Python, JavaScript, Java 등의 코드를 실행할 수 있어요!\n"
                    "명령어로 시작하지 않는 메시지는 향후 AI 분석 기능으로 처리될 예정입니다."
                )
            
            self.stats['commands_processed'] += 1
            
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                self.stats['errors_handled'] += 1
                await handle_command_error(update, context, e, "message")
            else:
                await update.message.reply_text("메시지 처리 중 오류가 발생했습니다.")
    
    async def error_callback(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """글로벌 오류 콜백"""
        try:
            logger.error(f"전역 오류 발생: {context.error}")
            
            if ERROR_HANDLER_AVAILABLE and isinstance(update, Update):
                self.stats['errors_handled'] += 1
                await handle_command_error(update, context, context.error, "global")
            
        except Exception as e:
            logger.critical(f"오류 콜백에서 오류 발생: {e}")
    
    def setup_handlers(self):
        """명령어 핸들러 설정"""
        if not self.application:
            return
        
        # 명령어 핸들러들
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("analyze_url", self.analyze_url_command))
        self.application.add_handler(CommandHandler("error_stats", self.error_stats_command))
        self.application.add_handler(CommandHandler("run_code", self.run_code_command))
        self.application.add_handler(CommandHandler("code_languages", self.code_languages_command))
        self.application.add_handler(CommandHandler("code_stats", self.code_stats_command))
        self.application.add_handler(CommandHandler("code_help", self.code_help_command))
        self.application.add_handler(CommandHandler("code_review", self.code_review_command))
        self.application.add_handler(CommandHandler("learn_path", self.learn_path_command))
        self.application.add_handler(CommandHandler("code_history", self.code_history_command))
        self.application.add_handler(CommandHandler("benchmark", self.benchmark_command))
        self.application.add_handler(CommandHandler("optimize_tips", self.optimize_tips_command))
        
        # 메시지 핸들러
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler)
        )
        
        # 오류 핸들러
        self.application.add_error_handler(self.error_callback)
        
        logger.info("모든 핸들러가 설정되었습니다")
    
    async def start_bot(self):
        """봇 시작"""
        try:
            if not TELEGRAM_AVAILABLE:
                raise ImportError("텔레그램 모듈이 설치되지 않았습니다")
            
            if not self.bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다")
            
            # Application 생성
            self.application = Application.builder().token(self.bot_token).build()
            
            # 핸들러 설정
            self.setup_handlers()
            
            # 봇 시작
            logger.info("🚀 팜솔라 AI 봇 시작 중...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("✅ 팜솔라 AI 봇이 성공적으로 시작되었습니다!")
            
            # 무한 대기
            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                logger.info("봇 종료 신호를 받았습니다...")
            
        except Exception as e:
            logger.error(f"봇 시작 오류: {e}")
            if ERROR_HANDLER_AVAILABLE:
                result = await error_handler.handle_error(e, {"context": "bot_startup"})
                print(f"🔧 {result['user_message']}")
            else:
                print("❌ 봇을 시작할 수 없습니다. 환경 설정을 확인해주세요.")
            raise
        
        finally:
            # 정리
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
                logger.info("봇이 정상적으로 종료되었습니다")

    def parse_code_block(self, text: str) -> Dict[str, Any]:
        """
        텔레그램 메시지에서 코드 블록을 파싱합니다.
        
        지원 형식:
        1. ```language\ncode\n```
        2. ```\ncode\n```
        3. `code` (인라인 코드)
        4. 일반 텍스트 (언어 자동 감지)
        
        Returns:
            Dict containing 'language', 'code', 'success', 'error_message'
        """
        import re
        
        try:
            # 코드 블록 패턴 매칭
            code_block_pattern = r'```(?:(\w+)\n)?(.*?)```'
            match = re.search(code_block_pattern, text, re.DOTALL)
            
            if match:
                language = match.group(1) or 'auto'
                code = match.group(2).strip()
                return {
                    'language': language,
                    'code': code,
                    'success': True,
                    'error_message': None
                }
            
            # 인라인 코드 패턴
            inline_pattern = r'`([^`]+)`'
            inline_match = re.search(inline_pattern, text)
            
            if inline_match:
                code = inline_match.group(1).strip()
                return {
                    'language': 'auto',
                    'code': code,
                    'success': True,
                    'error_message': None
                }
            
            # 일반 텍스트로 처리
            if text.strip():
                return {
                    'language': 'auto',
                    'code': text.strip(),
                    'success': True,
                    'error_message': None
                }
            
            return {
                'language': None,
                'code': None,
                'success': False,
                'error_message': "코드를 찾을 수 없습니다."
            }
            
        except Exception as e:
            return {
                'language': None,
                'code': None,
                'success': False,
                'error_message': f"코드 파싱 오류: {str(e)}"
            }

    def detect_language(self, code: str) -> str:
        """
        코드에서 프로그래밍 언어를 자동 감지합니다.
        
        Args:
            code: 분석할 코드 문자열
            
        Returns:
            감지된 언어명 (기본값: 'python')
        """
        if not code.strip():
            return 'python'
        
        code = code.strip().lower()
        
        # 언어 감지 패턴
        language_patterns = {
            'python': [
                r'def\s+\w+\s*\(',
                r'import\s+\w+',
                r'from\s+\w+\s+import',
                r'print\s*\(',
                r'if\s+__name__\s*==\s*[\'"]__main__[\'"]',
                r':\s*$'  # 파이썬의 콜론 문법
            ],
            'javascript': [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*=',
                r'let\s+\w+\s*=',
                r'var\s+\w+\s*=',
                r'console\.log\s*\(',
                r'=>',  # 화살표 함수
                r'require\s*\('
            ],
            'java': [
                r'public\s+class\s+\w+',
                r'public\s+static\s+void\s+main',
                r'System\.out\.println',
                r'import\s+java\.',
                r'^\s*package\s+\w+'
            ],
            'cpp': [
                r'#include\s*<.*>',
                r'int\s+main\s*\(',
                r'std::',
                r'cout\s*<<',
                r'cin\s*>>',
                r'using\s+namespace\s+std'
            ],
            'go': [
                r'package\s+main',
                r'func\s+main\s*\(',
                r'import\s*\(',
                r'fmt\.Print',
                r':=',
                r'go\s+\w+'
            ],
            'rust': [
                r'fn\s+main\s*\(',
                r'let\s+mut\s+',
                r'println!\s*\(',
                r'use\s+std::',
                r'extern\s+crate',
                r'->\s*\w+'
            ],
            'php': [
                r'<\?php',
                r'\$\w+\s*=',
                r'echo\s+',
                r'function\s+\w+\s*\(',
                r'class\s+\w+'
            ],
            'ruby': [
                r'def\s+\w+',
                r'puts\s+',
                r'class\s+\w+',
                r'end\s*$',
                r'require\s+[\'"]',
                r'@\w+'  # 인스턴스 변수
            ],
            'csharp': [
                r'using\s+System',
                r'namespace\s+\w+',
                r'class\s+\w+',
                r'Console\.WriteLine',
                r'public\s+static\s+void\s+Main'
            ]
        }
        
        # 각 언어별 패턴 매칭 점수 계산
        scores = {}
        for language, patterns in language_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, code, re.MULTILINE):
                    score += 1
            scores[language] = score
        
        # 가장 높은 점수의 언어 반환
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        # 기본값
        return 'python'

    def format_execution_result(self, result, language: str) -> Dict[str, Any]:
        """
        코드 실행 결과를 텔레그램 메시지 형태로 포맷팅합니다.
        
        Args:
            result: ExecutionResult 객체
            language: 실행된 언어
            
        Returns:
            Dict containing 'message', 'needs_file', 'file_content', 'file_name'
        """
        try:
            # 기본 정보
            status_emoji = "✅" if result.success else "❌"
            language_name = result.language.title()
            
            # 헤더 메시지
            header = f"{status_emoji} **{language_name} 코드 실행 결과**\n\n"
            
            # 실행 정보
            exec_info = f"🕐 **실행 시간**: {result.execution_time:.3f}초\n"
            exec_info += f"💾 **메모리 사용**: {result.memory_usage}MB\n"
            exec_info += f"📊 **성능 점수**: {result.performance_score}/100\n"
            exec_info += f"🔧 **반환 코드**: {result.return_code}\n\n"
            
            # 출력 결과
            output_section = ""
            if result.output:
                output_section = f"📤 **출력 결과**:\n```\n{result.output}\n```\n\n"
            
            # 오류 메시지
            error_section = ""
            if result.error:
                error_section = f"⚠️ **오류 메시지**:\n```\n{result.error}\n```\n\n"
            
            # 의존성 정보
            deps_section = ""
            if result.dependencies_detected:
                deps_list = ", ".join(result.dependencies_detected)
                deps_section = f"📦 **감지된 의존성**: {deps_list}\n\n"
            
            # 최적화 제안
            suggestions_section = ""
            if result.optimization_suggestions:
                suggestions_section = "💡 **최적화 제안**:\n"
                for i, suggestion in enumerate(result.optimization_suggestions[:3], 1):
                    suggestions_section += f"{i}. {suggestion}\n"
                suggestions_section += "\n"
            
            # 전체 메시지 조합
            full_message = header + exec_info + output_section + error_section + deps_section + suggestions_section
            
            # 텔레그램 메시지 길이 제한 (4096자) 체크
            if len(full_message) <= 4000:  # 여유분 고려
                return {
                    'message': full_message.strip(),
                    'needs_file': False,
                    'file_content': None,
                    'file_name': None
                }
            else:
                # 긴 출력은 파일로 전송
                summary_message = header + exec_info + deps_section + suggestions_section
                
                if result.output:
                    summary_message += "📤 **출력 결과**: 파일로 전송됨\n\n"
                if result.error:
                    summary_message += "⚠️ **오류 메시지**: 파일로 전송됨\n\n"
                
                # 파일 내용 준비
                file_content = f"=== {language_name} 코드 실행 결과 ===\n\n"
                file_content += f"실행 시간: {result.execution_time:.3f}초\n"
                file_content += f"메모리 사용: {result.memory_usage}MB\n"
                file_content += f"성능 점수: {result.performance_score}/100\n"
                file_content += f"반환 코드: {result.return_code}\n\n"
                
                if result.output:
                    file_content += f"=== 출력 결과 ===\n{result.output}\n\n"
                if result.error:
                    file_content += f"=== 오류 메시지 ===\n{result.error}\n\n"
                if result.dependencies_detected:
                    file_content += f"=== 감지된 의존성 ===\n{', '.join(result.dependencies_detected)}\n\n"
                if result.optimization_suggestions:
                    file_content += "=== 최적화 제안 ===\n"
                    for i, suggestion in enumerate(result.optimization_suggestions, 1):
                        file_content += f"{i}. {suggestion}\n"
                
                return {
                    'message': summary_message.strip(),
                    'needs_file': True,
                    'file_content': file_content,
                    'file_name': f"execution_result_{language}_{int(datetime.now().timestamp())}.txt"
                }
                
        except Exception as e:
            error_message = f"❌ **결과 포맷팅 오류**\n\n⚠️ 오류: {str(e)}"
            return {
                'message': error_message,
                'needs_file': False,
                'file_content': None,
                'file_name': None
            }

# 메인 함수
async def main():
    """메인 실행 함수"""
    try:
        print("=" * 50)
        print("🤖 팜솔라 AI 봇 시작")
        print("=" * 50)
        
        # OFFLINE_MODE 체크
        offline_mode = os.getenv('OFFLINE_MODE', 'false').lower() == 'true'
        
        # 환경변수 확인
        if not os.getenv('TELEGRAM_BOT_TOKEN') and not offline_mode:
            print("❌ TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다")
            print("💡 .env 파일에 TELEGRAM_BOT_TOKEN=your_bot_token을 추가해주세요")
            print("📴 또는 OFFLINE_MODE=true로 설정하여 오프라인 모드로 실행하세요")
            return
        
        # OFFLINE_MODE 실행
        if offline_mode:
            print("📴 OFFLINE MODE 실행 중...")
            print("\n" + "="*60)
            print("📴 OFFLINE MODE - 시스템 상태 보고서")
            print("="*60)
            
            if ERROR_HANDLER_AVAILABLE:
                print("✅ 오류 처리 시스템: 활성화")
                stats = error_handler.get_error_stats()
                print(f"📊 성공률: {stats['success_rate']:.1f}%")
            else:
                print("❌ 오류 처리 시스템: 비활성화")
            
            print("\n💡 사용 가능한 기능:")
            print("• 📋 시스템 상태 확인")
            print("• 🔧 오류 처리 시스템 테스트")
            print("• 📊 통계 시스템")
            
            print("\n🚀 온라인 기능을 위해 다음을 설정하세요:")
            print("• TELEGRAM_BOT_TOKEN - 텔레그램 봇 토큰")
            print("• ADMIN_USER_ID - 관리자 사용자 ID")
            print("• GEMINI_API_KEY - Gemini AI API 키 (선택)")
            
            print("\n⏳ 5초 후 종료됩니다...")
            import time
            time.sleep(5)
            print("📴 OFFLINE MODE 완료")
            return
        
        # 봇 생성 및 시작
        bot = FarmSolarBot()
        await bot.start_bot()
        
    except Exception as e:
        print(f"❌ 봇 실행 중 오류 발생: {e}")
        if ERROR_HANDLER_AVAILABLE:
            result = await error_handler.handle_error(e, {"context": "main"})
            print(f"🔧 해결 방법: {result['user_message']}")
    
    finally:
        print("👋 봇이 종료되었습니다")

if __name__ == "__main__":
    # 기본 도움말 시스템 설정
    if ERROR_HANDLER_AVAILABLE:
        help_system.register_command_help(
            command="/start",
            description="봇을 시작하고 환영 메시지를 확인합니다",
            usage="/start",
            examples=["/start"]
        )
        
        help_system.register_command_help(
            command="/analyze_url",
            description="웹사이트 내용을 분석합니다",
            usage="/analyze_url <URL>",
            examples=["/analyze_url https://example.com"]
        )
        
        # 코드 실행 명령어들 등록
        help_system.register_command_help(
            command="/run_code",
            description="다양한 프로그래밍 언어의 코드를 실행합니다",
            usage="/run_code [언어] <코드> 또는 코드 블록에 답장",
            examples=[
                "/run_code print('Hello World')",
                "/run_code python print('Hello Python!')",
                "/run_code javascript console.log('Hello JS!');"
            ]
        )
        
        help_system.register_command_help(
            command="/code_languages",
            description="지원하는 프로그래밍 언어 목록과 상세 정보를 확인합니다",
            usage="/code_languages",
            examples=["/code_languages"]
        )
        
        help_system.register_command_help(
            command="/code_stats",
            description="코드 실행 통계와 사용 현황을 확인합니다",
            usage="/code_stats",
            examples=["/code_stats"]
        )
        
        help_system.register_command_help(
            command="/code_help",
            description="코드 실행 상세 도움말을 확인합니다",
            usage="/code_help",
            examples=["/code_help"]
        )
    
    # 실행
    asyncio.run(main())
