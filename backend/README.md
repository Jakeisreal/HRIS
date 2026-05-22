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
- `GET /api/candidates`: 저장된 후보자 목록 조회
- `POST /api/candidates/upload`: 후보자 Excel 업로드

업로드는 `multipart/form-data`의 `file` 필드로 `.xlsx` 파일을 받습니다. `dry_run=true`를 함께 보내면 DB 저장 없이 컬럼 매핑과 검증 결과만 반환합니다.

## 필수 Excel 컬럼

- `사번` 또는 `employee_id`
- `이름` 또는 `name`

선택 컬럼은 부서, 직위, 근속, 평가, 리더십, 어학, 해외경험, 자격증, 주재원 적합도, 팀장 적합도, 후보목적입니다.
