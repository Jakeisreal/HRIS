# HR Talent Support

웹 기반 인사 업무 지원 시스템 프로토타입입니다. 주재원 후보 및 차기 팀장 후보를 검색, 필터링, 상세 조회, 비교하고 데이터 업로드/감사 로그 흐름을 확인할 수 있는 React + Vite 앱입니다.

## 1. 포함 기능

- 로그인 / 역할 선택
- 홈 대시보드
- 후보자 목록 검색·필터
- 후보자 상세 대시보드
- 후보자 비교
- 템플릿 관리
- 엑셀 업로드/데이터 관리 화면
- 감사 로그 화면
- 접근 차단 화면
- GitHub Pages 자동 배포 워크플로우

## 2. 로컬 실행 방법

```bash
npm install
npm run dev
```

브라우저에서 표시되는 로컬 주소로 접속합니다.

백엔드 API와 연동해 Excel 업로드를 테스트하려면 `.env.example`을 참고해 `.env`를 만들고 프론트 서버를 다시 시작합니다.

```text
VITE_API_BASE_URL=http://127.0.0.1:5000
```

## 3. 빌드 방법

```bash
npm ci
npm run build
npm run preview
```

## 4. GitHub 업로드 방법

1. GitHub에서 새 저장소를 만듭니다.
   - 예시 저장소명: `HR-Talent-Support`
   - Public 저장소 권장
2. 이 ZIP 파일의 압축을 풉니다.
3. 압축을 푼 폴더 안의 파일 전체를 새 저장소 루트에 업로드합니다.
   - `package.json`이 저장소 루트에 있어야 합니다.
   - `src/`, `.github/`, `index.html`도 루트에 있어야 합니다.
4. `main` 브랜치에 commit 합니다.
5. GitHub 저장소에서 `Actions` 탭으로 이동해 배포 워크플로우가 성공하는지 확인합니다.
6. `Settings` → `Pages`에서 Source가 `GitHub Actions`로 설정되어 있는지 확인합니다.
7. 배포 완료 후 아래 형태의 주소로 접속합니다.

```text
https://<GitHub아이디>.github.io/<저장소명>/
```

## 5. 백엔드 API 보안 및 기능 개선사항 (v2.0)

### 5.1 보안 강화
- **Bearer Token 인증**: 모든 후보자/템플릿 엔드포인트에서 Bearer token 필수
- **세션 TTL (Time-To-Live)**: 기본 8시간 (환경변수 `HRIS_AUTH_SESSION_TTL_SECONDS`로 설정 가능)
- **CORS 원점 검증**: `HRIS_CORS_ORIGIN` 환경변수로 허용된 원점만 접근 가능
- **파일 업로드 검증**: 
  - 파일 크기 제한 (기본 10MB, `HRIS_MAX_UPLOAD_BYTES`로 설정)
  - 확장자 검증 (.xlsx만 허용)
  - ZIP 매직 바이트 검증 (PK\x03\x04)

### 5.2 새로운 API 엔드포인트
- `POST /api/upload-runs/<run_id>/rollback`: 업로드 롤백 (데이터 원상복구)
- `DELETE /api/templates/<id>`: 템플릿 삭제 (hr 역할만)
- `POST /api/templates/<id>/unshare`: 템플릿 공유 취소 (개인용으로 전환)
- `GET /api/audit-logs/export`: 감사 로그 CSV 내보내기

### 5.3 감사 로그 기능 확대
- 필터 지원: 기간(from/to), 사용자, 위험도
- CSV 내보내기 기능
- 모든 주요 작업(로그인, 후보자 조회, 템플릿 공유 등) 기록

### 5.4 GitHub Pages 배포 버전
현재 GitHub Pages 배포 버전은 프론트엔드 프로토타입입니다.

- 데이터는 Mock Data입니다.
- 백엔드 API와 연결하려면 `VITE_API_BASE_URL` 환경변수 설정이 필요합니다.
- 실제 운영 환경에는 Flask API 서버 배포와 프론트엔드 API 연동이 필요합니다.

## 6. 백엔드 API 초안

```bash
pip install -r requirements.txt
python -m backend.app
```

기본 API 주소는 `http://127.0.0.1:5000`입니다.

### 6.1 인증 관련
- `POST /api/auth/login`: 로그인 (Bearer token 발급)
- `GET /api/auth/me`: 현재 사용자 정보 조회
- `POST /api/auth/logout`: 로그아웃

