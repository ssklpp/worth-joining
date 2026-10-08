# 트러블슈팅 기록

| 항목 | 내용 |
|---|---|
| 대상 | 팀 전원. 같은 문제를 두 번 조사하지 않기 위한 기록 |
| 규칙 | 에러 · 버그 · 환경 문제를 해결하면 이 문서에 항목을 추가하고, 해결 PR에 항목 번호를 적는다 |
| 상태 | 해결 · 우회 · 보류 |

---

## 목록

| # | 날짜 | 분류 | 문제 | 상태 | 관련 |
|---|---|---|---|---|---|
| [TS-001](#ts-001-windows에서-asyncmy-db-접속-실패-winerror-87) | 2026-10-08 | DB · 백엔드 | Windows에서 asyncmy DB 접속 실패 (`WinError 87`) | 해결 | #5 |
| [TS-002](#ts-002-alembicini-한글-주석으로-unicodedecodeerror) | 2026-10-08 | DB · 마이그레이션 | `alembic.ini` 한글 주석으로 `UnicodeDecodeError` | 해결 | #6 |
| [TS-003](#ts-003-uvicornexe-실행이-애플리케이션-제어-정책에-막힘) | 2026-10-08 | 로컬 환경 | `uvicorn.exe` 실행이 애플리케이션 제어 정책에 막힘 | 우회 | — |
| [TS-004](#ts-004-테스트가-없을-때-pytest-종료-코드-5) | 2026-10-08 | 테스트 | 테스트가 없을 때 `pytest` 종료 코드 5 | 해결 | #6 |
| [TS-005](#ts-005-github-actions-node-20-지원-종료--ubuntu-latest-변경-경고) | 2026-10-08 | CI | Node 20 지원 종료 · `ubuntu-latest` 변경 경고 | 해결 | #6 |
| [TS-006](#ts-006-git-설치-후에도-명령을-찾지-못함) | 2026-10-08 | 로컬 환경 | git 설치 후에도 `git`, `npx skills`가 git을 찾지 못함 | 해결 | — |
| [TS-007](#ts-007-headless-edge-스크린샷이-저장되지-않음) | 2026-10-08 | 문서 · 도구 | headless Edge 스크린샷이 저장되지 않음 | 해결 | — |
| [TS-008](#ts-008-claude-code가-pr-병합--보호-규칙-변경을-거부함) | 2026-10-08 | 협업 도구 | Claude Code가 PR 병합 · 보호 규칙 변경을 거부함 | 우회 | — |
| [TS-009](#ts-009-git-lf--crlf-변환-경고) | 2026-10-08 | Git | `LF will be replaced by CRLF` 경고 | 보류 | — |

---

## TS-001. Windows에서 asyncmy DB 접속 실패 (`WinError 87`)

- **증상:** 로컬에서 `/health`를 부르면 500. DB 접속 단계에서 실패한다.
  ```
  sqlalchemy.exc.OperationalError: (asyncmy.errors.OperationalError) (2003, "Can't connect to MySQL server on 'localhost' ([WinError 87] 매개 변수가 틀립니다)")
  ```
- **환경:** Windows 11, Python 3.12, asyncmy, MariaDB 11.4.13, `DB_SSL_VERIFY=false`
- **원인:** asyncmy는 접속 도중 소켓을 TLS로 전환한다. Windows 기본 이벤트 루프(`ProactorEventLoop`)에서는 이 전환이 `CreateIoCompletionPort` 단계에서 실패한다. MariaDB 11.4는 서버 TLS가 기본으로 켜져 있어 클라이언트가 TLS를 요청하면 이 경로를 탄다.
- **확인한 것:**
  - Selector 이벤트 루프 + TLS: 성공
  - Proactor 루프 + TLS 없음: 성공
  - Selector 루프는 앱 코드에서 바꿀 수 없다. uvicorn이 앱을 import하기 전에 루프를 만든다.
- **해결:** `app/core/db.py`의 `connect_args()`가 `DB_SSL_VERIFY=false`(로컬)면 TLS 없이, `true`(배포 · Linux)면 인증서를 검증하는 TLS로 접속한다. 로컬호스트 접속이라 평문이어도 위험이 없다. SPEC 3장에도 반영했다.
- **재발 방지:** 새 DB 접속 코드(파이프라인 pymysql 포함)는 `connect_args()`를 재사용한다.

## TS-002. `alembic.ini` 한글 주석으로 `UnicodeDecodeError`

- **증상:** Windows에서 `pytest` 또는 `alembic` 명령이 설정 파일을 읽다가 실패한다.
  ```
  UnicodeDecodeError: 'cp949' codec can't decode byte 0xec in position 2: illegal multibyte sequence
  ```
- **원인:** Alembic은 `configparser`로 `alembic.ini`를 읽고, Windows에서는 시스템 코드 페이지(cp949)를 쓴다. UTF-8 한글 주석을 cp949로 읽어 깨진다.
- **해결:** `alembic.ini`는 ASCII만 쓴다. 파일 첫 줄에 그 이유를 적어 두었다.
- **재발 방지:** Windows에서 `configparser`로 읽는 `.ini` 파일(`alembic.ini`, `setup.cfg` 등)에는 한글을 넣지 않는다.

## TS-003. `uvicorn.exe` 실행이 애플리케이션 제어 정책에 막힘

- **증상:** 가상환경의 실행 파일로 서버를 띄우면 거부된다.
  ```
  Start-Process : This command cannot be run due to the error: An Application Control policy has blocked this file.
  ```
- **원인:** PC의 Windows 애플리케이션 제어(WDAC 등) 정책이 `.venv\Scripts\*.exe` 런처를 막는다. 개인 PC 설정 문제라 팀원마다 다를 수 있다.
- **우회:** 모듈 실행으로 띄운다. 같은 방식으로 `python -m pytest`, `python -m alembic`도 쓸 수 있다.
  ```
  python -m uvicorn app.main:app --reload
  ```

## TS-004. 테스트가 없을 때 `pytest` 종료 코드 5

- **증상:** `pytest`가 `no tests ran`을 출력하고 종료 코드 5로 끝난다. CI에서는 실패로 처리된다.
- **원인:** pytest는 수집된 테스트가 0개면 종료 코드 5를 돌려준다.
- **해결:** Phase 0에서 스모크 테스트(`tests/api/test_health.py`)를 추가했다. 빈 테스트 폴더만 두고 CI를 켜지 않는다.

## TS-005. GitHub Actions Node 20 지원 종료 · `ubuntu-latest` 변경 경고

- **증상:** CI는 통과하지만 Annotations에 경고 2건이 나온다.
  ```
  Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-python@v5.
  The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026.
  ```
- **해결:** `actions/checkout@v5`, `actions/setup-python@v6`으로 올리고, 러너를 `ubuntu-24.04`로 고정했다. 10/19는 프로젝트 기간 중이라 환경이 중간에 바뀌지 않게 했다.
- **재발 방지:** 프로젝트가 끝난 뒤 러너 고정을 풀지 다시 정한다.

## TS-006. git 설치 후에도 명령을 찾지 못함

- **증상:** git을 설치했는데 VS Code 터미널에서 `git`을 찾지 못한다. `npx skills use ...`는 `spawn git ENOENT`로 실패한다.
- **원인:** VS Code(와 그 안의 터미널)는 시작할 때의 `PATH`를 계속 쓴다. 설치 프로그램이 바꾼 `PATH`가 반영되지 않는다. `gh` 설치 후에도 같다.
- **해결:** VS Code를 다시 시작한다. 바로 써야 하면 현재 PowerShell 세션의 `PATH`만 새로 읽는다.
  ```powershell
  $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
  ```

## TS-007. headless Edge 스크린샷이 저장되지 않음

- **증상:** README용 시안 캡처에서 `msedge --headless=new --screenshot=...`가 오류 없이 끝나지만 파일이 생기지 않는다.
- **원인:** 이미 실행 중인 Edge와 같은 프로필을 쓰려다 조용히 끝나는 것으로 보인다. 별도 사용자 데이터 폴더를 주면 저장된다.
- **해결:** `--user-data-dir=<임시 폴더>`를 함께 준다. headless 창의 최소 너비가 약 500px라 375~390px 모바일 캡처는 잘린다. 모바일 화면은 브라우저 개발자 도구나 Playwright로 캡처한다.
  ```
  msedge --headless=new --user-data-dir=<임시 폴더> --window-size=1440,900 --virtual-time-budget=3000 --screenshot=<출력.png> <파일 URL>
  ```

## TS-008. Claude Code가 PR 병합 · 보호 규칙 변경을 거부함

- **증상:** Claude Code에 PR 병합이나 ruleset 생성 · 변경을 맡기면 실행 전에 거부된다.
  ```
  Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Merge Without Review]
  ```
  같은 방식으로 `[CI Bypass]`, `[Permission Grant]`도 나왔다.
- **원인:** Claude Code 자동 모드는 리뷰 없는 병합과 저장소 권한 · 보호 설정 변경을 사람이 직접 할 일로 본다.
- **우회:** Claude는 브랜치 · 커밋 · PR까지만 만들고, 병합과 보호 규칙 변경은 사람이 GitHub 웹에서 한다(CLAUDE.md 팀 규칙). 꼭 맡겨야 하면 `/permissions`에서 해당 명령을 허용 규칙으로 추가한다.

## TS-009. git `LF → CRLF` 변환 경고

- **증상:** `git add` 때마다 경고가 나온다. 동작에는 영향이 없다.
  ```
  warning: in the working copy of 'app/core/db.py', LF will be replaced by CRLF the next time Git touches it
  ```
- **원인:** Windows git의 `core.autocrlf=true` 기본값. 저장소에는 LF로 들어가고 작업 폴더에서는 CRLF로 바뀐다.
- **상태:** 보류. 팀원 OS가 섞이면 줄 끝 차이로 diff가 커질 수 있다. 필요해지면 `.gitattributes`에 `* text=auto eol=lf`를 넣는다.

---

## 항목 추가 양식

```markdown
## TS-NNN. 한 줄 제목

- **증상:** 무엇이 어떻게 실패했는지. 오류 원문은 가장 중요한 한 줄만 코드 블록으로
- **환경:** OS, 버전, 관련 설정 (필요할 때만)
- **원인:** 왜 일어났는지
- **해결:** 무엇을 바꿨는지, 관련 PR · 파일
- **재발 방지:** 규칙 · 테스트 · 문서로 남긴 것 (있을 때만)
```

목록 표에도 한 줄 추가한다. 상태는 해결(원인 수정), 우회(원인은 그대로, 피해 가는 방법), 보류(영향이 작아 미룸) 중 하나다.
