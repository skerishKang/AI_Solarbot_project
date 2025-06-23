#!/usr/bin/env python3
"""
팜솔라 AI_Solarbot 배포 자동화 스크립트
실제 강의 환경에서의 원클릭 배포를 지원합니다.
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

class DeploymentManager:
    """배포 관리자"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"
        self.backup_dir = self.project_root / "backups"
        
        # 배포 환경 설정
        self.environments = {
            "development": {
                "name": "개발 환경",
                "host": "localhost",
                "port": 8000,
                "debug": True
            },
            "staging": {
                "name": "스테이징 환경", 
                "host": "staging.farmsolar.co.kr",
                "port": 443,
                "debug": False
            },
            "production": {
                "name": "운영 환경",
                "host": "bot.farmsolar.co.kr", 
                "port": 443,
                "debug": False
            }
        }
    
    def check_prerequisites(self):
        """배포 전 필수 조건 확인"""
        print("🔍 배포 전 필수 조건 확인 중...")
        
        errors = []
        
        # Python 버전 확인
        if sys.version_info < (3, 8):
            errors.append("Python 3.8 이상이 필요합니다.")
        
        # 필수 파일 확인
        required_files = [
            "requirements.txt",
            "src/bot.py",
            "config/.env.example"
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                errors.append(f"필수 파일이 없습니다: {file_path}")
        
        # 환경 변수 확인
        env_file = self.config_dir / ".env"
        if not env_file.exists():
            errors.append(".env 파일이 없습니다. .env.example을 복사하여 설정하세요.")
        
        return errors
    
    def setup_environment(self):
        """환경 설정"""
        print("⚙️ 환경 설정 중...")
        
        # 필요한 디렉토리 생성
        for directory in [self.logs_dir, self.backup_dir]:
            directory.mkdir(exist_ok=True)
            print(f"  ✅ 디렉토리 생성: {directory}")
        
        # .env 파일 확인 및 생성
        env_file = self.config_dir / ".env"
        env_example = self.config_dir / ".env.example"
        
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)
            print(f"  ✅ .env 파일 생성됨. 설정을 확인하세요: {env_file}")
            return False  # 사용자가 설정을 완료해야 함
        
        return True
    
    def install_dependencies(self):
        """의존성 패키지 설치"""
        print("📦 의존성 패키지 설치 중...")
        
        try:
            # pip 업그레이드
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # requirements.txt 설치
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True)
            
            print("  ✅ 모든 의존성 패키지가 설치되었습니다.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ 패키지 설치 실패: {e}")
            return False
    
    def run_tests(self):
        """테스트 실행"""
        print("🧪 통합 테스트 실행 중...")
        
        test_file = self.project_root / "test" / "integration_test.py"
        if not test_file.exists():
            print("  ⚠️ 테스트 파일이 없습니다. 테스트를 건너뜁니다.")
            return True
        
        try:
            result = subprocess.run(
                [sys.executable, str(test_file)], 
                capture_output=True, 
                text=True,
                timeout=300  # 5분 타임아웃
            )
            
            if result.returncode == 0:
                print("  ✅ 모든 테스트가 통과했습니다.")
                return True
            else:
                print(f"  ❌ 테스트 실패:\n{result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ❌ 테스트 타임아웃 (5분 초과)")
            return False
        except Exception as e:
            print(f"  ❌ 테스트 실행 오류: {e}")
            return False
    
    def backup_current_deployment(self):
        """현재 배포 백업"""
        print("💾 현재 배포 백업 중...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            # 중요 파일들만 백업
            backup_files = [
                "src/",
                "config/",
                "data/",
                "requirements.txt"
            ]
            
            backup_path.mkdir(exist_ok=True)
            
            for item in backup_files:
                source = self.project_root / item
                if source.exists():
                    if source.is_dir():
                        shutil.copytree(source, backup_path / item, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, backup_path / item)
            
            print(f"  ✅ 백업 완료: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"  ❌ 백업 실패: {e}")
            return None
    
    def deploy_to_environment(self, env_name):
        """특정 환경에 배포"""
        if env_name not in self.environments:
            print(f"❌ 알 수 없는 환경: {env_name}")
            return False
        
        env_config = self.environments[env_name]
        print(f"🚀 {env_config['name']}에 배포 중...")
        
        # 환경별 설정 적용
        if env_name == "production":
            return self._deploy_production()
        elif env_name == "staging":
            return self._deploy_staging()
        else:
            return self._deploy_development()
    
    def _deploy_development(self):
        """개발 환경 배포"""
        print("  🔧 개발 환경 설정 적용 중...")
        
        # 개발 모드 설정
        os.environ["DEBUG"] = "True"
        os.environ["LOG_LEVEL"] = "DEBUG"
        
        # 봇 시작
        return self._start_bot()
    
    def _deploy_staging(self):
        """스테이징 환경 배포"""
        print("  🔧 스테이징 환경 설정 적용 중...")
        
        # 스테이징 모드 설정
        os.environ["DEBUG"] = "False"
        os.environ["LOG_LEVEL"] = "INFO"
        
        return self._start_bot()
    
    def _deploy_production(self):
        """운영 환경 배포"""
        print("  🔧 운영 환경 설정 적용 중...")
        
        # 운영 모드 설정
        os.environ["DEBUG"] = "False"
        os.environ["LOG_LEVEL"] = "WARNING"
        
        # 추가 보안 설정
        os.environ["SECURE_MODE"] = "True"
        
        return self._start_bot()
    
    def _start_bot(self):
        """봇 시작"""
        try:
            bot_script = self.project_root / "start_bot.py"
            if not bot_script.exists():
                print("  ❌ start_bot.py 파일이 없습니다.")
                return False
            
            print("  🤖 AI_Solarbot 시작 중...")
            
            # 백그라운드에서 봇 실행
            process = subprocess.Popen(
                [sys.executable, str(bot_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # PID 저장
            pid_file = self.project_root / "bot.pid"
            with open(pid_file, "w") as f:
                f.write(str(process.pid))
            
            print(f"  ✅ 봇이 시작되었습니다. PID: {process.pid}")
            print(f"  📁 PID 파일: {pid_file}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 봇 시작 실패: {e}")
            return False
    
    def stop_bot(self):
        """봇 중지"""
        print("🛑 AI_Solarbot 중지 중...")
        
        pid_file = self.project_root / "bot.pid"
        if not pid_file.exists():
            print("  ⚠️ PID 파일이 없습니다. 봇이 실행 중이지 않을 수 있습니다.")
            return True
        
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            
            # 프로세스 종료
            import signal
            os.kill(pid, signal.SIGTERM)
            
            # PID 파일 삭제
            pid_file.unlink()
            
            print(f"  ✅ 봇이 중지되었습니다. PID: {pid}")
            return True
            
        except (ValueError, ProcessLookupError, FileNotFoundError) as e:
            print(f"  ⚠️ 봇 중지 중 오류: {e}")
            return True
        except Exception as e:
            print(f"  ❌ 봇 중지 실패: {e}")
            return False
    
    def show_status(self):
        """배포 상태 확인"""
        print("📊 AI_Solarbot 상태 확인")
        print("=" * 50)
        
        # PID 확인
        pid_file = self.project_root / "bot.pid"
        if pid_file.exists():
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())
                
                # 프로세스 존재 확인
                try:
                    os.kill(pid, 0)  # 신호 0은 프로세스 존재 확인용
                    print(f"🟢 상태: 실행 중 (PID: {pid})")
                except ProcessLookupError:
                    print("🔴 상태: 중지됨 (PID 파일은 있지만 프로세스 없음)")
                    pid_file.unlink()  # 잘못된 PID 파일 삭제
                    
            except (ValueError, FileNotFoundError):
                print("🔴 상태: 중지됨 (잘못된 PID 파일)")
        else:
            print("🔴 상태: 중지됨")
        
        # 로그 파일 확인
        log_file = self.logs_dir / "bot.log"
        if log_file.exists():
            print(f"📝 로그 파일: {log_file}")
            print(f"📊 로그 크기: {log_file.stat().st_size / 1024:.1f} KB")
        else:
            print("📝 로그 파일: 없음")
        
        # 환경 설정 확인
        env_file = self.config_dir / ".env"
        if env_file.exists():
            print(f"⚙️ 환경 설정: {env_file}")
        else:
            print("⚙️ 환경 설정: 없음")

def main():
    """메인 함수"""
    deploy_manager = DeploymentManager()
    
    if len(sys.argv) < 2:
        print("사용법: python deploy.py [명령어]")
        print("명령어:")
        print("  setup     - 환경 설정")
        print("  test      - 테스트 실행")
        print("  deploy    - 배포 (개발환경)")
        print("  deploy-staging  - 스테이징 배포")
        print("  deploy-prod     - 운영 배포")
        print("  stop      - 봇 중지")
        print("  status    - 상태 확인")
        print("  backup    - 백업 생성")
        return
    
    command = sys.argv[1]
    
    if command == "setup":
        print("🚀 팜솔라 AI_Solarbot 환경 설정")
        print("=" * 50)
        
        # 필수 조건 확인
        errors = deploy_manager.check_prerequisites()
        if errors:
            print("❌ 필수 조건 확인 실패:")
            for error in errors:
                print(f"  - {error}")
            return
        
        # 환경 설정
        if not deploy_manager.setup_environment():
            print("⚠️ .env 파일을 설정한 후 다시 실행하세요.")
            return
        
        # 의존성 설치
        if not deploy_manager.install_dependencies():
            return
        
        print("✅ 환경 설정이 완료되었습니다!")
        
    elif command == "test":
        deploy_manager.run_tests()
        
    elif command == "deploy":
        deploy_manager.deploy_to_environment("development")
        
    elif command == "deploy-staging":
        deploy_manager.deploy_to_environment("staging")
        
    elif command == "deploy-prod":
        # 운영 배포는 추가 확인
        confirm = input("⚠️ 운영 환경에 배포하시겠습니까? (yes/no): ")
        if confirm.lower() == "yes":
            deploy_manager.backup_current_deployment()
            deploy_manager.deploy_to_environment("production")
        else:
            print("배포가 취소되었습니다.")
            
    elif command == "stop":
        deploy_manager.stop_bot()
        
    elif command == "status":
        deploy_manager.show_status()
        
    elif command == "backup":
        deploy_manager.backup_current_deployment()
        
    else:
        print(f"알 수 없는 명령어: {command}")

if __name__ == "__main__":
    main() 