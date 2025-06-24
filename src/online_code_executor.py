"""
온라인 코드 실행 환경 확장 시스템
10개 프로그래밍 언어 지원, 성능 분석, 최적화 제안, AI 코드 리뷰 기능 포함
"""

import os
import re
import json
import time
import asyncio
import tempfile
import subprocess
import psutil
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# timeout_decorator 조건부 import
try:
    import timeout_decorator
    TIMEOUT_DECORATOR_AVAILABLE = True
except ImportError:
    TIMEOUT_DECORATOR_AVAILABLE = False
    print("⚠️ timeout_decorator를 찾을 수 없습니다. 타임아웃 기능이 제한됩니다.")
    # timeout_decorator 대체 함수
    def timeout_decorator(seconds):
        def decorator(func):
            return func
        return decorator

# AI 통합을 위한 imports
try:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from ai_integration_engine import AIIntegrationEngine
    AI_INTEGRATION_AVAILABLE = True
except ImportError:
    AI_INTEGRATION_AVAILABLE = False
    print("⚠️ AIIntegrationEngine을 찾을 수 없습니다. AI 코드 리뷰 기능이 비활성화됩니다.")

# 코드 히스토리 관리를 위한 imports
try:
    from code_history_manager import CodeHistoryManager, history_manager
    HISTORY_MANAGER_AVAILABLE = True
except ImportError:
    HISTORY_MANAGER_AVAILABLE = False
    print("⚠️ CodeHistoryManager를 찾을 수 없습니다. 히스토리 관리 기능이 비활성화됩니다.")

@dataclass
class ExecutionResult:
    """코드 실행 결과 데이터 클래스"""
    success: bool
    language: str
    output: str
    error: str
    execution_time: float
    memory_usage: int
    return_code: int
    performance_score: float
    optimization_suggestions: List[str]
    dependencies_detected: List[str]

@dataclass
class LanguageConfig:
    """언어별 설정 데이터 클래스"""
    name: str
    executable: str
    file_extension: str
    compile_command: Optional[str]
    run_command: str
    timeout: int
    memory_limit: int  # MB
    supported_features: List[str]

