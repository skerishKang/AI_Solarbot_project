#!/usr/bin/env python3
"""
팜솔라 AI_Solarbot 사용자 친화적 오류 처리 시스템
중앙화된 오류 처리, 친화적 메시지, 단계별 해결 가이드 제공
"""

import logging
import asyncio
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    """오류 카테고리"""
    AUTHENTICATION = "auth"
    NETWORK = "network"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    API = "api"
    FILE_SYSTEM = "file_system"
    PARSING = "parsing"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"

class ErrorSeverity(Enum):
    """오류 심각도"""
    LOW = "low"         # 사용자에게 알리지만 계속 진행
    MEDIUM = "medium"   # 사용자에게 알리고 대안 제시
    HIGH = "high"       # 사용자에게 알리고 작업 중단
    CRITICAL = "critical" # 관리자에게 알림

@dataclass
class ErrorInfo:
    """오류 정보 구조체"""
    category: ErrorCategory
    severity: ErrorSeverity
    user_message: str
    technical_message: str
    solution_steps: List[str]
    retry_possible: bool = False
    max_retries: int = 0
    retry_delay: float = 1.0
    escalate_to_admin: bool = False

class UserFriendlyErrorHandler:
    """사용자 친화적 오류 처리기"""
    
    def __init__(self):
        """초기화"""
        self.error_patterns = self._initialize_error_patterns()
        self.retry_counts = {}  # 오류별 재시도 횟수 추적
        self.error_stats = {
            'total_errors': 0,
            'resolved_errors': 0,
            'user_resolved_errors': 0,
            'admin_escalated_errors': 0,
            'auto_retried_errors': 0
        }
        
        # 관리자 알림 콜백
        self.admin_notify_callback: Optional[Callable] = None
        
        logger.info("사용자 친화적 오류 처리기 초기화 완료")
    
    def _initialize_error_patterns(self) -> Dict[str, ErrorInfo]:
        """오류 패턴 및 처리 정보 초기화"""
        return {
            # 의존성 관련 오류
            "module_not_found": ErrorInfo(
                category=ErrorCategory.DEPENDENCY,
                severity=ErrorSeverity.HIGH,
                user_message="📦 필요한 모듈이 설치되지 않았습니다",
                technical_message="Required Python module not found",
                solution_steps=[
                    "1️⃣ 잠시만 기다려주세요. 자동으로 필요한 모듈을 설치합니다",
                    "2️⃣ 설치 중에는 다른 작업을 하지 마세요",
                    "3️⃣ 설치 완료 후 다시 시도해주세요"
                ],
                retry_possible=True,
                max_retries=1,
                retry_delay=5.0
            ),
            
            # 인증 관련 오류
            "invalid_token": ErrorInfo(
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                user_message="🔐 봇 인증에 문제가 있습니다",
                technical_message="Telegram bot token is invalid or expired",
                solution_steps=[
                    "1️⃣ 환경변수에서 TELEGRAM_BOT_TOKEN을 확인해주세요",
                    "2️⃣ BotFather에서 새 토큰을 발급받아 교체해주세요",
                    "3️⃣ .env 파일을 다시 저장하고 봇을 재시작해주세요"
                ],
                retry_possible=False,
                escalate_to_admin=True
            ),
            
            "unauthorized": ErrorInfo(
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.MEDIUM,
                user_message="❌ 이 명령어를 사용할 권한이 없습니다",
                technical_message="User not authorized for this command",
                solution_steps=[
                    "1️⃣ 관리자 권한이 필요한 명령어입니다",
                    "2️⃣ 관리자에게 권한 요청을 해주세요",
                    "3️⃣ 일반 사용자 명령어를 사용해주세요"
                ],
                retry_possible=False
            ),
            
            # 네트워크 관련 오류
            "network_timeout": ErrorInfo(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                user_message="🌐 네트워크 연결이 불안정합니다",
                technical_message="Network request timed out",
                solution_steps=[
                    "1️⃣ 잠시 후 다시 시도해주세요",
                    "2️⃣ 인터넷 연결 상태를 확인해주세요",
                    "3️⃣ URL이 올바른지 확인해주세요"
                ],
                retry_possible=True,
                max_retries=3,
                retry_delay=2.0
            ),
            
            # 사용자 입력 오류
            "invalid_url": ErrorInfo(
                category=ErrorCategory.USER_INPUT,
                severity=ErrorSeverity.LOW,
                user_message="🔗 올바르지 않은 URL입니다",
                technical_message="URL format validation failed",
                solution_steps=[
                    "1️⃣ URL이 http:// 또는 https://로 시작하는지 확인해주세요",
                    "2️⃣ 웹사이트 주소를 다시 확인해주세요",
                    "3️⃣ 예시: https://example.com"
                ],
                retry_possible=False
            ),
            
            "missing_parameters": ErrorInfo(
                category=ErrorCategory.USER_INPUT,
                severity=ErrorSeverity.LOW,
                user_message="📝 필수 입력값이 없습니다",
                technical_message="Required parameters missing",
                solution_steps=[
                    "1️⃣ 명령어 사용법을 확인해주세요",
                    "2️⃣ /help 명령어로 도움말을 확인하세요",
                    "3️⃣ 모든 필수 값을 입력했는지 확인해주세요"
                ],
                retry_possible=False
            ),
            
            # 기본 오류
            "unknown_error": ErrorInfo(
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                user_message="❓ 예상치 못한 오류가 발생했습니다",
                technical_message="Unknown error occurred",
                solution_steps=[
                    "1️⃣ 잠시 후 다시 시도해주세요",
                    "2️⃣ 동일한 문제가 계속되면 관리자에게 알려주세요",
                    "3️⃣ 다른 명령어나 기능을 사용해보세요"
                ],
                retry_possible=True,
                max_retries=1,
                retry_delay=1.0,
                escalate_to_admin=True
            )
        }
    
    def classify_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """오류 분류 및 패턴 매칭"""
        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 구체적인 오류 패턴 매칭
        if "no module named" in error_msg or "modulenotfounderror" in error_type:
            return "module_not_found"
        elif "invalid token" in error_msg or "unauthorized" in error_msg:
            return "invalid_token"
        elif "forbidden" in error_msg and context and context.get("command_type") == "admin":
            return "unauthorized"
        elif "timeout" in error_msg or "timed out" in error_msg:
            return "network_timeout"
        elif "invalid url" in error_msg or "url" in error_msg:
            return "invalid_url"
        elif "missing" in error_msg and "parameter" in error_msg:
            return "missing_parameters"
        else:
            return "unknown_error"
    
    async def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """중앙화된 오류 처리"""
        try:
            # 통계 업데이트
            self.error_stats['total_errors'] += 1
            
            # 오류 분류
            error_key = self.classify_error(error, context)
            error_info = self.error_patterns.get(error_key, self.error_patterns["unknown_error"])
            
            # 로깅
            logger.error(f"오류 발생 [{error_key}]: {error_info.technical_message} - {str(error)}")
            
            # 특별 처리: 모듈 없음 오류
            if error_key == "module_not_found":
                module_name = self._extract_module_name(str(error))
                if module_name:
                    await self._handle_missing_module(module_name)
            
            # 사용자 친화적 응답 생성
            user_response = self._generate_user_response(error_info, error_key == "module_not_found")
            
            return {
                'success': False,
                'error_category': error_info.category.value,
                'severity': error_info.severity.value,
                'user_message': user_response,
                'technical_message': error_info.technical_message,
                'escalated': error_info.escalate_to_admin
            }
            
        except Exception as handling_error:
            logger.critical(f"오류 처리 중 오류 발생: {handling_error}")
            return {
                'success': False,
                'error_category': 'system',
                'severity': 'critical',
                'user_message': "😵 시스템에 심각한 문제가 발생했습니다. 관리자에게 즉시 알려주세요.",
                'technical_message': f"Error handler failed: {str(handling_error)}",
                'escalated': True
            }
    
    def _extract_module_name(self, error_msg: str) -> Optional[str]:
        """오류 메시지에서 모듈명 추출"""
        try:
            if "No module named" in error_msg:
                # "No module named 'selenium'" -> "selenium"
                start = error_msg.find("'") + 1
                end = error_msg.find("'", start)
                if start > 0 and end > start:
                    return error_msg[start:end]
        except:
            pass
        return None
    
    async def _handle_missing_module(self, module_name: str):
        """누락된 모듈 자동 설치"""
        try:
            import subprocess
            import sys
            
            # 모듈별 설치 매핑
            install_map = {
                'selenium': 'selenium',
                'telegram': 'python-telegram-bot',
                'google': 'google-api-python-client google-auth google-auth-oauthlib',
                'openai': 'openai',
                'dotenv': 'python-dotenv'
            }
            
            package_to_install = install_map.get(module_name, module_name)
            
            logger.info(f"모듈 자동 설치 시작: {package_to_install}")
            
            # pip install 실행
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_to_install],
                capture_output=True,
                text=True,
                timeout=300  # 5분 타임아웃
            )
            
            if result.returncode == 0:
                logger.info(f"모듈 설치 성공: {package_to_install}")
                self.error_stats['resolved_errors'] += 1
            else:
                logger.error(f"모듈 설치 실패: {result.stderr}")
                
        except Exception as e:
            logger.error(f"모듈 자동 설치 오류: {e}")
    
    def _generate_user_response(self, error_info: ErrorInfo, is_auto_fixing: bool = False) -> str:
        """사용자 친화적 응답 메시지 생성"""
        # 기본 메시지
        response = f"{error_info.user_message}\n\n"
        
        # 자동 수정 중인 경우
        if is_auto_fixing:
            response += "🔧 **자동 수정 중**: 필요한 모듈을 설치하고 있습니다...\n"
            response += "⏳ 잠시만 기다려주세요 (최대 5분 소요)\n\n"
        
        # 해결 방법
        response += "🔧 **해결 방법:**\n"
        for step in error_info.solution_steps:
            response += f"{step}\n"
        
        # 심각도별 추가 안내
        if error_info.severity == ErrorSeverity.HIGH:
            response += "\n⚠️ **주의**: 이 문제는 즉시 해결이 필요합니다."
        elif error_info.severity == ErrorSeverity.CRITICAL:
            response += "\n🚨 **긴급**: 관리자에게 즉시 알림이 전송되었습니다."
        
        # 도움말 링크
        response += "\n\n💡 **추가 도움이 필요하시면**:"
        response += "\n• `/help` - 전체 도움말"
        response += "\n• `/status` - 시스템 상태 확인"
        response += "\n• 관리자에게 직접 문의"
        
        return response
    
    def get_error_stats(self) -> Dict[str, Any]:
        """오류 통계 반환"""
        stats = self.error_stats.copy()
        stats['success_rate'] = (
            (stats['resolved_errors'] / stats['total_errors'] * 100) 
            if stats['total_errors'] > 0 else 100.0
        )
        return stats

