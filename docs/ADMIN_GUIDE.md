# 팜솔라 AI_Solarbot 관리자 가이드

## 📋 목차
1. [관리자 개요](#관리자-개요)
2. [시스템 설정](#시스템-설정)
3. [학생 관리](#학생-관리)
4. [과제 관리](#과제-관리)
5. [모니터링](#모니터링)
6. [문제해결](#문제해결)
7. [유지보수](#유지보수)

---

## 👨‍💼 관리자 개요

### 관리자 권한
팜솔라 AI_Solarbot 관리자는 다음 권한을 가집니다:
- 🔧 시스템 설정 변경
- 👥 학생 계정 관리
- 📊 전체 사용 통계 조회
- 🎯 과제 및 코스 관리
- 🚨 시스템 모니터링 및 알림

### 관리자 인증
```bash
# 관리자 권한 확인
/admin_check

# 관리자 모드 활성화
/admin_mode on
```

---

## ⚙️ 시스템 설정

### 환경 변수 설정
```bash
# config/.env 파일 설정
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ADMIN_USER_ID=your_telegram_id
```

### AI 모델 설정
```bash
# AI 사용량 한도 설정
/set_quota gemini 1500    # Gemini 일일 한도
/set_quota openai 100     # OpenAI 일일 한도

# 기본 모델 변경
/set_default_model gemini-2.5-flash
```

### 시스템 공지사항
```bash
# 전체 공지사항 발송
/broadcast "시스템 점검 안내: 오늘 밤 12시-2시"

# 특정 그룹 공지
/broadcast_group 12주코스 "과제 제출 마감 연장 안내"
```

---

## 👥 학생 관리

### 학생 목록 조회
```bash
# 전체 학생 목록
/student_list

# 코스별 학생 목록
/student_list 12주

# 활성 사용자 목록
/active_users 7  # 최근 7일 활성 사용자
```

### 학생 계정 관리
```bash
# 학생 정보 조회
/student_info @username

# 학생 워크스페이스 초기화
/reset_workspace user_id

# 학생 계정 일시정지
/suspend_user user_id "부적절한 사용"

# 계정 정지 해제
/unsuspend_user user_id
```

### 드라이브 연결 지원
```bash
# 학생 드라이브 연결 상태 확인
/check_drive_status user_id

# 강제 드라이브 재연결
/force_reconnect user_id
```

---

## 📚 과제 관리

### 과제 템플릿 관리
```bash
# 새 과제 템플릿 생성
/create_assignment "1주차_파이썬기초" "파이썬 기본 문법 실습"

# 과제 템플릿 수정
/edit_assignment assignment_id

# 과제 삭제
/delete_assignment assignment_id
```

### 과제 제출 현황
```bash
# 전체 제출 현황
/submission_status

# 특정 과제 제출 현황
/submission_status "1주차_파이썬기초"

# 미제출자 목록
/pending_submissions "1주차_파이썬기초"
```

### AI 채점 관리
```bash
# AI 채점 기준 설정
/set_grading_criteria assignment_id criteria.json

# 수동 재채점
/regrade_submission submission_id

# 채점 통계
/grading_stats assignment_id
```

---

## 📊 모니터링

### 시스템 상태 모니터링
```bash
# 시스템 전체 상태
/system_status

# 서버 리소스 사용량
/server_stats

# API 사용량 통계
/api_usage_stats
```

### 사용자 활동 모니터링
```bash
# 실시간 활동 로그
/activity_log 50  # 최근 50개 활동

# 사용자별 활동 통계
/user_activity_stats user_id

# 기능별 사용 통계
/feature_usage_stats
```

### 에러 모니터링
```bash
# 에러 로그 확인
/error_log 24h  # 최근 24시간 에러

# 에러 통계
/error_stats

# 크리티컬 에러 알림 설정
/set_error_alert critical
```

---

## 🛠️ 문제해결

### 일반적인 문제들

#### 1. 구글 드라이브 연결 문제
```bash
# 전체 사용자 드라이브 상태 확인
/check_all_drives

# 문제가 있는 사용자 찾기
/find_drive_issues

# 대량 드라이브 재연결
/bulk_reconnect_drives
```

#### 2. AI 응답 지연 문제
```bash
# AI 응답 시간 통계
/ai_response_stats

# 모델별 성능 비교
/model_performance_compare

# 모델 로드 밸런싱 조정
/adjust_load_balancing
```

#### 3. 과제 제출 문제
```bash
# 제출 실패 로그
/submission_failures

# 파일 업로드 문제 진단
/diagnose_upload_issues user_id

# 수동 과제 등록
/manual_submit user_id assignment_id file_id
```

### 긴급 상황 대응

#### 시스템 과부하
```bash
# 긴급 모드 활성화 (기능 제한)
/emergency_mode on

# 사용자 접속 제한
/limit_concurrent_users 50

# 리소스 집약적 기능 비활성화
/disable_feature web_search
```

#### 데이터 백업 및 복구
```bash
# 전체 데이터 백업
/backup_all_data

# 특정 사용자 데이터 백업
/backup_user_data user_id

# 데이터 복구
/restore_data backup_file_id
```

---

## 🔧 유지보수

### 정기 점검 작업
```bash
# 주간 점검 스크립트 실행
/weekly_maintenance

# 월간 통계 생성
/generate_monthly_report

# 사용자 데이터 정리
/cleanup_inactive_users 90  # 90일 미사용 계정
```

### 성능 최적화
```bash
# 캐시 정리
/clear_cache

# 데이터베이스 최적화
/optimize_database

# 로그 파일 정리
/cleanup_logs 30  # 30일 이상 된 로그 삭제
```

### 업데이트 관리
```bash
# 봇 버전 확인
/version

# 업데이트 확인
/check_updates

# 점검 모드 설정
/maintenance_mode on "시스템 업데이트 중"
```

---

## 📈 분석 및 리포팅

### 학습 분석
```bash
# 학습 진도 분석
/learning_progress_analysis

# 과제 완료율 통계
/assignment_completion_stats

# 학생 참여도 분석
/engagement_analysis
```

### 시스템 사용 분석
```bash
# 기능별 사용 빈도
/feature_usage_frequency

# 피크 시간대 분석
/peak_usage_analysis

# 지역별 사용 통계
/regional_usage_stats
```

### 리포트 생성
```bash
# 주간 리포트 생성
/generate_weekly_report

# 월간 리포트 생성
/generate_monthly_report

# 커스텀 리포트 생성
/generate_custom_report start_date end_date
```

---

## 🚨 알림 및 경고 설정

### 시스템 알림 설정
```bash
# 에러 임계값 설정
/set_alert_threshold error_rate 5%

# 사용량 알림 설정
/set_quota_alert 90%  # 90% 도달 시 알림

# 서버 리소스 알림
/set_resource_alert memory 80%
```

### 관리자 알림 채널
```bash
# 알림 채널 설정
/set_admin_channel @admin_alerts

# 긴급 알림 설정
/set_emergency_contact @admin_emergency

# 알림 레벨 설정
/set_alert_level critical
```

---

## 📞 지원 및 연락처

### 기술 지원
- 🔧 **시스템 개발팀**: dev@farmsolar.co.kr
- 📊 **데이터 분석팀**: analytics@farmsolar.co.kr
- 🚨 **긴급 상황**: emergency@farmsolar.co.kr

### 관리자 커뮤니티
- 💬 **관리자 텔레그램 그룹**: @FarmSolar_Admins
- 📚 **관리자 위키**: wiki.farmsolar.co.kr
- 🎓 **관리자 교육**: training.farmsolar.co.kr

---

## 📝 체크리스트

### 일일 점검 체크리스트
- [ ] 시스템 상태 확인 (`/system_status`)
- [ ] 에러 로그 확인 (`/error_log 24h`)
- [ ] API 사용량 확인 (`/api_usage_stats`)
- [ ] 학생 활동 확인 (`/activity_log 50`)
- [ ] 과제 제출 현황 확인 (`/submission_status`)

### 주간 점검 체크리스트
- [ ] 전체 데이터 백업 (`/backup_all_data`)
- [ ] 성능 통계 분석 (`/weekly_maintenance`)
- [ ] 사용자 피드백 검토
- [ ] 시스템 업데이트 확인 (`/check_updates`)
- [ ] 주간 리포트 생성 (`/generate_weekly_report`)

### 월간 점검 체크리스트
- [ ] 월간 통계 생성 (`/generate_monthly_report`)
- [ ] 비활성 사용자 정리 (`/cleanup_inactive_users 90`)
- [ ] 시스템 최적화 (`/optimize_database`)
- [ ] 보안 점검
- [ ] 관리자 권한 검토

---

*이 가이드는 AI_Solarbot v2.0 관리자 기능을 기준으로 작성되었습니다. 최신 업데이트는 `/admin_help` 명령어로 확인하세요.* 