class OnlineCodeExecutor:
    """확장된 온라인 코드 실행 시스템 (AI 코드 리뷰 기능 포함)"""
    
    def __init__(self, ai_handler=None):
        self.supported_languages = self._initialize_languages()
        self.execution_history = []
        self.temp_dir = tempfile.mkdtemp(prefix="code_executor_")
        self.max_execution_time = 30  # 최대 실행 시간 (초)
        self.max_memory_usage = 512  # 최대 메모리 사용량 (MB)
        
        # AI 통합 엔진 초기화
        self.ai_integration_engine = None
        if ai_handler:
            try:
                # AI 통합 엔진 임포트 시도
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from ai_integration_engine import AIIntegrationEngine
                self.ai_integration_engine = AIIntegrationEngine(ai_handler)
                print("✅ AI 코드 리뷰 기능이 활성화되었습니다.")
            except ImportError as e:
                print(f"⚠️ AI 통합 엔진을 로드할 수 없습니다: {e}")
                print("📝 AI 코드 리뷰 기능이 비활성화됩니다.")
        
        # 온라인 컴파일러 API 설정
        self.online_apis = {
            'judge0': {
                'url': 'https://judge0-ce.p.rapidapi.com',
                'headers': {
                    'X-RapidAPI-Key': os.getenv('JUDGE0_API_KEY', ''),
                    'X-RapidAPI-Host': 'judge0-ce.p.rapidapi.com',
                    'Content-Type': 'application/json'
                }
            },
            'paiza': {
                'url': 'https://api.paiza.io',
                'headers': {'Content-Type': 'application/json'}
            }
        }
        
    def _initialize_languages(self) -> Dict[str, LanguageConfig]:
        """지원 언어 초기화 - 10개 언어"""
        return {
            'python': LanguageConfig(
                name='Python',
                executable='python',
                file_extension='.py',
                compile_command=None,
                run_command='python {file}',
                timeout=15,
                memory_limit=256,
                supported_features=['numpy', 'pandas', 'matplotlib', 'requests']
            ),
            'javascript': LanguageConfig(
                name='JavaScript',
                executable='node',
                file_extension='.js',
                compile_command=None,
                run_command='node {file}',
                timeout=10,
                memory_limit=128,
                supported_features=['express', 'lodash', 'axios', 'moment']
            ),
            'typescript': LanguageConfig(
                name='TypeScript',
                executable='ts-node',
                file_extension='.ts',
                compile_command='tsc {file} --outDir {temp_dir}',
                run_command='ts-node {file}',
                timeout=15,
                memory_limit=256,
                supported_features=['@types/node', 'typescript']
            ),
            'java': LanguageConfig(
                name='Java',
                executable='java',
                file_extension='.java',
                compile_command='javac {file}',
                run_command='java -cp {dir} {class_name}',
                timeout=20,
                memory_limit=512,
                supported_features=['spring', 'junit', 'maven']
            ),
            'cpp': LanguageConfig(
                name='C++',
                executable='g++',
                file_extension='.cpp',
                compile_command='g++ -o {output} {file}',
                run_command='{output}',
                timeout=15,
                memory_limit=256,
                supported_features=['std', 'boost', 'opencv']
            ),
            'go': LanguageConfig(
                name='Go',
                executable='go',
                file_extension='.go',
                compile_command=None,
                run_command='go run {file}',
                timeout=15,
                memory_limit=256,
                supported_features=['gin', 'gorm', 'testify']
            ),
            'rust': LanguageConfig(
                name='Rust',
                executable='rustc',
                file_extension='.rs',
                compile_command='rustc {file} -o {output}',
                run_command='{output}',
                timeout=20,
                memory_limit=256,
                supported_features=['serde', 'tokio', 'reqwest']
            ),
            'php': LanguageConfig(
                name='PHP',
                executable='php',
                file_extension='.php',
                compile_command=None,
                run_command='php {file}',
                timeout=10,
                memory_limit=128,
                supported_features=['composer', 'laravel', 'symfony']
            ),
            'ruby': LanguageConfig(
                name='Ruby',
                executable='ruby',
                file_extension='.rb',
                compile_command=None,
                run_command='ruby {file}',
                timeout=15,
                memory_limit=256,
                supported_features=['rails', 'sinatra', 'rspec']
            ),
            'csharp': LanguageConfig(
                name='C#',
                executable='dotnet',
                file_extension='.cs',
                compile_command='csc {file}',
                run_command='dotnet run',
                timeout=20,
                memory_limit=512,
                supported_features=['asp.net', 'entity-framework', 'xunit']
            )
        }
    
    async def execute_code(self, code: str, language: str, use_online_api: bool = False) -> ExecutionResult:
        """코드 실행 (로컬 또는 온라인 API 사용)"""
        try:
            language = language.lower()
            
            if language not in self.supported_languages:
                return ExecutionResult(
                    success=False,
                    language=language,
                    output="",
                    error=f"지원하지 않는 언어: {language}. 지원 언어: {', '.join(self.supported_languages.keys())}",
                    execution_time=0.0,
                    memory_usage=0,
                    return_code=-1,
                    performance_score=0.0,
                    optimization_suggestions=[],
                    dependencies_detected=[]
                )
            
            # 스마트 실행 모드: 온라인 API 우선 시도, 실패 시 로컬 폴백
            if use_online_api:
                if self._is_online_api_available():
                    online_result = await self._execute_online(code, language)
                    if online_result.success:
                        return online_result
                    else:
                        # 온라인 실행 실패 시 로컬로 폴백
                        print(f"온라인 실행 실패, 로컬 실행으로 폴백: {online_result.error}")
                        local_result = await self._execute_local(code, language)
                        # 온라인 실행 시도 정보를 에러 메시지에 추가
                        if not local_result.success:
                            local_result.error += f"\\n\\n⚠️ 온라인 실행도 실패했습니다: {online_result.error}"
                        return local_result
                else:
                    # 온라인 API 사용 불가능 시 로컬 실행
                    print("온라인 API 사용 불가능, 로컬 실행으로 진행")
                    return await self._execute_local(code, language)
            else:
                # 로컬 실행 우선, 실패 시 온라인 API 자동 시도
                local_result = await self._execute_local(code, language)
                
                # 로컬 실행이 실패하고 온라인 API가 사용 가능한 경우 자동 폴백
                if not local_result.success and self._is_online_api_available():
                    print(f"로컬 실행 실패, 온라인 API로 재시도: {local_result.error}")
                    online_result = await self._execute_online(code, language)
                    if online_result.success:
                        # 성공한 온라인 결과에 로컬 실행 시도 정보 추가
                        online_result.error = f"ℹ️ 로컬 실행 실패로 온라인 실행됨. 로컬 오류: {local_result.error}\\n\\n{online_result.error}".strip()
                        return online_result
                    else:
                        # 둘 다 실패한 경우 로컬 결과에 온라인 실패 정보 추가
                        local_result.error += f"\\n\\n⚠️ 온라인 실행도 실패했습니다: {online_result.error}"
                
                return local_result
                
        except Exception as e:
            return ExecutionResult(
                success=False,
                language=language,
                output="",
                error=f"실행 중 예상치 못한 오류 발생: {str(e)}",
                execution_time=0.0,
                memory_usage=0,
                return_code=-1,
                performance_score=0.0,
                optimization_suggestions=["🔧 시스템 관리자에게 문의하거나 다른 언어로 시도해보세요."],
                dependencies_detected=[]
            )
    
    async def _execute_local(self, code: str, language: str) -> ExecutionResult:
        """로컬 환경에서 코드 실행"""
        config = self.supported_languages[language]
        start_time = time.time()
        
        # 임시 파일 생성
        temp_file = os.path.join(self.temp_dir, f"code_{int(time.time())}{config.file_extension}")
        
        try:
            # 코드 파일 작성
            with open(temp_file, 'w', encoding='utf-8') as f:
                # Java의 경우 클래스명 추출 및 수정
                if language == 'java':
                    code = self._fix_java_class_name(code, temp_file)
                f.write(code)
            
            # 의존성 검사
            dependencies = self._detect_dependencies(code, language)
            
            # 컴파일 단계 (필요한 경우)
            if config.compile_command:
                compile_result = await self._compile_code(temp_file, config)
                if not compile_result['success']:
                    return ExecutionResult(
                        success=False,
                        language=language,
                        output="",
                        error=compile_result['error'],
                        execution_time=time.time() - start_time,
                        memory_usage=0,
                        return_code=compile_result['return_code'],
                        performance_score=0.0,
                        optimization_suggestions=[],
                        dependencies_detected=dependencies
                    )
            
            # 코드 실행
            execution_result = await self._run_code(temp_file, config)
            
            # 성능 분석
            performance_score = self._calculate_performance_score(
                execution_result['execution_time'],
                execution_result['memory_usage'],
                len(code)
            )
            
            # 최적화 제안 생성
            optimization_suggestions = self._generate_optimization_suggestions(
                code, language, execution_result
            )
            
            # 실행 이력 저장
            result = ExecutionResult(
                success=execution_result['success'],
                language=language,
                output=execution_result['output'],
                error=execution_result['error'],
                execution_time=execution_result['execution_time'],
                memory_usage=execution_result['memory_usage'],
                return_code=execution_result['return_code'],
                performance_score=performance_score,
                optimization_suggestions=optimization_suggestions,
                dependencies_detected=dependencies
            )
            
            self.execution_history.append({
                'timestamp': datetime.now().isoformat(),
                'language': language,
                'success': result.success,
                'execution_time': result.execution_time,
                'performance_score': result.performance_score
            })
            
            return result
            
        finally:
            # 임시 파일 정리
            self._cleanup_temp_files(temp_file)
    
    def _fix_java_class_name(self, code: str, file_path: str) -> str:
        """Java 코드의 클래스명을 파일명에 맞게 수정"""
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # public class 찾기
        class_pattern = r'public\s+class\s+(\w+)'
        match = re.search(class_pattern, code)
        
        if match:
            old_class_name = match.group(1)
            # 클래스명을 파일명으로 변경
            code = code.replace(f'class {old_class_name}', f'class {file_name}')
        else:
            # public class가 없으면 추가
            if 'class ' not in code:
                code = f'public class {file_name} {{\n    public static void main(String[] args) {{\n{code}\n    }}\n}}'
        
        return code
    
    async def _compile_code(self, file_path: str, config: LanguageConfig) -> Dict:
        """코드 컴파일"""
        try:
            if not config.compile_command:
                return {"success": True, "error": "", "return_code": 0}
            
            # 출력 파일명 생성
            if config.name == 'C++' or config.name == 'Rust':
                output_file = file_path.replace(config.file_extension, '.exe' if os.name == 'nt' else '')
            else:
                output_file = file_path
            
            # 컴파일 명령어 준비
            compile_cmd = config.compile_command.format(
                file=file_path,
                output=output_file,
                temp_dir=self.temp_dir,
                dir=os.path.dirname(file_path)
            )
            
            # 컴파일 실행
            process = await asyncio.create_subprocess_shell(
                compile_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(file_path)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
                
                return {
                    "success": process.returncode == 0,
                    "error": stderr.decode('utf-8', errors='ignore'),
                    "return_code": process.returncode,
                    "output_file": output_file if process.returncode == 0 else None
                }
            except asyncio.TimeoutError:
                process.kill()
                return {"success": False, "error": "컴파일 시간 초과", "return_code": -1}
            
        except Exception as e:
            return {"success": False, "error": f"컴파일 오류: {str(e)}", "return_code": -1}
    
    async def _run_code(self, file_path: str, config: LanguageConfig) -> Dict:
        """코드 실행"""
        try:
            start_time = time.time()
            initial_memory = psutil.virtual_memory().used
            
            # 실행 명령어 준비
            if config.name == 'Java':
                # Java 특별 처리
                class_name = os.path.splitext(os.path.basename(file_path))[0]
                run_cmd = config.run_command.format(
                    file=file_path,
                    dir=os.path.dirname(file_path),
                    class_name=class_name
                )
            elif config.compile_command and config.name in ['C++', 'Rust']:
                # 컴파일된 실행 파일 실행
                output_file = file_path.replace(config.file_extension, '.exe' if os.name == 'nt' else '')
                run_cmd = output_file
            else:
                run_cmd = config.run_command.format(file=file_path)
            
            # 프로세스 실행
            process = await asyncio.create_subprocess_shell(
                run_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(file_path)
            )
            
            # 실행 및 메모리 모니터링
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=config.timeout
                )
                
                execution_time = time.time() - start_time
                final_memory = psutil.virtual_memory().used
                memory_usage = max(0, (final_memory - initial_memory) // (1024 * 1024))  # MB
                
                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode('utf-8', errors='ignore'),
                    "error": stderr.decode('utf-8', errors='ignore'),
                    "return_code": process.returncode,
                    "execution_time": execution_time,
                    "memory_usage": memory_usage
                }
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "output": "",
                    "error": f"실행 시간 초과 ({config.timeout}초)",
                    "return_code": -1,
                    "execution_time": config.timeout,
                    "memory_usage": 0
                }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"실행 오류: {str(e)}",
                "return_code": -1,
                "execution_time": 0.0,
                "memory_usage": 0
            }
    
    async def _execute_online(self, code: str, language: str) -> ExecutionResult:
        """온라인 API를 통한 코드 실행 (Judge0 API)"""
        try:
            start_time = time.time()
            
            # Judge0 언어 ID 매핑
            language_id_map = {
                'python': 71,      # Python 3.8.1
                'javascript': 63,  # JavaScript (Node.js 12.14.0)
                'java': 62,        # Java (OpenJDK 13.0.1)
                'cpp': 54,         # C++ (GCC 9.2.0)
                'go': 60,          # Go (1.13.5)
                'rust': 73,        # Rust (1.40.0)
                'php': 68,         # PHP (7.4.1)
                'ruby': 72,        # Ruby (2.7.0)
                'csharp': 51,      # C# (Mono 6.6.0.161)
                'typescript': 74   # TypeScript (3.7.4)
            }
            
            if language not in language_id_map:
                return ExecutionResult(
                    success=False,
                    language=language,
                    output="",
                    error=f"온라인 실행에서 지원하지 않는 언어: {language}",
                    execution_time=0.0,
                    memory_usage=0,
                    return_code=-1,
                    performance_score=0.0,
                    optimization_suggestions=[],
                    dependencies_detected=[]
                )
            
            # Judge0 API 호출을 위한 데이터 준비
            submission_data = {
                "source_code": code,
                "language_id": language_id_map[language],
                "stdin": "",
                "expected_output": ""
            }
            
            # API 키 확인
            api_key = self.online_apis['judge0']['headers']['X-RapidAPI-Key']
            if not api_key:
                # API 키가 없으면 로컬 실행으로 폴백
                return await self._execute_local(code, language)
            
            # Judge0 API에 제출
            submit_url = f"{self.online_apis['judge0']['url']}/submissions"
            
            response = requests.post(
                submit_url,
                headers=self.online_apis['judge0']['headers'],
                json=submission_data,
                timeout=10
            )
            
            if response.status_code != 201:
                # API 호출 실패 시 로컬 실행으로 폴백
                return await self._execute_local(code, language)
            
            submission_result = response.json()
            token = submission_result.get('token')
            
            if not token:
                return await self._execute_local(code, language)
            
            # 결과 조회 (최대 30초 대기)
            max_attempts = 30
            attempt = 0
            
            while attempt < max_attempts:
                await asyncio.sleep(1)
                
                get_url = f"{self.online_apis['judge0']['url']}/submissions/{token}"
                result_response = requests.get(
                    get_url,
                    headers=self.online_apis['judge0']['headers'],
                    timeout=5
                )
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    status_id = result_data.get('status', {}).get('id', 0)
                    
                    # 처리 완료 상태 (1: In Queue, 2: Processing, 3: Accepted, 4: Wrong Answer, etc.)
                    if status_id > 2:
                        execution_time = time.time() - start_time
                        
                        # 결과 파싱
                        stdout = result_data.get('stdout', '') or ''
                        stderr = result_data.get('stderr', '') or ''
                        compile_output = result_data.get('compile_output', '') or ''
                        
                        # 에러 메시지 조합
                        error_msg = ""
                        if stderr:
                            error_msg += f"Runtime Error: {stderr}\n"
                        if compile_output:
                            error_msg += f"Compile Error: {compile_output}\n"
                        
                        # 성공 여부 판단
                        success = status_id == 3  # Accepted
                        
                        # 메모리 사용량 (KB -> MB 변환)
                        memory_kb = result_data.get('memory', 0) or 0
                        memory_usage = int(memory_kb / 1024) if memory_kb else 0
                        
                        # API 실행 시간 (초)
                        api_time = result_data.get('time', 0) or 0
                        actual_execution_time = float(api_time) if api_time else execution_time
                        
                        # 의존성 검출
                        dependencies = self._detect_dependencies(code, language)
                        
                        # 성능 점수 계산
                        performance_score = self._calculate_performance_score(
                            actual_execution_time, memory_usage, len(code)
                        )
                        
                        # 최적화 제안 생성
                        execution_result_dict = {
                            'execution_time': actual_execution_time,
                            'memory_usage': memory_usage,
                            'error': error_msg
                        }
                        suggestions = self._generate_optimization_suggestions(
                            code, language, execution_result_dict
                        )
                        
                        # 실행 이력 저장
                        history_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'language': language,
                            'success': success,
                            'execution_time': actual_execution_time,
                            'memory_usage': memory_usage,
                            'performance_score': performance_score,
                            'api_used': 'judge0'
                        }
                        self.execution_history.append(history_entry)
                        
                        return ExecutionResult(
                            success=success,
                            language=language,
                            output=stdout,
                            error=error_msg.strip(),
                            execution_time=actual_execution_time,
                            memory_usage=memory_usage,
                            return_code=result_data.get('exit_code', 0) or 0,
                            performance_score=performance_score,
                            optimization_suggestions=suggestions,
                            dependencies_detected=dependencies
                        )
                
                attempt += 1
            
            # 타임아웃 발생 시 로컬 실행으로 폴백
            return await self._execute_local(code, language)
            
        except requests.exceptions.RequestException as e:
            # 네트워크 오류 시 로컬 실행으로 폴백
            print(f"Judge0 API 네트워크 오류: {e}")
            return await self._execute_local(code, language)
            
        except Exception as e:
            # 기타 오류 시 로컬 실행으로 폴백
            print(f"Judge0 API 오류: {e}")
            return await self._execute_local(code, language)
    
    def _detect_dependencies(self, code: str, language: str) -> List[str]:
        """코드에서 의존성 라이브러리 검출"""
        dependencies = []
        
        if language == 'python':
            # import 문 찾기
            import_patterns = [
                r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, code)
                dependencies.extend(matches)
        
        elif language == 'javascript':
            # require/import 문 찾기
            js_patterns = [
                r'require\([\'"]([^\'\"]+)[\'"]\)',
                r'import\s+.*\s+from\s+[\'"]([^\'\"]+)[\'"]'
            ]
            for pattern in js_patterns:
                matches = re.findall(pattern, code)
                dependencies.extend(matches)
        
        elif language == 'java':
            # import 문 찾기
            java_pattern = r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*);'
            matches = re.findall(java_pattern, code)
            dependencies.extend(matches)
        
        elif language == 'go':
            # import 문 찾기
            go_pattern = r'import\s+[\'"]([^\'\"]+)[\'"]'
            matches = re.findall(go_pattern, code)
            dependencies.extend(matches)
        
        elif language == 'rust':
            # use 문 찾기
            rust_pattern = r'use\s+([a-zA-Z_][a-zA-Z0-9_:]*);'
            matches = re.findall(rust_pattern, code)
            dependencies.extend(matches)
        
        elif language == 'cpp':
            # include 문 찾기
            cpp_pattern = r'#include\s*[<"]([^>"]+)[">]'
            matches = re.findall(cpp_pattern, code)
            dependencies.extend(matches)
        
        # 중복 제거 및 표준 라이브러리 필터링
        unique_deps = list(set(dependencies))
        standard_libs = ['std', 'system', 'os', 'sys', 'iostream', 'vector', 'string']
        return [dep for dep in unique_deps if dep not in standard_libs]
    
    def _calculate_performance_score(self, execution_time: float, memory_usage: int, code_length: int) -> float:
        """성능 점수 계산 (0-100)"""
        try:
            # 기준값 설정
            time_weight = 0.4
            memory_weight = 0.3
            efficiency_weight = 0.3
            
            # 시간 점수 (5초 이내면 만점)
            time_score = max(0, 100 - (execution_time / 5.0) * 100)
            
            # 메모리 점수 (100MB 이내면 만점)
            memory_score = max(0, 100 - (memory_usage / 100.0) * 100)
            
            # 효율성 점수 (코드 길이 대비 실행 시간)
            efficiency_ratio = code_length / max(execution_time, 0.001)
            efficiency_score = min(100, efficiency_ratio / 1000 * 100)
            
            # 가중 평균
            total_score = (
                time_score * time_weight +
                memory_score * memory_weight +
                efficiency_score * efficiency_weight
            )
            
            return round(total_score, 2)
            
        except:
            return 0.0
    
    def _generate_optimization_suggestions(self, code: str, language: str, execution_result: Dict) -> List[str]:
        """최적화 제안 생성"""
        suggestions = []
        
        try:
            # 실행 시간 기반 제안
            execution_time = execution_result.get('execution_time', 0)
            if execution_time > 5:
                suggestions.append("⏱️ 실행 시간이 긴 편입니다. 알고리즘 최적화를 고려해보세요.")
            
            # 메모리 사용량 기반 제안
            memory_usage = execution_result.get('memory_usage', 0)
            if memory_usage > 200:
                suggestions.append("💾 메모리 사용량이 높습니다. 불필요한 변수나 데이터 구조를 정리해보세요.")
            
            # 언어별 특화 제안
            if language == 'python':
                if 'for' in code and 'range' in code:
                    suggestions.append("🐍 Python: list comprehension 사용을 고려해보세요.")
                if 'print(' in code and code.count('print(') > 5:
                    suggestions.append("🐍 Python: 많은 print문 대신 logging 모듈 사용을 권장합니다.")
                if '+ ' in code and 'str(' in code:
                    suggestions.append("🐍 Python: 문자열 포맷팅에 f-string 사용을 권장합니다.")
            
            elif language == 'javascript':
                if 'var ' in code:
                    suggestions.append("🟨 JavaScript: var 대신 let 또는 const 사용을 권장합니다.")
                if '==' in code:
                    suggestions.append("🟨 JavaScript: == 대신 === 사용을 권장합니다.")
                if 'function(' in code:
                    suggestions.append("🟨 JavaScript: 화살표 함수 사용을 고려해보세요.")
            
            elif language == 'java':
                if 'String +' in code:
                    suggestions.append("☕ Java: 문자열 연결 시 StringBuilder 사용을 고려해보세요.")
                if 'new ArrayList' in code and 'size()' not in code:
                    suggestions.append("☕ Java: ArrayList 초기 크기 설정을 고려해보세요.")
                if 'System.out.println' in code and code.count('System.out.println') > 3:
                    suggestions.append("☕ Java: 로깅 프레임워크 사용을 고려해보세요.")
            
            elif language == 'cpp':
                if '#include <iostream>' in code and 'using namespace std' not in code:
                    suggestions.append("⚡ C++: using namespace std; 사용을 고려해보세요.")
                if 'malloc' in code:
                    suggestions.append("⚡ C++: new/delete 대신 스마트 포인터 사용을 권장합니다.")
            
            elif language == 'go':
                if 'fmt.Println' in code and code.count('fmt.Println') > 5:
                    suggestions.append("🐹 Go: 로깅 패키지 사용을 고려해보세요.")
                if 'err != nil' not in code and 'error' in code:
                    suggestions.append("🐹 Go: 에러 처리를 명시적으로 해주세요.")
            
            # 에러 기반 제안
            error_msg = execution_result.get('error', '').lower()
            if 'timeout' in error_msg:
                suggestions.append("⏰ 무한 루프나 비효율적인 알고리즘을 확인해보세요.")
            if 'memory' in error_msg:
                suggestions.append("💾 메모리 누수나 큰 데이터 구조 사용을 확인해보세요.")
            if 'syntax' in error_msg:
                suggestions.append("📝 문법 오류를 확인해보세요.")
            
            # 성능 점수 기반 제안
            performance_score = self._calculate_performance_score(
                execution_time, memory_usage, len(code)
            )
            
            if performance_score >= 90:
                suggestions.append("🌟 우수한 성능입니다! 코드가 매우 효율적으로 작성되었습니다.")
            elif performance_score >= 70:
                suggestions.append("👍 양호한 성능입니다. 약간의 최적화로 더 개선할 수 있습니다.")
            elif performance_score >= 50:
                suggestions.append("📈 성능 개선 여지가 있습니다. 알고리즘이나 데이터 구조를 검토해보세요.")
            else:
                suggestions.append("🔧 성능 최적화가 필요합니다. 전체적인 접근 방식을 재검토해보세요.")
            
            # 기본 제안 (제안이 없는 경우)
            if not suggestions:
                suggestions.append("✅ 코드가 정상적으로 실행되었습니다!")
            
            return suggestions[:5]  # 최대 5개 제안
            
        except Exception as e:
            return ["💡 코드 최적화 분석 중 오류가 발생했습니다."]
    
    def _is_online_api_available(self) -> bool:
        """온라인 API 사용 가능 여부 확인"""
        try:
            # Judge0 API 키 확인
            api_key = self.online_apis['judge0']['headers']['X-RapidAPI-Key']
            if not api_key or api_key == 'your_rapidapi_key_here':
                return False
            
            # Judge0 API 연결 테스트 (간단한 상태 확인)
            test_url = f"{self.online_apis['judge0']['url']}/languages"
            
            response = requests.get(
                test_url,
                headers=self.online_apis['judge0']['headers'],
                timeout=5
            )
            
            # API가 정상 응답하면 사용 가능
            if response.status_code == 200:
                return True
            else:
                print(f"Judge0 API 상태 확인 실패: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Judge0 API 연결 테스트 실패: {e}")
            return False
        except Exception as e:
            print(f"Judge0 API 상태 확인 오류: {e}")
            return False
    
    def _cleanup_temp_files(self, file_path: str):
        """임시 파일 정리"""
        try:
            # 메인 파일 삭제
            if os.path.exists(file_path):
                os.unlink(file_path)
            
            # 컴파일된 파일들 삭제
            base_name = os.path.splitext(file_path)[0]
            compiled_extensions = ['.exe', '.class', '.o', '']
            
            for ext in compiled_extensions:
                compiled_file = base_name + ext
                if os.path.exists(compiled_file) and compiled_file != file_path:
                    os.unlink(compiled_file)
                    
        except Exception:
            pass  # 파일 삭제 실패는 무시
    
    def get_supported_languages(self) -> List[str]:
        """지원하는 언어 목록 반환"""
        return list(self.supported_languages.keys())
    
    def get_language_info(self, language: str) -> Optional[LanguageConfig]:
        """특정 언어 정보 반환"""
        return self.supported_languages.get(language.lower())
    
    def get_execution_statistics(self) -> Dict:
        """실행 통계 반환"""
        if not self.execution_history:
            return {"total_executions": 0, "average_performance": 0, "language_usage": {}}
        
        total = len(self.execution_history)
        avg_performance = sum(h['performance_score'] for h in self.execution_history) / total
        
        language_usage = {}
        for history in self.execution_history:
            lang = history['language']
            language_usage[lang] = language_usage.get(lang, 0) + 1
        
        return {
            "total_executions": total,
            "average_performance": round(avg_performance, 2),
            "language_usage": language_usage,
            "success_rate": sum(1 for h in self.execution_history if h['success']) / total * 100
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """실행 이력 반환"""
        return self.execution_history[-limit:]
    
    def clear_execution_history(self):
        """실행 이력 초기화"""
        self.execution_history.clear()
    
    def get_system_info(self) -> Dict:
        """시스템 정보 및 지원 기능 반환"""
        return {
            "version": "1.0.0",
            "supported_languages": len(self.supported_languages),
            "online_api_available": self._is_online_api_available(),
            "total_executions": len(self.execution_history),
            "temp_directory": self.temp_dir,
            "features": [
                "로컬 코드 실행 (10개 언어)",
                "온라인 API 연동 (Judge0)",
                "성능 분석 및 최적화 제안",
                "의존성 자동 검출",
                "실행 이력 관리",
                "스마트 폴백 시스템"
            ],
            "api_endpoints": {
                "judge0": self.online_apis['judge0']['url']
            }
        }
    
    def __del__(self):
        """소멸자 - 임시 디렉토리 정리"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass

    async def perform_ai_code_review(self, code: str, language: str, execution_result: Optional[ExecutionResult] = None) -> Dict[str, Any]:
        """AI 기반 코드 리뷰 수행"""
        try:
            if not self.ai_integration_engine:
                return {
                    'ai_review_available': False,
                    'error': 'AI 코드 리뷰 기능이 초기화되지 않았습니다.',
                    'suggestion': 'OnlineCodeExecutor 초기화 시 ai_handler를 전달해주세요.'
                }
            
            # ExecutionResult를 딕셔너리로 변환 (선택적)
            execution_data = None
            if execution_result:
                execution_data = {
                    'success': execution_result.success,
                    'execution_time': execution_result.execution_time,
                    'memory_usage': execution_result.memory_usage,
                    'performance_score': execution_result.performance_score,
                    'return_code': execution_result.return_code,
                    'output': execution_result.output,
                    'error': execution_result.error
                }
            
            # AI 코드 리뷰 수행
            review_result = await self.ai_integration_engine.perform_ai_code_review(
                code=code,
                language=language,
                execution_result=execution_data
            )
            
            review_result['ai_review_available'] = True
            review_result['review_timestamp'] = datetime.now().isoformat()
            
            return review_result
            
        except Exception as e:
            return {
                'ai_review_available': False,
                'error': f'AI 코드 리뷰 중 오류 발생: {str(e)}',
                'suggestion': 'AI 서비스 상태를 확인하거나 나중에 다시 시도해주세요.'
            }
    
    async def execute_code_with_ai_review(self, code: str, language: str, use_online_api: bool = False, enable_ai_review: bool = True) -> Tuple[ExecutionResult, Optional[Dict[str, Any]]]:
        """코드 실행과 AI 리뷰를 함께 수행"""
        try:
            # 1. 코드 실행
            execution_result = await self.execute_code(code, language, use_online_api)
            
            # 2. AI 리뷰 수행 (선택적)
            ai_review_result = None
            if enable_ai_review and self.ai_integration_engine:
                ai_review_result = await self.perform_ai_code_review(code, language, execution_result)
                
                # execution_history에 AI 리뷰 결과 추가
                if self.execution_history and ai_review_result.get('ai_review_available', False):
                    # 가장 최근 실행 기록에 AI 리뷰 결과 추가
                    latest_history = self.execution_history[-1]
                    latest_history['ai_review'] = {
                        'overall_quality': ai_review_result.get('ai_overall_quality', 0),
                        'code_grade': ai_review_result.get('ai_code_grade', 'Unknown'),
                        'dimensions': ai_review_result.get('ai_code_dimensions', {}),
                        'suggestions_count': len(ai_review_result.get('ai_improvement_suggestions', [])),
                        'review_summary': ai_review_result.get('ai_code_review_summary', '')
                    }
            
            return execution_result, ai_review_result
            
        except Exception as e:
            error_execution_result = ExecutionResult(
                success=False,
                language=language,
                output="",
                error=f"통합 실행 중 오류 발생: {str(e)}",
                execution_time=0.0,
                memory_usage=0,
                return_code=-1,
                performance_score=0.0,
                optimization_suggestions=[],
                dependencies_detected=[]
            )
            return error_execution_result, None

# 전역 인스턴스 (필요시 사용)
online_code_executor = None

if __name__ == "__main__":
    # 스크립트로 직접 실행될 때만 인스턴스 생성
    online_code_executor = OnlineCodeExecutor() 