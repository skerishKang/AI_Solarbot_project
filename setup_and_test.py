#!/usr/bin/env python3
"""
AI_Solarbot 프로젝트 설정 및 테스트 실행 스크립트
의존성 설치, 환경 설정, 테스트 실행을 자동화
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(title):
    """헤더 출력"""
    print("\n" + "=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def print_step(step, description):
    """단계별 진행 상황 출력"""
    print(f"\n📋 {step}. {description}")

def run_command(command, description="", check=True):
    """명령어 실행"""
    if description:
        print(f"   💻 {description}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=check
        )
        
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 명령어 실행 실패: {e}")
        if e.stderr:
            print(f"   🔍 오류 내용: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"   ❌ 예상치 못한 오류: {e}")
        return False

def check_python_version():
    """Python 버전 확인"""
    print_step(1, "Python 버전 확인")
    
    version = sys.version_info
    if version >= (3, 8):
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} (요구사항: 3.8+)")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (요구사항: 3.8+)")
        print("   🔧 Python 3.8 이상으로 업그레이드하세요.")
        return False

def install_dependencies(offline_mode=False):
    """의존성 패키지 설치"""
    print_step(2, "의존성 패키지 설치")
    
    # requirements.txt 파일 확인
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("   ❌ requirements.txt 파일을 찾을 수 없습니다.")
        return False
    
    # pip 업그레이드
    print("   🔄 pip 업그레이드...")
    run_command("python -m pip install --upgrade pip", check=False)
    
    # 오프라인 모드에서는 기본 패키지만 설치
    if offline_mode:
        print("   🔧 OFFLINE_MODE: 기본 패키지만 설치")
        basic_packages = [
            "python-dotenv",
            "requests",
            "beautifulsoup4",
            "pandas",
            "numpy",
            "nltk",
            "textblob",
            "scikit-learn"
        ]
        
        for package in basic_packages:
            success = run_command(f"pip install {package}", f"{package} 설치", check=False)
            if not success:
                print(f"   ⚠️ {package} 설치 실패 (계속 진행)")
    else:
        # 전체 패키지 설치
        print("   📦 전체 패키지 설치...")
        success = run_command("pip install -r requirements.txt", "requirements.txt에서 패키지 설치", check=False)
        if not success:
            print("   ⚠️ 일부 패키지 설치 실패 (계속 진행)")
    
    return True

def setup_environment():
    """환경 설정"""
    print_step(3, "환경 설정")
    
    # 필요한 디렉토리 생성
    directories = ["logs", "data", "config", "test"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   📁 {directory}/ 디렉토리 확인")
    
    # 환경 변수 파일 확인
    env_file = Path(".env")
    if not env_file.exists():
        print("   ⚠️ .env 파일이 없습니다. .env.example을 참고하여 생성하세요.")
    else:
        print("   ✅ .env 파일 확인")
    
    return True

def run_tests(offline_mode=False):
    """테스트 실행"""
    print_step(4, "통합 테스트 실행")
    
    # 환경 변수 설정
    env = os.environ.copy()
    if offline_mode:
        env['OFFLINE_MODE'] = 'true'
        print("   🔧 OFFLINE_MODE 활성화")
    else:
        env['OFFLINE_MODE'] = 'false'
        print("   🌐 ONLINE_MODE 활성화")
    
    # 테스트 실행
    test_file = Path("test/integration_test.py")
    if not test_file.exists():
        print("   ❌ 테스트 파일을 찾을 수 없습니다.")
        return False
    
    print("   🧪 통합 테스트 시작...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        # 테스트 출력 표시
        if result.stdout:
            print("   📋 테스트 결과:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        if result.stderr:
            print("   ⚠️ 테스트 경고/오류:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        success = result.returncode == 0
        if success:
            print("   ✅ 모든 테스트 통과!")
        else:
            print("   ❌ 일부 테스트 실패")
        
        return success
        
    except subprocess.TimeoutExpired:
        print("   ⏰ 테스트 타임아웃 (5분 초과)")
        return False
    except Exception as e:
        print(f"   ❌ 테스트 실행 오류: {e}")
        return False

def create_content_analyzer_test():
    """콘텐츠 분석기 단독 테스트 생성"""
    print_step(5, "콘텐츠 분석기 단독 테스트")
    
    test_code = '''#!/usr/bin/env python3
"""
지능형 콘텐츠 분석기 단독 테스트
외부 의존성 없이 로컬에서 실행 가능
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from intelligent_content_analyzer import IntelligentContentAnalyzer
    
    def test_content_analyzer():
        print("🧪 지능형 콘텐츠 분석기 테스트 시작")
        
        analyzer = IntelligentContentAnalyzer()
        
        # 테스트 콘텐츠
        test_content = """
        # 태양광 발전 시스템 가이드
        
        태양광 발전은 친환경적이고 지속가능한 에너지원입니다.
        이 가이드는 초보자를 위한 완전한 설치 방법을 제공합니다.
        
        ## 장점
        - 환경 친화적
        - 장기적 비용 절약
        - 정부 지원 혜택
        
        ## 주의사항
        하지만 초기 투자 비용이 높고, 날씨에 영향을 받습니다.
        전문가와 상담 후 설치를 권장합니다.
        """
        
        try:
            # 감정 분석 테스트
            print("\\n1. 감정 분석 테스트")
            sentiment = analyzer._calculate_sentiment_score("태양광 가이드", test_content)
            print(f"   감정: {sentiment.get('overall', 'N/A')}")
            print(f"   점수: {sentiment.get('score', 0):.2f}")
            
            # 고급 감정 분석 테스트
            print("\\n2. 고급 감정 분석 테스트")
            advanced_sentiment = analyzer._calculate_advanced_sentiment_score(
                "태양광 가이드", test_content, "https://example.com"
            )
            print(f"   신뢰도: {advanced_sentiment.get('confidence', 0):.2f}")
            print(f"   강도: {advanced_sentiment.get('intensity', 0):.2f}")
            
            # 품질 평가 테스트
            print("\\n3. 품질 평가 테스트")
            quality = analyzer._calculate_advanced_quality_score(
                "태양광 가이드", test_content, "https://example.com", "tutorial"
            )
            print(f"   전체 점수: {quality.get('overall_score', 0):.1f}")
            print(f"   등급: {quality.get('grade', 'N/A')}")
            
            print("\\n✅ 모든 테스트 완료!")
            return True
            
        except Exception as e:
            print(f"\\n❌ 테스트 실패: {e}")
            return False
    
    if __name__ == "__main__":
        success = test_content_analyzer()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("src/intelligent_content_analyzer.py 파일이 있는지 확인하세요.")
    sys.exit(1)
