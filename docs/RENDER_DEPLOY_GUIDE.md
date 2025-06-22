# 🚀 Render.com 배포 가이드

## 📋 사전 준비사항

### 1. GitHub 리포지토리 생성
```bash
# 프로젝트를 GitHub에 업로드
git init
git add .
git commit -m "Initial commit: AI Solarbot Project"
git remote add origin https://github.com/YOUR_USERNAME/ai-solarbot.git
git push -u origin main
```

### 2. 필수 환경변수 준비
다음 값들을 미리 준비해주세요:
- `TELEGRAM_BOT_TOKEN`: 텔레그램 봇 토큰
- `GEMINI_API_KEY`: Gemini API 키
- `OPENAI_API_KEY`: OpenAI API 키 (선택사항)
- `ADMIN_USER_ID`: 관리자 텔레그램 사용자 ID

## 🌐 Render 배포 단계

### Step 1: 새 서비스 생성
1. [Render Dashboard](https://dashboard.render.com)에 로그인
2. **"New +"** 버튼 클릭
3. **"Background Worker"** 선택

### Step 2: GitHub 연결
1. **"Connect a repository"** 선택
2. GitHub 계정 연결 및 권한 부여
3. `ai-solarbot` 리포지토리 선택

### Step 3: 서비스 설정
```yaml
Name: ai-solarbot
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python src/bot.py
Plan: Free
```

### Step 4: 환경변수 설정
Environment Variables 섹션에서 다음을 추가:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
ADMIN_USER_ID=your_telegram_user_id
```

### Step 5: 배포 실행
1. **"Create Web Service"** 클릭
2. 자동 배포 시작 (약 2-3분 소요)
3. 로그에서 "SUCCESS: AI_Solarbot bot is ready" 확인

## 📊 배포 후 확인사항

### 1. 서비스 상태 확인
- Render Dashboard에서 서비스 상태가 "Live"인지 확인
- 로그에서 에러 메시지가 없는지 확인

### 2. 봇 기능 테스트
텔레그램에서 다음 명령어들을 테스트:
```
/start - 봇 시작
/help - 도움말
/status - 시스템 상태
/solar_calc 5 - 태양광 계산
```

### 3. 관리자 기능 테스트 (관리자만)
```
/admin_dashboard - 시스템 대시보드
/admin_users - 사용자 통계
/admin_backup - 데이터 백업
```

## 🔧 문제 해결

### 자주 발생하는 문제들

#### 1. 봇이 응답하지 않는 경우
- 환경변수가 올바르게 설정되었는지 확인
- Render 로그에서 에러 메시지 확인
- Telegram Bot Token이 유효한지 확인

#### 2. API 키 관련 오류
```
Error: API key not found
```
**해결방법**: Environment Variables에서 API 키 재확인

#### 3. 메모리 부족 오류
```
Error: Memory limit exceeded
```
**해결방법**: Free 플랜의 메모리 제한 (512MB) 고려하여 코드 최적화

### 로그 확인 방법
1. Render Dashboard → 해당 서비스 선택
2. **"Logs"** 탭 클릭  
3. 실시간 로그 모니터링

## 💡 최적화 팁

### 1. 자동 재배포 설정
- GitHub에 푸시할 때마다 자동 배포
- `render.yaml` 파일로 설정 관리

### 2. 환경별 설정 분리
```python
# config/settings.py
import os

# 개발/운영 환경 분리
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    # 운영 환경 설정
    LOG_LEVEL = 'INFO'
else:
    # 개발 환경 설정  
    LOG_LEVEL = 'DEBUG'
```

### 3. 모니터링 및 알림
- Render에서 제공하는 모니터링 기능 활용
- 봇 다운타임 발생시 이메일 알림 설정

## 📈 업그레이드 옵션

### 무료 플랜 제한사항
- **메모리**: 512MB
- **CPU**: 공유
- **Sleep**: 15분 비활성시 자동 슬립

### 유료 플랜 혜택 ($7/월)
- **메모리**: 1GB+
- **CPU**: 전용
- **Sleep**: 없음 (24/7 운영)
- **커스텀 도메인** 지원

## 🎯 배포 완료!

배포가 성공적으로 완료되면:
- ✅ 봇이 24/7 자동 운영
- ✅ GitHub 푸시시 자동 업데이트  
- ✅ 서버 관리 불필요
- ✅ 무료로 시작 가능

---

## 📞 지원

문제가 발생하면:
1. Render 로그 확인
2. GitHub Issues 생성
3. 텔레그램 봇 `/admin_status` 명령어로 상태 확인 