# 전역 오류 처리기 인스턴스
error_handler = UserFriendlyErrorHandler()

async def handle_command_error(update, context, error: Exception, command_name: str = "unknown"):
    """텔레그램 명령어 오류 처리 헬퍼"""
    error_context = {
        'command_name': command_name,
        'user_id': update.effective_user.id if update.effective_user else None,
        'chat_id': update.effective_chat.id if update.effective_chat else None,
        'message_text': update.message.text if update.message else None
    }
    
    result = await error_handler.handle_error(error, error_context)
    
    # 사용자에게 친화적 메시지 전송
    try:
        if update.message:
            await update.message.reply_text(
                result['user_message'],
                parse_mode='Markdown'
            )
    except Exception as send_error:
        logger.error(f"오류 메시지 전송 실패: {send_error}")
        # 최후 수단: 간단한 메시지
        try:
            await update.message.reply_text(
                "죄송합니다. 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
            )
        except:
            pass
    
    return result

class HelpSystem:
    """도움말 시스템"""
    
    def __init__(self):
        self.command_help = {}
        self.faq = {}
    
    def register_command_help(self, command: str, description: str, usage: str, examples: List[str]):
        """명령어 도움말 등록"""
        self.command_help[command] = {
            'description': description,
            'usage': usage,
            'examples': examples
        }
    
    def get_general_help(self) -> str:
        """전체 도움말 반환"""
        response = "🤖 **팜솔라 AI 봇 도움말**\n\n"
        response += "📋 **사용 가능한 명령어**:\n\n"
        
        for command, info in self.command_help.items():
            response += f"• `{command}` - {info['description']}\n"
        
        response += "\n💡 **사용 팁**:\n"
        response += "• 오류가 발생하면 친화적인 해결 방법을 제시합니다\n"
        response += "• 필요한 모듈이 없으면 자동으로 설치합니다\n"
        response += "• 관리자 명령어는 권한이 있는 사용자만 사용할 수 있습니다\n"
        
        return response

# 전역 도움말 시스템
help_system = HelpSystem() 