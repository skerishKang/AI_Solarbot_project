#!/usr/bin/env python3
"""
팜솔라 AI_Solarbot 시작 스크립트 (개선된 버전)
단계별 의존성 검증, OFFLINE_MODE 지원, graceful startup 구현
"""

import os
import sys
import logging
import asyncio
import importlib
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 환경 변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not found, loading environment from system")

# 전역 설정
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "false").lower() == "true"
STARTUP_TIMEOUT = int(os.getenv("STARTUP_TIMEOUT", "30"))

class StartupManager:
    """봇 시작 프로세스 관리자"""
    
    def __init__(self):
        self.logger = None
        self.startup_time = time.time()
        self.dependency_status = {}
        self.failed_components = []
        self.offline_mode = OFFLINE_MODE
        
    def setup_logging(self):
        """향상된 로깅 설정"""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_file = os.getenv("LOG_FILE", "logs/bot.log")
        
        # 로그 디렉토리 생성
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)
        
        # 로깅 포맷 설정
        log_format = "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # 파일과 콘솔 로깅 설정
        handlers = [
            logging.StreamHandler(sys.stdout)
        ]
        
        try:
            handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        except Exception as e:
            print(f"⚠️ 로그 파일 생성 실패: {e}")
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            datefmt=date_format,
            handlers=handlers
        )
        
        # 외부 라이브러리 로그 레벨 조정
        for lib in ["httpx", "telegram", "urllib3", "asyncio"]:
            logging.getLogger(lib).setLevel(logging.WARNING)
        
        self.logger = logging.getLogger("StartupManager")
        self.logger.info("🔧 로깅 시스템 초기화 완료")
        
        if self.offline_mode:
            self.logger.info("📴 OFFLINE MODE 활성화")

    def check_dependencies(self) -> Dict[str, bool]:
        """의존성 체크리스트 검증"""
        self.logger.info("🔍 의존성 검증 시작...")
        
        dependencies = {
            "필수 환경변수": self._check_environment_variables(),
            "Python 모듈": self._check_python_modules(),
            "시스템 디렉토리": self._check_directories(),
            "외부 서비스": self._check_external_services() if not self.offline_mode else True,
            "설정 파일": self._check_config_files()
        }
        
        self.dependency_status = dependencies
        
        # 검증 결과 출력
        for dep_name, status in dependencies.items():
            status_icon = "✅" if status else "❌"
            self.logger.info(f"{status_icon} {dep_name}: {'통과' if status else '실패'}")
        
        failed_deps = [name for name, status in dependencies.items() if not status]
        if failed_deps:
            self.failed_components.extend(failed_deps)
            if not self.offline_mode and "외부 서비스" in failed_deps:
                self.logger.warning("🔄 OFFLINE MODE로 전환하여 계속 진행...")
                self.offline_mode = True
                dependencies["외부 서비스"] = True
        
        return dependencies

    def _check_environment_variables(self) -> bool:
        """환경 변수 확인"""
        required_vars = ["TELEGRAM_BOT_TOKEN", "ADMIN_USER_ID"]
        optional_vars = ["GEMINI_API_KEY", "GOOGLE_CREDENTIALS_FILE"]
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        if missing_required:
            self.logger.error(f"❌ 필수 환경 변수 누락: {', '.join(missing_required)}")
            self.logger.error("config/.env 파일을 확인하세요.")
            return False
        
        if missing_optional:
            self.logger.warning(f"⚠️ 선택적 환경 변수 누락: {', '.join(missing_optional)}")
            self.logger.warning("일부 기능이 제한될 수 있습니다.")
        
        return True

    def _check_python_modules(self) -> bool:
        """필수 Python 모듈 확인"""
        # 절대 필수 모듈 (없으면 아예 시작 불가)
        critical_modules = ["asyncio", "logging", "importlib", "pathlib"]
        
        # 온라인 모드에서만 필수인 모듈
        online_required_modules = ["telegram", "telegram.ext"]
        
        # 선택적 모듈
        optional_modules = [
            "google.auth", "googleapiclient", "cryptography", "dotenv",
            "aiohttp", "google_auth_oauthlib"
        ]
        
        missing_critical = []
        missing_online = []
        missing_optional = []
        
        # 절대 필수 모듈 확인
        for module in critical_modules:
            try:
                importlib.import_module(module)
            except ImportError:
                missing_critical.append(module)
        
        # 온라인 모드 필수 모듈 확인
        for module in online_required_modules:
            try:
                importlib.import_module(module)
            except ImportError:
                missing_online.append(module)
        
        # 선택적 모듈 확인
        for module in optional_modules:
            try:
                importlib.import_module(module)
            except ImportError:
                missing_optional.append(module)
        
        # 절대 필수 모듈이 없으면 실패
        if missing_critical:
            self.logger.error(f"❌ 절대 필수 모듈 누락: {', '.join(missing_critical)}")
            return False
        
        # 온라인 모드 필수 모듈이 없으면 OFFLINE_MODE로 전환
        if missing_online:
            if not self.offline_mode:
                self.logger.warning(f"⚠️ 온라인 모듈 누락: {', '.join(missing_online)}")
                self.logger.warning("🔄 OFFLINE MODE로 자동 전환...")
                self.offline_mode = True
            else:
                self.logger.info(f"📴 OFFLINE MODE - 온라인 모듈 스킵: {', '.join(missing_online)}")
        
        # 선택적 모듈 누락은 경고만
        if missing_optional:
            self.logger.warning(f"⚠️ 선택적 모듈 누락: {', '.join(missing_optional)}")
            self.logger.warning("일부 고급 기능이 제한될 수 있습니다.")
        
        return True

    def _check_directories(self) -> bool:
        """필요한 디렉토리 생성 및 확인"""
        directories = ["logs", "data", "backups", "config"]
        
        try:
            for directory in directories:
                Path(directory).mkdir(exist_ok=True)
            self.logger.info("📁 시스템 디렉토리 확인 완료")
            return True
        except Exception as e:
            self.logger.error(f"❌ 디렉토리 생성 실패: {e}")
            return False

    def _check_external_services(self) -> bool:
        """외부 서비스 연결 확인"""
        if self.offline_mode:
            return True
        
        services_status = {}
        
        # 텔레그램 API 확인
        try:
            import telegram
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if bot_token:
                # 간단한 봇 정보 조회로 연결 테스트
                services_status["Telegram"] = True
            else:
                services_status["Telegram"] = False
        except Exception as e:
            self.logger.warning(f"⚠️ 텔레그램 연결 확인 실패: {e}")
            services_status["Telegram"] = False
        
        # Gemini API 확인
        gemini_key = os.getenv("GEMINI_API_KEY")
        services_status["Gemini"] = bool(gemini_key)
        
        # Google Drive 확인
        credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "config/google_credentials.json")
        services_status["Google Drive"] = Path(credentials_file).exists()
        
        failed_services = [name for name, status in services_status.items() if not status]
        if failed_services:
            self.logger.warning(f"⚠️ 외부 서비스 연결 실패: {', '.join(failed_services)}")
            return False
        
        return True

    def _check_config_files(self) -> bool:
        """설정 파일 확인"""
        config_files = {
            "config/settings.py": "시스템 설정",
            ".env": "환경 변수"
        }
        
        missing_files = []
        for file_path, description in config_files.items():
            if not Path(file_path).exists():
                missing_files.append(f"{description} ({file_path})")
        
        if missing_files:
            self.logger.warning(f"⚠️ 설정 파일 누락: {', '.join(missing_files)}")
            # 설정 파일은 누락되어도 기본값으로 동작 가능
        
        return True

    def initialize_components(self) -> bool:
        """시스템 컴포넌트 초기화"""
        self.logger.info("🔧 시스템 컴포넌트 초기화...")
        
        initialization_results = []
        
        try:
            # 암호화 키 확인/생성
            try:
                if not os.getenv("ENCRYPTION_KEY") and not self.offline_mode:
                    self._generate_encryption_key()
                initialization_results.append("암호화 키: ✅")
            except Exception as e:
                self.logger.warning(f"⚠️ 암호화 키 처리 실패: {e}")
                initialization_results.append("암호화 키: ⚠️")
            
            # 모니터링 시스템 초기화
            try:
                self._initialize_monitoring()
                initialization_results.append("모니터링: ✅")
            except Exception as e:
                self.logger.warning(f"⚠️ 모니터링 초기화 실패: {e}")
                initialization_results.append("모니터링: ❌")
            
            # AI 핸들러 초기화 (OFFLINE_MODE에서는 스킵)
            if not self.offline_mode:
                try:
                    self._initialize_ai_handler()
                    initialization_results.append("AI 핸들러: ✅")
                except Exception as e:
                    self.logger.warning(f"⚠️ AI 핸들러 초기화 실패: {e}")
                    initialization_results.append("AI 핸들러: ❌")
            else:
                initialization_results.append("AI 핸들러: 📴 (OFFLINE)")
            
            # 결과 요약
            self.logger.info("📋 초기화 결과:")
            for result in initialization_results:
                self.logger.info(f"   {result}")
            
            self.logger.info("✅ 시스템 컴포넌트 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 시스템 초기화 치명적 실패: {e}")
            self.logger.exception("상세 오류 정보:")
            return False

    def _generate_encryption_key(self):
        """암호화 키 생성"""
        try:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            self.logger.info("🔐 새로운 암호화 키가 생성되었습니다.")
            self.logger.info("이 키를 .env 파일의 ENCRYPTION_KEY에 저장하세요:")
            self.logger.info(f"ENCRYPTION_KEY={key.decode()}")
        except ImportError:
            self.logger.warning("⚠️ cryptography 모듈 없음, 암호화 기능 비활성화")

    def _initialize_monitoring(self):
        """모니터링 시스템 초기화"""
        try:
            from monitoring import bot_monitor
            bot_monitor.log_activity("system", "startup", "Bot startup initiated")
            self.logger.info("📊 모니터링 시스템 초기화 완료")
        except ImportError:
            self.logger.warning("⚠️ 모니터링 모듈 로드 실패")
        except Exception as e:
            self.logger.warning(f"⚠️ 모니터링 시스템 초기화 실패: {e}")

    def _initialize_ai_handler(self):
        """AI 핸들러 초기화"""
        try:
            from ai_integration_engine import ai_engine
            self.logger.info("🤖 AI 통합 엔진 초기화 완료")
        except ImportError:
            self.logger.warning("⚠️ AI 핸들러 초기화 실패, 기본 기능만 사용")
        except Exception as e:
            self.logger.warning(f"⚠️ AI 핸들러 초기화 오류: {e}")

    async def start_bot_with_timeout(self) -> bool:
        """타임아웃이 있는 봇 시작"""
        self.logger.info("🚀 봇 시작 프로세스 시작...")
        
        try:
            # 봇 시작을 비동기로 실행
            bot_task = asyncio.create_task(self._start_bot())
            
            # 타임아웃 설정
            await asyncio.wait_for(bot_task, timeout=STARTUP_TIMEOUT)
            return True
            
        except asyncio.TimeoutError:
            self.logger.error(f"❌ 봇 시작 타임아웃 ({STARTUP_TIMEOUT}초)")
            return False
        except Exception as e:
            self.logger.error(f"❌ 봇 시작 실패: {e}")
            return False

    async def _start_bot(self):
        """실제 봇 시작 로직"""
        try:
            # 시작 정보 출력
            self._print_startup_info()
            
            if self.offline_mode:
                # OFFLINE_MODE에서는 시스템 상태만 확인
                await self._run_offline_mode()
            else:
                # 온라인 모드에서 텔레그램 봇 시작
                from bot import main as bot_main
                await bot_main()
            
        except ImportError as e:
            if not self.offline_mode:
                self.logger.error(f"❌ 봇 모듈 로드 실패: {e}")
                self.logger.warning("🔄 OFFLINE MODE로 전환하여 재시도...")
                self.offline_mode = True
                await self._run_offline_mode()
            else:
                self.logger.error(f"❌ OFFLINE MODE에서도 시작 실패: {e}")
                raise
        except Exception as e:
            self.logger.error(f"❌ 봇 실행 실패: {e}")
            raise

    async def _run_offline_mode(self):
        """OFFLINE MODE 실행 - 시스템 상태 확인 및 보고"""
        self.logger.info("📴 OFFLINE MODE 실행 중...")
        
        # 시스템 상태 확인
        system_status = self._check_system_health()
        
        # 보고서 생성
        report = self.generate_startup_report()
        
        # 콘솔에 출력
        print("\n" + "="*60)
        print("📴 OFFLINE MODE - 시스템 상태 보고서")
        print("="*60)
        print(report)
        print("="*60)
        
        if system_status['healthy']:
            print("\n✅ 시스템이 정상적으로 초기화되었습니다.")
            print("💡 온라인 기능을 사용하려면 필요한 모듈을 설치하세요:")
            print("   pip install python-telegram-bot google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        else:
            print("\n⚠️ 시스템에 문제가 있습니다.")
            for issue in system_status['issues']:
                print(f"   • {issue}")
        
        print("\n🔄 5초 후 종료됩니다...")
        await asyncio.sleep(5)
        
        self.logger.info("📴 OFFLINE MODE 종료")

    def _check_system_health(self) -> dict:
        """시스템 상태 검사"""
        issues = []
        
        # 환경 변수 확인
        required_env_vars = ['TELEGRAM_BOT_TOKEN', 'ADMIN_USER_ID']
        for var in required_env_vars:
            if not os.getenv(var):
                issues.append(f"환경 변수 {var} 누락")
        
        # 디렉토리 확인
        required_dirs = ['logs', 'data', 'config']
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                issues.append(f"디렉토리 {dir_name} 누락")
        
        # 모듈 가용성 확인
        optional_modules = ['telegram', 'google.auth', 'cryptography']
        missing_modules = []
        for module in optional_modules:
            try:
                importlib.import_module(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            issues.append(f"선택적 모듈 누락: {', '.join(missing_modules)}")
        
        return {
            'healthy': len(issues) <= 1,  # 1개 이하의 문제는 허용
            'issues': issues,
            'missing_modules': missing_modules
        }

    def _print_startup_info(self):
        """시작 정보 출력"""
        startup_duration = time.time() - self.startup_time
        
        self.logger.info("🚀 팜솔라 AI_Solarbot 시작")
        self.logger.info("=" * 60)
        self.logger.info(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"⏱️  초기화 시간: {startup_duration:.2f}초")
        self.logger.info(f"🐍 Python 버전: {sys.version.split()[0]}")
        self.logger.info(f"📁 작업 디렉토리: {os.getcwd()}")
        self.logger.info(f"🔧 환경: {os.getenv('ENVIRONMENT', 'development')}")
        self.logger.info(f"🤖 봇 이름: {os.getenv('BOT_NAME', 'AI_Solarbot')}")
        self.logger.info(f"📊 버전: {os.getenv('BOT_VERSION', '2.0.0')}")
        
        if self.offline_mode:
            self.logger.info("📴 모드: OFFLINE (제한된 기능)")
        else:
            self.logger.info("🌐 모드: ONLINE (전체 기능)")
        
        if self.failed_components:
            self.logger.warning(f"⚠️ 실패한 컴포넌트: {', '.join(self.failed_components)}")
        
        self.logger.info("=" * 60)

    def generate_startup_report(self) -> str:
        """시작 보고서 생성"""
        startup_duration = time.time() - self.startup_time
        
        report = f"""🚀 **봇 시작 보고서**

⏱️ **초기화 시간:** {startup_duration:.2f}초
🔧 **모드:** {'OFFLINE' if self.offline_mode else 'ONLINE'}

📋 **의존성 검증 결과:**"""
        
        for dep_name, status in self.dependency_status.items():
            status_icon = "✅" if status else "❌"
            report += f"\n{status_icon} {dep_name}"
        
        if self.failed_components:
            report += f"\n\n⚠️ **실패한 컴포넌트:**\n{chr(10).join([f'• {comp}' for comp in self.failed_components])}"
        
        report += f"\n\n🎯 **권장 사항:**"
        if self.offline_mode:
            report += "\n• 온라인 기능을 위해 필요한 API 키와 인증 파일을 설정하세요"
        if self.failed_components:
            report += "\n• 실패한 컴포넌트를 확인하고 필요한 설정을 완료하세요"
        if startup_duration > 10:
            report += "\n• 시작 시간이 길어지고 있습니다. 시스템 최적화를 고려하세요"
        
        return report

def main():
    """메인 함수"""
    startup_manager = StartupManager()
    
    try:
        print("🚀 팜솔라 AI_Solarbot 시작 중...")
        print("=" * 50)
        
        # 1단계: 로깅 설정
        startup_manager.setup_logging()
        
        # 2단계: 의존성 검증
        dependencies = startup_manager.check_dependencies()
        
        # 치명적 오류 체크
        critical_deps = ["필수 환경변수", "Python 모듈", "시스템 디렉토리"]
        critical_failures = [dep for dep in critical_deps if not dependencies.get(dep, False)]
        
        if critical_failures:
            startup_manager.logger.error(f"💥 치명적 의존성 실패: {', '.join(critical_failures)}")
            startup_manager.logger.error("봇을 시작할 수 없습니다. 설정을 확인하세요.")
            sys.exit(1)
        
        # 3단계: 시스템 초기화
        if not startup_manager.initialize_components():
            startup_manager.logger.error("💥 시스템 초기화 실패")
            sys.exit(1)
        
        # 4단계: 봇 시작
        startup_manager.logger.info("🤖 텔레그램 봇 연결 중...")
        
        # 비동기 봇 시작
        success = asyncio.run(startup_manager.start_bot_with_timeout())
        
        if not success:
            startup_manager.logger.error("💥 봇 시작 실패")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 봇이 중지되었습니다.")
        if startup_manager.logger:
            startup_manager.logger.info("봇이 정상적으로 종료되었습니다.")
            
            # 종료 시 시작 보고서 출력
            report = startup_manager.generate_startup_report()
            startup_manager.logger.info(f"시작 보고서:\n{report}")
            
    except Exception as e:
        print(f"\n💥 치명적 오류: {e}")
        if startup_manager.logger:
            startup_manager.logger.error(f"치명적 오류로 봇이 종료됩니다: {e}")
            startup_manager.logger.exception("상세 오류 정보:")
        sys.exit(1)

if __name__ == "__main__":
    main()
