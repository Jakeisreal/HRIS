# Backend API

Flask + SQLite 기반의 HR Talent Support API 초안입니다.

## 실행

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.app
```

기본 주소는 `http://127.0.0.1:5000`입니다.

## 주요 API

- `GET /api/health`: API 상태 확인
- `POST /api/auth/login`: 로그인 및 bearer token 발급
- `GET /api/auth/me`: 현재 로그인 사용자 확인
- `POST /api/auth/logout`: 세션 토큰 폐기
- `GET /api/candidates`: 저장된 후보자 목록 조회
- `POST /api/candidates/upload`: 후보자 Excel 업로드

데모 계정은 `E24017 / password`(인사담당자), `E90001 / password`(팀장/조회자)입니다.

업로드는 `hr` 역할 bearer token이 필요합니다. `multipart/form-data`의 `file` 필드로 `.xlsx` 파일을 받습니다. `dry_run=true`를 함께 보내면 DB 저장 없이 컬럼 매핑과 검증 결과만 반환합니다.

## 필수 Excel 컬럼

- `사번` 또는 `employee_id`
- `이름` 또는 `name`

선택 컬럼은 부서, 직군, 직위, 등급, 입사일, 근무지, 이메일, 근속, 평가, 최근 3년 평가, 리더십, 어학, 어학종류, 해외경험, 해외국가, 해외유형, 자격증, 주재원 적합도, 팀장 적합도, 후보목적입니다.

업로드 결과는 사번 기준으로 신규, 변경, 중복 건수를 계산합니다. 변경 행은 필드별 이전 값과 신규 값을 `upload_changes` 테이블에 기록합니다.