### 6.2 후보자 관리 (Bearer token 필수)
- `GET /api/candidates`: 후보자 목록 조회
- `POST /api/candidates/upload`: Excel 파일 업로드 (hr 역할만)
- `POST /api/upload-runs/<run_id>/rollback`: 업로드 롤백

### 6.3 템플릿 관리 (Bearer token 필수)
- `GET /api/templates`: 템플릿 목록 조회
- `POST /api/templates`: 템플릿 생성 (hr 역할만)
- `PUT /api/templates/<id>`: 템플릿 수정 (hr 역할만)
- `POST /api/templates/<id>/share`: 템플릿 공유 (hr 역할만)
- `POST /api/templates/<id>/unshare`: 템플릿 공유 취소 (hr 역할만)
- `DELETE /api/templates/<id>`: 템플릿 삭제 (hr 역할만)

### 6.4 감사 로그 (hr 역할 필수)
- `GET /api/audit-logs`: 감사 로그 조회 (필터 지원: from, to, user, risk)
- `GET /api/audit-logs/export`: 감사 로그 CSV 내보내기

### 6.5 테스트 계정

데모 계정은 서버 시작 시 자동 생성됩니다.

- 인사담당자: `E24017` / `password` (역할: hr)
- 팀장/조회자: `E90001` / `password` (역할: viewer)

### 6.6 Excel 업로드

후보자 Excel 업로드는 로그인 후 발급된 bearer token이 필요하며, `hr` 역할만 실행할 수 있습니다.

**요청**:
- 메서드: `POST`
- URL: `/api/candidates/upload`
- 헤더: `Authorization: Bearer <token>`
- 바디: `multipart/form-data`
  - `file`: .xlsx 파일
  - `dry_run`: `true` (선택, DB 저장 없이 검증만)

**응답**:
- 신규, 변경, 중복, 오류 건수
- 변경된 행은 필드별 변경 이력 포함

### 6.7 환경변수 설정

- `HRIS_CORS_ORIGIN`: CORS 허용 원점 (필수, 예: `http://localhost:3000`)
- `HRIS_AUTH_SESSION_TTL_SECONDS`: 세션 TTL (기본: 28800, 8시간)
- `HRIS_MAX_UPLOAD_BYTES`: 파일 업로드 제한 (기본: 10485760, 10MB)
- `HRIS_DEMO_PASSWORD`: 데모 계정 비밀번호 (선택, 기본: `password`)

## 7. 백엔드 테스트

pytest를 사용하여 백엔드 API를 테스트합니다.

```bash
python -m pytest tests/ -v
```

### 7.1 테스트 커버리지

총 14개의 테스트 케이스:

**인증 관련 (4개)**
- 로그인 및 Token 발급
- 사용자 정보 조회
- 업로드 권한 검증
- 후보자 목록 조회 시 인증 필수

**감사 로그 (3개)**
- 로그인/후보자 조회 이벤트 기록
- 권한 없는 접근 차단 기록
- 필터 및 CSV 내보내기

**템플릿 관리 (4개)**
- 기본 템플릿 조회
- 템플릿 생성 및 공유
- 권한 검증
- 공유 취소 및 삭제

**파일 업로드 (1개)**
- 업로드 및 변경 사항 추적

### 7.2 GitHub Actions 자동 테스트

모든 commit 시 GitHub Actions에서 자동으로:
1. Python 3.11 환경 설정
2. pytest 실행 (14 tests 통과 필수)
3. npm 빌드 (통과 시에만)
4. GitHub Pages 배포

감사 로그는 로그인, 후보자 목록 조회, Excel 업로드 검증/반영, 권한 차단 이벤트를 DB에 저장합니다. `GET /api/audit-logs`는 `hr` 역할 token으로만 조회할 수 있습니다.

템플릿은 기본 제공, 인사팀 공유, 나만 보기 범위를 지원합니다. 조회자는 기본 제공/공유 템플릿만 볼 수 있고, 인사담당자는 개인 템플릿 저장과 공유 전환을 할 수 있습니다.

## 7. 권장 후속 개발

```text
React Frontend
  ↓ API 호출
Flask Backend
  ↓
SQLite 또는 PostgreSQL
```

우선순위는 다음과 같습니다.

1. 업로드 롤백/승인 흐름
2. 템플릿 수정/삭제 UI 고도화
