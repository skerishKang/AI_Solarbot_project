# AI_Solarbot API 가이드

## 📋 개요

AI_Solarbot은 텔레그램 봇으로서 다음과 같은 주요 기능을 제공합니다:

- 🤖 **AI 엔진 통합**: Gemini, ChatGPT 지원
- 📚 **교과서 관리**: 주차별 교과서 내용 제공
- 📝 **과제 관리**: 과제 생성, 제출, 평가
- ☀️ **태양광 계산**: 발전량, 수익성 분석

## 🔧 주요 명령어

### 기본 명령어

| 명령어 | 설명 | 사용법 |
|--------|------|--------|
| `/start` | 봇 시작 및 메뉴 표시 | `/start` |
| `/help` | 도움말 표시 | `/help` |
| `/menu` | 메인 메뉴 표시 | `/menu` |

### AI 관련 명령어

| 명령어 | 설명 | 사용법 |
|--------|------|--------|
| `/gemini` | Gemini AI로 질문 | `/gemini 질문내용` |
| `/gpt` | ChatGPT로 질문 | `/gpt 질문내용` |
| `/usage` | AI 사용량 확인 | `/usage` |

### 교과서 관련 명령어

| 명령어 | 설명 | 사용법 |
|--------|------|--------|
| `/교과서` | 주차별 교과서 메뉴 | `/교과서` |
| `/주차` | 특정 주차 내용 | `/주차 1` |

### 과제 관련 명령어

| 명령어 | 설명 | 사용법 |
|--------|------|--------|
| `/과제` | 과제 관리 메뉴 | `/과제` |
| `/과제생성` | 새 과제 생성 | `/과제생성` |
| `/과제제출` | 과제 제출 | `/과제제출` |
| `/과제확인` | 과제 현황 확인 | `/과제확인` |

### 태양광 관련 명령어

| 명령어 | 설명 | 사용법 |
|--------|------|--------|
| `/태양광계산` | 발전량 계산 | `/태양광계산` |
| `/수익성분석` | 투자 수익성 분석 | `/수익성분석` |

## 🔗 API 엔드포인트

### Webhook 설정

```python
# 웹훅 URL 설정
WEBHOOK_URL = "https://your-domain.com/webhook"

# 봇 토큰으로 웹훅 설정
bot.set_webhook(url=WEBHOOK_URL)
```

### 메시지 처리

```python
# 메시지 핸들러 예시
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "안녕하세요! AI_Solarbot입니다.")
```

## 📊 데이터 구조

### 과제 데이터 형식

```json
{
    "homework_id": "unique_id",
    "title": "과제 제목",
    "description": "과제 설명",
    "due_date": "2024-01-01",
    "status": "pending|submitted|graded",
    "student_id": "telegram_user_id",
    "submission": {
        "content": "제출 내용",
        "timestamp": "2024-01-01T10:00:00Z",
        "files": ["file1.pdf", "file2.jpg"]
    },
    "grade": {
        "score": 85,
        "feedback": "평가 피드백",
        "grader": "teacher_id",
        "timestamp": "2024-01-01T15:00:00Z"
    }
}
```

### 사용량 추적 데이터

```json
{
    "user_id": "telegram_user_id",
    "date": "2024-01-01",
    "gemini_requests": 10,
    "gpt_requests": 5,
    "total_tokens": 1500,
    "last_reset": "2024-01-01T00:00:00Z"
}
```

## 🔐 인증 및 권한

### 관리자 권한

```python
ADMIN_USERS = [
    123456789,  # 관리자 텔레그램 ID
    987654321   # 부관리자 텔레그램 ID
]

def is_admin(user_id):
    return user_id in ADMIN_USERS
```

### 사용자 권한 레벨

- **Level 0**: 게스트 (기본 기능만)
- **Level 1**: 학생 (과제 제출 가능)
- **Level 2**: 교사 (과제 생성/평가 가능)
- **Level 3**: 관리자 (모든 기능 접근)

## 🛠️ 설정 및 환경변수

### 필수 환경변수

```bash
# 텔레그램 봇 토큰
TELEGRAM_BOT_TOKEN=your_bot_token_here

# AI API 키
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here

# 관리자 설정
ADMIN_USER_ID=your_telegram_id
BOT_USERNAME=AI_Solarbot
```

### 선택적 환경변수

```bash
# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=5432
DB_NAME=solarbot
DB_USER=solarbot_user
DB_PASSWORD=your_password

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
```

## 📈 모니터링 및 로깅

### 로그 레벨

- **DEBUG**: 디버깅 정보
- **INFO**: 일반 정보
- **WARNING**: 경고 메시지
- **ERROR**: 오류 메시지
- **CRITICAL**: 치명적 오류

### 메트릭 수집

```python
# 사용량 통계
def log_usage(user_id, command, tokens_used):
    logger.info(f"User {user_id} used {command}, tokens: {tokens_used}")
```

## 🚀 배포 가이드

### 로컬 개발 환경

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 봇 실행
python start_bot.py
```

### 프로덕션 배포

```bash
# Docker를 사용한 배포
docker build -t ai-solarbot .
docker run -d --name solarbot -p 8000:8000 ai-solarbot

# 또는 직접 배포
python -m gunicorn --bind 0.0.0.0:8000 app:app
```

## 🔄 업데이트 및 유지보수

### 정기 업데이트 사항

1. **AI 모델 버전 확인**
2. **보안 패치 적용**
3. **사용량 데이터 정리**
4. **로그 파일 로테이션**

### 백업 정책

- **일일 백업**: 과제 데이터, 사용자 설정
- **주간 백업**: 전체 데이터베이스
- **월간 백업**: 시스템 전체 스냅샷

## 📞 지원 및 문의

- **개발자**: 팜솔라 개발팀
- **이메일**: support@farmsolar.com
- **문서 업데이트**: 2024-01-01 