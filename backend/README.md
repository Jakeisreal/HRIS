# Backend API

Flask + SQLite 기반의 HR Talent Support API (v2.0)입니다.

## 실행

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.app
```

기본 주소는 `http://127.0.0.1:5000`입니다.

## 주요 기능

### 보안
- **Bearer Token 인증**: 모든 후보자/템플릿 엔드포인트에서 Bearer token 필수
- **세션 TTL**: 기본 8시간 (환경변수 `HRIS_AUTH_SESSION_TTL_SECONDS`로 설정)
- **CORS 검증**: 환경변수 `HRIS_CORS_ORIGIN`으로 허용 원점 제한
- **파일 업로드 검증**: 크기, 확장자(.xlsx), ZIP 매직 바이트 검증

### 환경변수
- `HRIS_CORS_ORIGIN`: CORS 허용 원점 (필수, 프로덕션에서 누락 시 RuntimeError)
- `HRIS_AUTH_SESSION_TTL_SECONDS`: 세션 TTL (기본: 28800초 = 8시간)
- `HRIS_MAX_UPLOAD_BYTES`: 파일 업로드 제한 (기본: 10485760 = 10MB)
- `HRIS_DEMO_PASSWORD`: 데모 계정 비밀번호 (기본: `password`)

## 주요 API

### 인증
- `POST /api/auth/login`: 로그인 및 bearer token 발급
- `GET /api/auth/me`: 현재 로그인 사용자 확인
- `POST /api/auth/logout`: 세션 토큰 폐기

### 후보자 관리 (Bearer token 필수)
- `GET /api/candidates`: 저장된 후보자 목록 조회
- `POST /api/candidates/upload`: 후보자 Excel 업로드 (hr 역할만)
- `POST /api/upload-runs/<run_id>/rollback`: 업로드 롤백 및 데이터 원상복구

### 템플릿 관리 (Bearer token 필수)
- `GET /api/templates`: 사용자가 조회 가능한 템플릿 목록
- `POST /api/templates`: 개인 템플릿 생성 (hr 역할만)
- `PUT /api/templates/<id>`: 템플릿 수정 (hr 역할만)
- `POST /api/templates/<id>/share`: 인사팀 공유로 전환 (hr 역할만)
- `POST /api/templates/<id>/unshare`: 개인용으로 전환 (hr 역할만)
- `DELETE /api/templates/<id>`: 템플릿 삭제 (hr 역할만)

### 감사 로그 (hr 역할 필수, Bearer token 필수)
- `GET /api/audit-logs`: 감사 로그 조회
  - 쿼리 파라미터: `from` (ISO 날짜), `to` (ISO 날짜), `user` (사번), `risk` (위험도)
- `GET /api/audit-logs/export`: 감사 로그 CSV 다운로드

## 테스트 계정

- 인사담당자: `E24017` / `password` (역할: hr)
- 팀장/조회자: `E90001` / `password` (역할: viewer)

## Excel 업로드

### 요청 형식
- 메서드: `POST`
- URL: `/api/candidates/upload`
- 헤더: `Authorization: Bearer <token>`
- 바디: `multipart/form-data`
  - `file`: .xlsx 파일 (필수)
  - `dry_run`: `true` (선택, DB 저장 없이 검증만)

### 응답
신규, 변경, 중복, 오류 건수와 함께 변경 행의 필드별 이전/신규 값이 포함됩니다.

### 필수 Excel 컬럼
- `사번` 또는 `employee_id`
- `이름` 또는 `name`

### 선택 컬럼
부서, 직군, 직위, 등급, 입사일, 근무지, 이메일, 근속, 평가, 최근 3년 평가, 리더십, 어학, 어학종류, 해외경험, 해외국가, 해외유형, 자격증, 주재원 적합도, 팀장 적합도, 후보목적

업로드 결과는 사번 기준으로 신규, 변경, 중복 건수를 계산합니다. 변경 행은 필드별 이전 값과 신규 값을 `upload_changes` 테이블에 기록합니다.

## 감사 로그

### 기록되는 이벤트
- 로그인 성공/실패
- 후보자 목록 조회
- 업로드 실행/검증
- 권한 차단

### 필터 지원
- 기간 필터 (from, to)
- 사용자 필터 (user)
- 위험도 필터 (risk)

### CSV 내보내기
`GET /api/audit-logs/export`로 현재 필터 조건에 맞는 모든 감사 로그를 CSV 형식으로 다운로드합니다.

## 테스트

```bash
python -m pytest tests/ -v
```

14개의 테스트 케이스:
- 인증 (4개): 로그인, 사용자 정보 조회, 업로드 권한, 후보자 목록 인증
- 감사 로그 (3개): 이벤트 기록, 권한 차단, 필터 및 내보내기
- 템플릿 관리 (4개): 기본 템플릿, 생성/공유, 권한 검증, 공유 취소/삭제
- 파일 업로드 (1개): 업로드 및 변경 추적
- 파일 파싱 (2개): 필수값 검증, 유효한 행 파싱
