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

## 5. 현재 버전의 한계

현재 GitHub Pages 배포 버전은 프론트엔드 프로토타입입니다.

- 데이터는 Mock Data입니다.
- 실제 로그인 인증은 구현되어 있지 않습니다.
- 엑셀 업로드 API 초안은 `backend/`에 추가되어 있으나, 배포된 GitHub Pages 화면에는 아직 연결되어 있지 않습니다.
- 감사 로그는 예시 데이터입니다.
- 실제 업무 운영에는 Flask API 서버 배포와 프론트엔드 API 연동이 필요합니다.

## 6. 백엔드 API 초안

```bash
pip install -r requirements.txt
python -m backend.app
```

기본 API 주소는 `http://127.0.0.1:5000`입니다.

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/candidates`
- `POST /api/candidates/upload`

데모 계정은 서버 시작 시 자동 생성됩니다.

- 인사담당자: `E24017` / `password`
- 팀장/조회자: `E90001` / `password`

후보자 Excel 업로드는 로그인 후 발급된 bearer token이 필요하며, `hr` 역할만 실행할 수 있습니다. `.xlsx` 파일을 `multipart/form-data`의 `file` 필드로 전송합니다. `dry_run=true`를 사용하면 DB 저장 없이 검증 결과만 확인합니다. 업로드 결과에는 신규, 변경, 중복, 오류 건수가 포함되며 변경 행은 필드별 변경 이력으로 저장됩니다.

프론트엔드 업로드 화면은 `VITE_API_BASE_URL`이 설정된 경우 로그인 API를 호출하고, 발급된 token으로 `POST /api/candidates/upload`와 `GET /api/candidates`를 호출합니다. GitHub Pages처럼 API 주소가 없는 배포에서는 기존 Mock Data 화면을 유지합니다.

## 7. 권장 후속 개발

```text
React Frontend
  ↓ API 호출
Flask Backend
  ↓
SQLite 또는 PostgreSQL
```

우선순위는 다음과 같습니다.

1. 감사 로그 저장 API
2. 템플릿 저장/공유 API
3. 업로드 롤백/승인 흐름
