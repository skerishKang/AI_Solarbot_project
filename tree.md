# 🌳 AI_Solarbot_Project 구조 (v2.2)

## 📊 프로젝트 통계
- **총 라인 수**: 2,100+ 줄
- **주요 모듈**: 5개
- **명령어**: 27개
- **기능**: 엔터프라이즈급 모니터링/관리 + 과제 업로드/설명 시스템

## 📁 디렉토리 구조

```
AI_Solarbot_Project/
├── 📄 README.md (311줄) - 프로젝트 전체 가이드
├── 📄 requirements.txt (11줄) - 패키지 의존성
├── 📄 start_bot.py (45줄) - 통합 실행 스크립트
├── 📄 start_bot.bat (10줄) - Windows 배치 실행
├── 📄 tree.md (현재 파일) - 프로젝트 구조
├── 📄 project_plan.md (업데이트됨) - 프로젝트 계획
│
├── 📁 src/ (메인 소스코드)
│   ├── 🐍 bot.py (720줄) - 메인 봇 로직 + 새로운 명령어
│   ├── 🧠 ai_handler.py (320줄) - AI 엔진 + 과제 설명 기능
│   ├── 📚 homework_manager.py (299줄) - 과제 관리
│   ├── 📊 monitoring.py (310줄) - 실시간 모니터링
│   └── 👑 admin_commands.py (320줄) - 관리자 기능
│
├── 📁 config/
│   └── ⚙️ settings.py (85줄) - 중앙화 설정
│
├── 📁 docs/
│   └── 📖 API_GUIDE.md (150줄) - API 사용 가이드
│
├── 📁 과제/ (새로 추가)
│   └── 📚 README.md (120줄) - 과제 관리 가이드
│
├── 📁 data/ (자동 생성)
│   ├── 📊 homework_data.json - 과제 데이터
│   ├── 📈 user_activity.json - 사용자 활동
│   ├── 📉 bot_metrics.json - 봇 메트릭
│   └── ❌ error_log.json - 에러 로그
│
└── 📁 backups/ (자동 생성)
    └── 📦 [타임스탬프]/ - 자동 백업 폴더
```

## 🚀 새로운 기능 (v2.1 → v2.2)

### 📤 과제 파일 업로드 시스템
- **명령어**: `/upload [과제명]`, `/upload_homework [과제명]`
- **기능**: 
  - 자동 파일 경로 감지
  - HTML 파일 텍스트 추출
  - 다중 경로 패턴 지원
  - 과제 내용 자동 분석

### 📚 과제 설명 생성 시스템  
- **명령어**: `/explain [과제명]`, `/explain_homework [과제명]`
- **기능**:
  - AI 기반 과제 분석
  - 단계별 풀이 가이드
  - 실무 활용 팁 제공
  - 학습 목표 명시
  - 예상 소요시간 안내

### 🗂️ 과제 관리 가이드
- **파일**: `과제/README.md`
- **내용**:
  - 표준 폴더 구조 제안
  - 파일 명명 규칙
  - 봇 연동 방법
  - 사용 예시 및 체크리스트

## 🎯 명령어 목록 (총 27개)

### 📚 과제 및 학습 (8개)
- `/homework` - 현재 과제 확인
- `/homework [주차] [강]` - 특정 과제 확인  
- `/upload [과제명]` - 과제 파일 업로드 ⭐ 신규
- `/explain [과제명]` - 과제 설명 생성 ⭐ 신규
- `/submit [내용]` - 과제 제출
- `/progress` - 진도 확인
- `/template [주제]` - 프롬프트 템플릿
- `/practice` - 연습 과제

### ☀️ 태양광 계산 (2개)
- `/solar` - 계산 가이드
- `/calc [용량] [지역] [각도]` - 즉시 계산

### 🔧 시스템 (3개)  
- `/start` - 봇 시작
- `/help` - 도움말
- `/status` - 시스템 상태

### 👑 관리자 전용 (14개)
- `/admin` - 대시보드
- `/admin_dashboard` - 시스템 리소스
- `/admin_users` - 사용자 분석
- `/admin_backup` - 데이터 백업
- `/admin_cleanup` - 로그 정리
- `/admin_broadcast` - 전체 공지
- `/admin_restart` - 봇 재시작
- `/admin_report` - 일일 리포트
- `/admin_stats` - 상세 통계
- `/admin_logs` - 에러 로그
- `/admin_config` - 설정 관리
- `/admin_monitor` - 모니터링 설정
- `/admin_export` - 데이터 내보내기
- `/next` - 다음 주차 진행

## 🔥 주요 개선사항

### 1. 과제 파일 업로드 자동화
```python
# 자동 경로 감지 패턴
possible_paths = [
    f"수업/6주/3. 교과서/{homework_input}/{homework_input}과제.html",
    f"수업/12주/3. 교과서/{homework_input}/{homework_input}과제.html", 
    f"과제/{homework_input}/과제.html"
]
```

### 2. AI 기반 과제 설명 생성
```python
# 설명 형식
📚 과제 개요
🎯 학습 목표  
📋 단계별 가이드
💡 실무 활용 팁
⚠️ 주의사항
⏱️ 예상 소요시간
🌟 성공 포인트
```

### 3. 표준화된 과제 관리
- 일관된 폴더 구조
- 표준 파일 명명 규칙
- 자동 봇 연동
- 진도 추적 시스템

## 💾 데이터 저장

### JSON 파일 구조
```json
{
  "homework_data.json": "과제 정보",
  "user_activity.json": "사용자 활동 추적",
  "bot_metrics.json": "봇 성능 메트릭",
  "error_log.json": "에러 로그"
}
```

## 🎉 성과 요약

| 항목 | v2.0 | v2.1 | v2.2 | 증가율 |
|------|------|------|------|--------|
| 총 라인 수 | 1,061 | 1,905 | 2,100+ | +98% |
| 명령어 수 | 12 | 25 | 27 | +125% |
| 모듈 수 | 3 | 5 | 6 | +100% |
| 기능 복잡도 | 기본 | 고급 | 엔터프라이즈 | - |

---

**🚀 현재 상태**: 프로덕션급 엔터프라이즈 교육 봇
**📈 다음 목표**: 웹 인터페이스 및 대시보드 개발
**🎯 비전**: 완전 자동화된 AI 교육 플랫폼 