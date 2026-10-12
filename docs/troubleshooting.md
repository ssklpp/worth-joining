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
| [TS-010](#ts-010-쌓은-pr이-앞-pr의-squash-merge-후-충돌) | 2026-10-12 | Git · 협업 | 쌓은 PR이 앞 PR의 squash merge 후 충돌 | 해결 | #12 |
| [TS-011](#ts-011-ci에서만-modulenotfounderror-no-module-named-tests) | 2026-10-12 | 테스트 · CI | CI에서만 `ModuleNotFoundError: No module named 'tests'` | 해결 | #14 |
| [TS-012](#ts-012-백필-중-한-달-core-적재가-10분-넘게-멈춤) | 2026-10-12 | DB · 성능 | 백필 중 한 달 core 적재가 10분 넘게 멈춤 | 해결 | #15 |
| [TS-013](#ts-013-to_ym에-from_ym-값이-들어감) | 2026-10-12 | API | `to_ym`에 `from_ym` 값이 들어감 | 해결 | #20 |
| [TS-014](#ts-014-locust-실행-시-gevent-dll-로드-실패) | 2026-10-12 | 환경 · Windows | locust 실행 시 gevent DLL 로드 실패 | 우회 | #21 |
| [TS-015](#ts-015-localhost-부하-측정에서-최대-응답이-약-2초) | 2026-10-12 | 환경 · Windows | localhost 부하 측정에서 최대 응답이 약 2초 | 우회 | #21 |

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

## TS-010. 쌓은 PR이 앞 PR의 squash merge 후 충돌

- **증상:** PR B를 PR A의 브랜치 위에 쌓아 두고 A를 먼저 병합하자, base가 `main`으로 바뀐 B에 "This branch has conflicts that must be resolved"가 뜬다. 충돌 파일은 A와 B가 함께 고친 파일(`CLAUDE.md`, `docs/06_architecture.md`)이다.
- **원인:** squash merge는 A의 커밋들을 `main`에 **새 커밋 하나**로 넣는다. B 브랜치에는 A의 원래 커밋이 그대로 남아 있어, git은 같은 줄을 두 커밋이 다르게 고친 것으로 본다.
- **해결:** B 브랜치에서 A의 원래 커밋을 빼고, B의 커밋만 최신 `main` 위로 옮긴 뒤 PR 브랜치를 덮어쓴다. `main`이 아니라 PR 브랜치를 덮어쓰므로 ruleset에 걸리지 않는다.
  ```
  git fetch
  git rebase --onto origin/main <A의 마지막 원래 커밋> <B 브랜치>
  git push --force-with-lease origin <B 브랜치>
  ```
  옮긴 뒤 `git diff origin/main HEAD`가 B 원래 커밋의 diff와 같은지 확인한다.
- **재발 방지:** 가능하면 PR을 쌓지 않고 앞 PR이 병합된 뒤 최신 `main`에서 브랜치를 만든다. 쌓아야 하면 A 병합 직후 B를 위 방법으로 옮긴다.

## TS-011. CI에서만 `ModuleNotFoundError: No module named 'tests'`

- **증상:** 로컬에서는 통과하는데 CI의 `pytest -v`가 테스트 수집 단계에서 실패한다.
  ```
  E   ModuleNotFoundError: No module named 'tests'
  ```
- **원인:** 테스트가 공용 도우미를 `from tests.nps_csv import ...`로 가져온다. 로컬은 `python -m pytest`로 실행해 현재 폴더가 `sys.path`에 들어가지만, CI는 `pytest`를 바로 실행해 저장소 루트가 `sys.path`에 없다.
- **해결:** `pyproject.toml`의 `[tool.pytest.ini_options]`에 `pythonpath = ["."]`를 넣었다. 실행 방식과 관계없이 루트를 `sys.path`에 넣는다.
- **재발 방지:** push 전에 `python -P -m pytest`로 돌린다. `-P`(Python 3.11+)는 현재 폴더를 `sys.path`에 넣지 않아 CI와 조건이 같다. 이 PC는 `pytest.exe`도 애플리케이션 제어에 막힌다(TS-003). 설정 없이 이 명령으로 같은 오류를 재현하고, 설정 후 통과를 확인했다.

## TS-012. 백필 중 한 달 core 적재가 10분 넘게 멈춤

- **증상:** `python -m pipeline.nps.load --all`에서 2025-08 ~ 2026-05는 달마다 약 11초였는데, 2026-06에서 `INSERT INTO workplace … SELECT`가 `Sending data` 상태로 8분 넘게 끝나지 않았다.
- **환경:** MariaDB 11.4.13, `raw_nps_workplace` 약 133만 행(10개월분), `company` 약 15만 행
- **원인:** `raw_nps_workplace`의 인덱스가 `snapshot_ym` 하나뿐이었다(카디널리티 9~13). 행이 늘면서 통계가 갱신되자 11.4 비용 기반 옵티마이저가 `company`를 먼저 읽고 `raw`를 회사마다 다시 훑는 계획을 고른 것으로 보인다. 같은 SELECT를 다른 세션에서 EXPLAIN하면 `raw` 전체 스캔(`ALL`) + `company` `eq_ref`로 나와, 계획이 통계에 따라 흔들린다는 점을 확인했다.
- **해결:** 마이그레이션 `0002`로 `ix_snapshot`을 `ix_snapshot_company (snapshot_ym, biz_no6, name_norm)`로 바꿨다. 월 조건과 회사 조인을 한 인덱스로 받는다. 멈춘 쿼리는 같은 계정으로 `KILL <id>`했다(`PROCESS` 권한이 없어도 자기 연결은 끊을 수 있다).
- **재발 방지:** 조인 키로 쓰는 raw · core 컬럼에는 처음부터 복합 인덱스를 둔다. 백필은 백그라운드로 돌리고 `ingestion_log`의 월별 소요 시간을 본다. 11.4 계획은 `EXPLAIN` 결과를 기준으로 삼는다(SPEC 5.3).

---

## TS-013. `to_ym`에 `from_ym` 값이 들어감

- **증상:** `GET /companies/{id}/trend?from_ym=202606`이 202606 ~ 202608이 아니라 202606 한 달만 돌려줬다. `to_ym`만 주면 무시됐다.
- **원인:** 두 파라미터가 모듈 상수 `YM = Query(None, ...)` 하나를 기본값으로 함께 썼다. FastAPI는 파라미터를 등록할 때 그 `FieldInfo`에 alias(파라미터 이름)를 써 넣으므로, 같은 객체를 공유한 `to_ym`도 쿼리 문자열의 `from_ym`을 읽었다.
- **해결:** `YM = Annotated[int | None, Query(...)]` 타입 별칭으로 바꾸고 `from_ym: YM = None, to_ym: YM = None`으로 썼다(`app/routers/companies.py`). `tests/api/test_companies.py::test_trend_filters_period`가 from만 · to만 주는 경우를 확인한다.
- **재발 방지:** `Query()` · `Path()` 객체를 여러 파라미터가 공유하지 않는다. 재사용하려면 `Annotated` 별칭으로 만든다.

---

## TS-014. locust 실행 시 gevent DLL 로드 실패

- **증상:** `python -m locust --version`이 바로 실패했다.
  ```
  ImportError: DLL load failed while importing _gevent_c_greenlet_primitives: 응용 프로그램 제어 정책에서 이 파일을 차단했습니다.
  ```
  `PURE_PYTHON=1`만 주면 이어서 `Couldn't parse TOML file: 'cp949' codec can't decode byte 0xeb`가 났다.
- **환경:** Windows 11, 애플리케이션 제어 정책(TS-003과 같은 원인), locust 2.46.7
- **원인:** 정책이 `.venv` 안의 gevent C 확장(`.pyd`)을 막는다. 순수 Python 구현으로 돌리면 locust가 `pyproject.toml`을 시스템 기본 인코딩(cp949)으로 읽다가 한글 주석에서 실패한다.
- **해결:** `PURE_PYTHON=1`(gevent 순수 Python 구현)과 `PYTHONUTF8=1`(UTF-8 모드)을 함께 준다. `greenlet`은 정책에 막히지 않았다. 실행 예는 `tests/perf/locustfile.py` 첫 부분에 있다.
- **재발 방지:** C 확장이 있는 개발 도구가 막히면 먼저 순수 Python 모드가 있는지 찾는다.

## TS-015. localhost 부하 측정에서 최대 응답이 약 2초

- **증상:** `--host http://localhost:8000`으로 locust를 돌리면 p95는 6ms인데 최대가 2,047 ~ 2,100ms로, 요청 종류마다 몇 건씩 튀었다.
- **원인:** Windows에서 `localhost`가 IPv6 `::1`로 먼저 풀린다. uvicorn은 `127.0.0.1`에만 열려 있어 새 연결마다 `::1` 연결 실패를 기다린 뒤 IPv4로 다시 붙는다. 튀는 건수가 사용자 수(연결 수)와 비슷했다.
- **해결:** 측정 대상을 `http://127.0.0.1:8000`으로 바꾸자 최대가 75ms가 됐다. 서버 성능 문제가 아니다.
- **재발 방지:** 로컬 성능 측정은 `127.0.0.1`을 쓴다(`tests/perf/locustfile.py`, `docs/explain.md` 2장).

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