'''
    
    # 테스트 파일 생성
    test_file = Path("test/content_analyzer_test.py")
    test_file.write_text(test_code, encoding='utf-8')
    
    print(f"   📄 {test_file} 생성 완료")
    
    # 테스트 실행
    print("   🧪 콘텐츠 분석기 테스트 실행...")
    success = run_command(f"python {test_file}", "콘텐츠 분석기 테스트", check=False)
    
    return success

def main():
    """메인 함수"""
    print_header("AI_Solarbot 프로젝트 설정 및 테스트")
    
    # 명령행 인수 처리
    offline_mode = '--offline' in sys.argv or os.getenv('OFFLINE_MODE', 'false').lower() == 'true'
    skip_install = '--skip-install' in sys.argv
    test_only = '--test-only' in sys.argv
    
    if offline_mode:
        print("🔧 OFFLINE_MODE로 실행")
    
    # 1. Python 버전 확인
    if not check_python_version():
        sys.exit(1)
    
    # 2. 의존성 설치 (스킵 옵션이 없는 경우)
    if not skip_install and not test_only:
        if not install_dependencies(offline_mode):
            print("⚠️ 의존성 설치에 문제가 있지만 계속 진행합니다.")
    
    # 3. 환경 설정
    if not test_only:
        setup_environment()
    
    # 4. 테스트 실행
    test_success = run_tests(offline_mode)
    
    # 5. 콘텐츠 분석기 단독 테스트
    analyzer_success = create_content_analyzer_test()
    
    # 결과 요약
    print_header("설정 및 테스트 완료")
    
    if test_success and analyzer_success:
        print("🎉 모든 설정과 테스트가 성공적으로 완료되었습니다!")
        print("\n📋 다음 단계:")
        print("   1. .env 파일을 설정하여 API 키 등을 추가하세요")
        print("   2. python src/bot.py 명령으로 봇을 실행하세요")
        print("   3. 문제가 발생하면 logs/ 디렉토리의 로그를 확인하세요")
        return True
    else:
        print("⚠️ 일부 테스트가 실패했지만 기본 기능은 동작할 수 있습니다.")
        print("\n🔧 문제 해결:")
        print("   1. python setup_and_test.py --offline 로 오프라인 모드 시도")
        print("   2. pip install -r requirements.txt 로 수동 설치")
        print("   3. 개별 모듈을 확인하여 누락된 의존성 설치")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 