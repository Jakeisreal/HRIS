# Local Run Guide

Windows에서 로컬 백엔드와 프론트엔드를 가장 쉽게 실행하는 방법입니다.

## 1. 한 번에 실행

저장소 루트에서 아래 파일을 더블클릭합니다.

```text
start_all.bat
```

이 파일은 두 개의 창을 엽니다.

- `HRIS Backend`: Flask API 서버 (`http://127.0.0.1:5000`)
- `HRIS Frontend`: Vite 프론트엔드 서버 (`http://localhost:5173`)

첫 실행 시 자동으로 처리되는 항목입니다.

- `.env.example`을 복사해 `.env` 생성
- `.venv` Python 가상환경 생성
- `requirements.txt` Python 패키지 설치
- `node_modules`가 없으면 `npm install` 실행

## 2. 로그인 계정

백엔드 연동 상태에서는 아래 테스트 계정을 사용할 수 있습니다.

| 접속 유형 | 아이디 | 비밀번호 |
| --- | --- | --- |
| 인사담당자 | E24017 | password |
| 팀장/조회자 | E90001 | password |

아이디에 맞지 않는 접속 유형을 선택하면 로그인이 차단됩니다.

## 3. Excel 업로드

샘플 파일은 저장소 루트의 `template_candidate_data.xlsx`입니다.

1. 웹앱에서 `데이터 관리` 메뉴로 이동합니다.
2. `template_candidate_data.xlsx`를 업로드합니다.
3. 변경 감지 결과를 확인합니다.
4. 문제가 없으면 `반영`을 누릅니다.

샘플 파일을 다시 만들려면 아래 명령을 실행합니다.

```bash
python create_template.py
```

## 4. 서버 종료

열려 있는 `HRIS Backend`, `HRIS Frontend` 창에서 각각 `Ctrl+C`를 누른 뒤 창을 닫습니다.

## 5. 로그인에서 `Failed to fetch`가 보일 때

브라우저 주소가 아래 주소인지 먼저 확인합니다.

```text
http://localhost:5173
```

아래 주소는 로컬 테스트용으로 사용하지 않습니다.

```text
https://jakeisreal.github.io/HRIS/
http://192.168.x.x:5173
```

그 다음 `HRIS Backend` 창에 오류가 없는지 확인합니다. 백엔드가 정상이라면 아래 주소가 브라우저에서 열립니다.

```text
http://127.0.0.1:5000/api/health
```

## 6. 수동 실행

필요하면 백엔드와 프론트엔드를 따로 실행할 수 있습니다.

```text
start_backend.bat
start_frontend.bat
```
