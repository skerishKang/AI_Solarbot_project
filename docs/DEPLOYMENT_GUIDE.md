# 팜솔라 AI_Solarbot 배포 가이드

## 📋 목차
1. [배포 준비](#배포-준비)
2. [환경 변수 설정](#환경-변수-설정)
3. [자동 배포](#자동-배포)
4. [수동 배포](#수동-배포)
5. [배포 후 확인](#배포-후-확인)
6. [문제해결](#문제해결)

---

## 🚀 배포 준비

### 시스템 요구사항
- **Python**: 3.8 이상
- **메모리**: 최소 2GB RAM
- **저장공간**: 최소 5GB
- **네트워크**: 인터넷 연결 필수

### 필수 계정 및 API 키
1. **텔레그램 봇 토큰**: [@BotFather](https://t.me/BotFather)에서 발급
2. **Google Gemini API**: [Google AI Studio](https://aistudio.google.com/)
3. **OpenAI API**: [OpenAI Platform](https://platform.openai.com/)
4. **구글 드라이브 API**: [Google Cloud Console](https://console.cloud.google.com/)

---

## ⚙️ 환경 변수 설정

### .env 파일 생성
프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# 기본 설정
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ADMIN_USER_ID=your_telegram_user_id
BOT_NAME=AI_Solarbot
BOT_VERSION=2.0.0

# AI API 키
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_AI_MODEL=gemini-2.5-flash

# 구글 드라이브
GOOGLE_PROJECT_ID=your_google_project_id
GOOGLE_CREDENTIALS_FILE=config/google_credentials.json
DRIVE_FOLDER_NAME=AI_Solarbot_과제

# 로깅
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# 보안
ENCRYPTION_KEY=auto_generated_key_will_be_here
SESSION_TIMEOUT=60

# 사용량 제한
GEMINI_DAILY_LIMIT=1500
OPENAI_DAILY_LIMIT=100
USER_DAILY_MESSAGE_LIMIT=200

# 팜솔라 설정
DEFAULT_COURSE_TYPE=12주
FARMSOLAR_WEBSITE=https://farmsolar.co.kr

# 배포 환경
ENVIRONMENT=production
DEBUG=false
```

### 구글 드라이브 인증 설정
1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트 생성
2. Google Drive API 활성화
3. OAuth 2.0 클라이언트 ID 생성
4. `credentials.json` 다운로드 후 `config/google_credentials.json`으로 저장

---

## 🤖 자동 배포

### 1단계: 환경 설정
```bash
python deploy.py setup
```
- 필수 조건 확인
- 디렉토리 생성
- 의존성 패키지 설치

### 2단계: 테스트 실행
```bash
python deploy.py test
```
- 통합 테스트 실행
- 시스템 안정성 확인

### 3단계: 배포 실행
```bash
# 개발 환경
python deploy.py deploy

# 스테이징 환경  
python deploy.py deploy-staging

# 운영 환경
python deploy.py deploy-prod
```

### 배포 상태 확인
```bash
python deploy.py status
```

### 봇 중지
```bash
python deploy.py stop
```

---

## 🔧 수동 배포

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 로드
```bash
# Windows
set TELEGRAM_BOT_TOKEN=your_token
set GEMINI_API_KEY=your_key

# Linux/Mac
export TELEGRAM_BOT_TOKEN=your_token
export GEMINI_API_KEY=your_key
```

### 3. 봇 시작
```bash
python start_bot.py
```

### 4. 백그라운드 실행 (Linux/Mac)
```bash
nohup python start_bot.py > logs/bot.log 2>&1 &
```

### 5. Windows 서비스 등록
```batch
# start_bot.bat 실행
start_bot.bat
```

---

## ✅ 배포 후 확인

### 기본 기능 테스트
1. **봇 응답 확인**
   ```
   텔레그램에서 /start 명령어 실행
   ```

2. **AI 기능 테스트**
   ```
   "안녕하세요" 메시지 전송 후 AI 응답 확인
   ```

3. **드라이브 연결 테스트**
   ```
   /connect_drive 명령어로 구글 드라이브 연결
   ```

4. **워크스페이스 생성 테스트**
   ```
   /create_workspace 12주 명령어 실행
   ```

### 시스템 모니터링
```bash
# 로그 확인
tail -f logs/bot.log

# 프로세스 확인
ps aux | grep bot.py

# 메모리 사용량 확인
free -h

# 디스크 사용량 확인
df -h
```

### 성능 테스트
```bash
# 통합 테스트 재실행
python test/integration_test.py

# 부하 테스트 (선택사항)
python test/load_test.py
```

---

## 🛠️ 문제해결

### 일반적인 문제들

#### 1. 봇이 시작되지 않음
**증상**: `start_bot.py` 실행 시 오류 발생

**해결방법**:
```bash
# 로그 확인
cat logs/bot.log

# 환경 변수 확인
echo $TELEGRAM_BOT_TOKEN

# 권한 확인
chmod +x start_bot.py
```

#### 2. AI 응답 없음
**증상**: 메시지 전송 시 AI가 응답하지 않음

**해결방법**:
```bash
# API 키 확인
echo $GEMINI_API_KEY
echo $OPENAI_API_KEY

# 사용량 한도 확인
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/usage
```

#### 3. 구글 드라이브 연결 실패
**증상**: `/connect_drive` 명령어 실행 시 오류

**해결방법**:
```bash
# 인증 파일 확인
ls -la config/google_credentials.json

# 권한 확인
cat config/google_credentials.json | jq .

# API 활성화 확인 (Google Cloud Console)
```

#### 4. 메모리 부족
**증상**: 시스템이 느려지거나 봇이 종료됨

**해결방법**:
```bash
# 메모리 사용량 확인
free -h
ps aux --sort=-%mem | head

# 봇 재시작
python deploy.py stop
python deploy.py deploy
```

### 로그 분석
```bash
# 에러 로그만 확인
grep "ERROR" logs/bot.log

# 최근 1시간 로그
grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" logs/bot.log

# 특정 사용자 활동 추적
grep "user_id:12345" logs/bot.log
```

### 긴급 복구
```bash
# 백업에서 복구
python deploy.py backup
cp backups/backup_latest/* ./

# 팩토리 리셋
rm -rf data/
python deploy.py setup
```

---

## 🔄 업데이트 및 유지보수

### 정기 업데이트
```bash
# 1. 백업 생성
python deploy.py backup

# 2. 코드 업데이트
git pull origin main

# 3. 의존성 업데이트
pip install -r requirements.txt --upgrade

# 4. 테스트 실행
python deploy.py test

# 5. 재배포
python deploy.py deploy-prod
```

### 로그 관리
```bash
# 로그 로테이션 (매주 실행)
python scripts/rotate_logs.py

# 오래된 로그 삭제 (매월 실행)
find logs/ -name "*.log.*" -mtime +30 -delete
```

### 성능 최적화
```bash
# 캐시 정리
rm -rf __pycache__/
rm -rf src/__pycache__/

# 데이터베이스 최적화 (선택사항)
python scripts/optimize_db.py
```

---

## 📊 모니터링 설정

### 시스템 모니터링 스크립트
```bash
#!/bin/bash
# monitor.sh

while true; do
    # 봇 프로세스 확인
    if ! pgrep -f "start_bot.py" > /dev/null; then
        echo "$(date): 봇이 중지됨. 재시작 중..." >> logs/monitor.log
        python start_bot.py &
    fi
    
    # 메모리 사용량 확인
    MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    if [ $MEMORY_USAGE -gt 80 ]; then
        echo "$(date): 메모리 사용량 높음: ${MEMORY_USAGE}%" >> logs/monitor.log
    fi
    
    sleep 300  # 5분마다 확인
done
```

### 크론탭 설정
```bash
# crontab -e
# 매일 새벽 2시 백업
0 2 * * * cd /path/to/AI_Solarbot_Project && python deploy.py backup

# 매주 일요일 로그 정리
0 3 * * 0 cd /path/to/AI_Solarbot_Project && python scripts/cleanup_logs.py

# 매시간 상태 확인
0 * * * * cd /path/to/AI_Solarbot_Project && python deploy.py status > /dev/null
```

---

## 🔒 보안 고려사항

### 환경 변수 보안
- `.env` 파일을 절대 Git에 커밋하지 마세요
- API 키는 정기적으로 갱신하세요
- 프로덕션 환경에서는 `DEBUG=false`로 설정하세요

### 파일 권한 설정
```bash
# 중요 파일 권한 제한
chmod 600 .env
chmod 600 config/google_credentials.json
chmod 700 logs/
```

### 방화벽 설정
```bash
# 필요한 포트만 열기
ufw allow 22    # SSH
ufw allow 443   # HTTPS
ufw enable
```

---

*이 가이드는 AI_Solarbot v2.0 기준으로 작성되었습니다. 최신 업데이트는 GitHub 저장소를 확인하세요.* 