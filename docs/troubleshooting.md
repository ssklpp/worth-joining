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
| [TS-016](#ts-016-전각-괄호-주가-정규화되지-않음) | 2026-10-12 | 데이터 · 정규화 | 전각 괄호 `（주）`가 정규화되지 않음 | 해결 | #23 |
| [TS-017](#ts-017-company-json-수집이-data-too-long-for-column-bizr_no로-중단) | 2026-10-12 | 데이터 · DART | company.json 수집이 `Data too long for column 'bizr_no'`로 중단 | 해결 | #24 |
| [TS-018](#ts-018-dart-재무의-순이익이-모두-비어-있음) | 2026-10-12 | 데이터 · DART | DART 재무의 순이익이 모두 비어 있음 | 해결 | #25 |
| [TS-019](#ts-019-vercel이-취약한-nextjs-배포를-거부함) | 2026-10-12 | 배포 · 보안 | Vercel이 취약한 Next.js 배포를 거부함 | 해결 | #30 |
| [TS-020](#ts-020-sql-파일-주석의-콜론이-바인드-파라미터로-읽힘) | 2026-10-12 | API · SQL | SQL 파일 주석의 콜론이 바인드 파라미터로 읽힘 | 해결 | #32 |
| [TS-021](#ts-021-pyproj-dll-로드-실패) | 2026-10-12 | 환경 · Windows | pyproj DLL 로드 실패 | 우회 | #33 |
| [TS-022](#ts-022-juso-좌표가-대량으로-좌표-없음으로-캐시됨) | 2026-10-12 | 데이터 · juso | juso 좌표가 대량으로 "좌표 없음"으로 캐시됨 | 해결 | #37 |
| [TS-023](#ts-023-마이그레이션이-중간에-실패해-테이블-하나만-남음lines-예약어) | 2026-10-13 | DB · MariaDB | 마이그레이션이 중간에 실패해 테이블 하나만 남음(`lines` 예약어) | 해결 | Phase 9 스키마 PR |
| [TS-024](#ts-024-마이그레이션-왕복-명령이-실패를-가려-0006-테이블이-지워짐) | 2026-10-13 | DB · 작업 실수 | 마이그레이션 왕복 명령이 실패를 가려 0006 테이블이 지워짐 | 해결 | Phase 9 스키마 PR |
| [TS-025](#ts-025-역세권-공간-조인이-몇-분씩-걸림) | 2026-10-13 | DB · 성능 | 역세권 공간 조인이 몇 분씩 걸림 | 해결 | Phase 9 q5 · q6 PR |
| [TS-026](#ts-026-역-시세-화면에서-역-위에-빈-회사-핀이-겹침) | 2026-10-15 | 웹 · 지도 | 역 시세 화면에서 역 위에 빈 회사 핀이 겹침 | 해결 | #80 |
| [TS-027](#ts-027-역-비교함에-없어진-역이-남으면-역-비교-화면이-계속-오류) | 2026-10-15 | 웹 · 상태 | 역 비교함에 없어진 역이 남으면 역 비교 화면이 계속 오류 | 해결 | #81 |
| [TS-028](#ts-028-역세권-750m-추이-집계가-10분을-넘김) | 2026-10-15 | DB · 성능 | 역세권 750m 추이 집계가 10분을 넘김 | 해결 | 역세권 반경 PR |
| [TS-029](#ts-029-로컬-개발-서버에서-csp가-네이버-지도를-막음) | 2026-10-16 | 웹 · 보안 | 로컬 개발 서버에서 CSP가 네이버 지도를 막음 | 해결 | #93 |
| [TS-030](#ts-030-개발-서버가-떠-있을-때-빌드하면-개발-화면이-깨짐) | 2026-10-16 | 웹 · 환경 | 개발 서버가 떠 있을 때 빌드하면 개발 화면이 깨짐 | 우회 | #91 |
| [TS-031](#ts-031-화면-테스트의-har-재생에-실패-응답이-섞임) | 2026-10-16 | 웹 · 테스트 | 화면 테스트의 HAR 재생에 실패 응답이 섞임 | 해결 | #91 |
| [TS-032](#ts-032-회사-핀-옆의-지하철역을-눌러도-열리지-않음) | 2026-10-16 | 웹 · 지도 | 회사 핀 옆의 지하철역을 눌러도 열리지 않음 | 해결 | 지도 클릭 PR |
| [TS-033](#ts-033-마곡역을-눌러도-열리지-않고-시세가-발산역과-같음) | 2026-10-16 | 데이터 · 역 | 마곡역을 눌러도 열리지 않고 시세가 발산역과 같음 | 해결 | 역 좌표 PR |

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

## TS-016. 전각 괄호 `（주）`가 정규화되지 않음

- **증상:** DART 매칭 결과를 살펴보다 "（주）골프존 → 골프존"이 정확 매칭이 아니라 유사 매칭(0.857)으로 연결된 것을 봤다. 국민연금 회사의 `name_norm`이 `주골프존`이었다.
- **원인:** 국민연금 원본 상호에 전각 괄호 `（주）`(U+FF08 · U+FF09)와 전각 영숫자가 섞여 있다. `normalize_name`의 `CORP_TOKENS`는 반각 `(주)`만 지우고, 전각 괄호는 `NON_WORD`가 괄호만 지워 `주`가 이름에 남았다. 서울 회사 159,048개 중 7,621개(4.8%)의 `name_norm`이 이 때문에 달랐고, 그중 13개는 같은 회사가 반각 · 전각 표기로 둘로 나뉘어 있었다.
- **해결:** `normalize_name`이 먼저 `unicodedata.normalize("NFKC", name)`을 적용한다(SPEC 6장 함수도 수정). `tests/unit/test_normalize.py`에 전각 괄호 · 전각 영문 사례를 넣었다. 로컬 DB는 국민연금 테이블과 mart를 비우고 13개월을 다시 적재했다(회사 159,035개, 품질 검사 모두 통과). `dart_corp.corp_name_norm`은 10행이 바뀌어 같은 함수로 다시 계산했다.
- **재발 방지:** 외부 문자열을 키로 쓰기 전에는 NFKC를 거친다. 정규화 규칙을 바꾸면 회사 식별 키가 바뀌므로 raw부터 다시 적재하고 DB 덤프도 새로 만든다.

---

## TS-017. company.json 수집이 `Data too long for column 'bizr_no'`로 중단

- **증상:** `python -m pipeline.dart.company_info`가 2,910건을 받은 뒤 멈췄다.
  ```
  sqlalchemy.exc.DataError: (pymysql.err.DataError) (1406, "Data too long for column 'bizr_no' at row 1")
  ```
- **원인:** 홍콩 법인(`00694003`)의 `bizr_no`가 16자리 현지 번호였다. `dart_corp.bizr_no`는 `VARCHAR(10)`이다. 국내 사업자번호는 항상 10자리다.
- **해결:** 숫자만 남긴 뒤 10자리가 아니면 `bizr_no`를 비운다(`pipeline/dart/company_info.py` `parse`). 해외 번호는 국민연금 사업자번호와 비교할 수 없으므로 매칭에 쓰지 않는다. 받은 법인은 한 건씩 `fetched_at`을 남기므로 다시 실행하면 이어 받았다. `ingestion_log.message`에 API 키가 없는 것도 확인했다.
- **재발 방지:** 외부 응답 값은 컬럼 길이 · 형식을 확인한 뒤 저장한다. `tests/unit/test_dart_company_info.py`에 해외 번호 사례를 넣었다.

---

## TS-018. DART 재무의 순이익이 모두 비어 있음

- **증상:** fixture로 만든 재무 적재기를 실제 응답에 처음 돌려 보니 매출 · 영업이익 · 부채 · 자본은 들어오는데 `net_income`만 모두 NULL이었다.
- **원인:** 다중회사 주요계정 응답의 순이익 계정명이 문서 예시와 달리 `당기순이익(손실)`이었다. 적재기는 `당기순이익`과 완전히 같은 이름만 찾았다. fixture도 문서 예시대로 만들어 테스트가 통과했다.
- **해결:** 계정명의 괄호 앞까지만 비교한다(`pipeline/dart/financials.py` `parse`). fixture의 계정명을 실제 응답과 같게 바꿨다.
- **재발 방지:** 외부 API fixture는 공식 문서 예시가 아니라 실제 응답 한 건을 보고 만든다. 새 수집기는 전체 실행 전에 몇 건만 불러 필드를 확인한다.

---

## TS-019. Vercel이 취약한 Next.js 배포를 거부함

- **증상:** Vercel 첫 배포에서 `next build`는 성공했는데 마지막 단계에서 멈췄다.
  ```
  Vulnerable version of Next.js detected, please update immediately.
  ```
  설치 로그에도 `npm warn deprecated next@15.5.4: This version has a security vulnerability ... CVE-2025-66478`가 있었다.
- **원인:** `create-next-app@15.5.4`로 `web/`을 만들어 Next.js 15.5.4 · React 19.1.0이 들어갔다. 이 버전은 React Server Components 원격 코드 실행 취약점(CVE-2025-66478, React 쪽 CVE-2025-55182) 패치 전이라 Vercel이 배포를 막는다. 로컬 빌드와 CI는 경고 없이 통과했다.
- **해결:** 같은 15.5 계열의 패치 버전으로 올렸다. `next` 15.5.27, `react` · `react-dom` 19.1.9, `eslint-config-next` 15.5.27. 코드 변경 없이 lint · 타입 검사 · 빌드가 통과했다.
- **재발 방지:** 프레임워크를 새로 만들 때 버전을 고르기 전에 `npm view <패키지>@<계열> version`으로 최신 패치를 확인하고, `npm install` 로그의 `deprecated ... security vulnerability` 경고를 넘기지 않는다.

---

## TS-020. SQL 파일 주석의 콜론이 바인드 파라미터로 읽힘

- **증상:** `sql/q_compare.sql`을 `text()`로 실행하자 `/compare` 테스트가 실패했다.
  ```
  sqlalchemy.exc.InvalidRequestError: A value is required for bind parameter 'ids는'
  ```
- **원인:** SQL 주석에 `-- :ids는 회사 ID 목록`이라고 썼다. SQLAlchemy `text()`는 주석 안도 가리지 않고 `:이름`을 바인드 파라미터로 찾는데, 한글도 이름 글자로 보아 `ids는`이라는 파라미터가 하나 더 생겼다.
- **해결:** 주석에서 콜론을 뺐다("ids 파라미터는 …").
- **재발 방지:** `sql/` 파일 주석에는 `:이름` 형태를 쓰지 않는다. 파일 첫머리 주석에 이 규칙을 적었다.

---

## TS-021. pyproj DLL 로드 실패

- **증상:** `import pyproj`가 실패했다.
  ```
  ImportError: DLL load failed while importing _context: 응용 프로그램 제어 정책에서 이 파일을 차단했습니다.
  ```
- **환경:** Windows 11, 응용 프로그램 제어 정책(TS-003 · TS-014와 같은 원인), pyproj 3.8
- **원인:** 정책이 `.venv` 안의 pyproj C 확장(PROJ 라이브러리)을 막는다. gevent와 달리 순수 Python 모드가 없다. 좌표 변환은 로컬 파이프라인에서 돌리므로 CI만으로는 해결되지 않는다.
- **해결:** `pipeline/geocode/projection.py`는 pyproj를 먼저 쓰고, 불러올 수 없으면 같은 투영(EPSG:5179, GRS80 횡메르카토르)의 역변환 공식으로 계산한다. CI(pyproj 동작)에서 서울 범위 5개 점이 pyproj와 1e-7도(약 1cm) 안으로 같은지 `tests/unit/test_projection.py`가 확인한다. 로컬에서는 이 비교 테스트를 건너뛴다.
- **재발 방지:** C 확장 패키지를 새로 쓰기 전에 로컬에서 `import`부터 해 본다. 막히면 순수 Python 대안 · CI 검증 방식을 정한다.

---

## TS-022. juso 좌표가 대량으로 "좌표 없음"으로 캐시됨

- **증상:** 회사 좌표를 상위 200곳으로 시험하자 DART 본사 주소 성공이 27곳뿐이었다. 104곳이 `no_coordinate`, 56곳이 `ambiguous`로 `geocode_cache`에 실패 캐시됐다. 같은 주소를 손으로 부르면 좌표가 나왔다.
- **원인:** 두 가지였다.
  1. juso는 짧은 시간에 요청이 몰리면 `errorCode: E0007`("짧은 시간동안 다량의 주소검색 요청이 있습니다")을 정상 HTTP 200으로 준다. 지오코더는 `0`이 아닌 코드를 그 주소의 실패로 보고 캐시해, 일시적 제한이 영구 실패가 됐다. 연속 호출 25건 중 14건이 E0007이었다.
  2. "강남대로 382"를 찾으면 본 건물과 `382-2` 가로판매대가, "양천로 13"을 찾으면 "양천로14나길 13"이, 같은 건물이 건물명만 다르게 두 줄 나와 "정확히 1건" 조건에 걸렸다.
- **해결:**
  1. `Juso._call`이 E0007이면 1 · 2 · 4 · 8 · 16초 간격으로 다시 부르고, 끝내 풀리지 않으면 `ApiError`로 멈춘다(캐시하지 않는다). 호출 사이에 0.15초 간격을 둔다.
  2. `same_building(자치구, 도로명 또는 동, 본번-부번)`: 도로명과 번호가 정확히 같은 결과만 남기고, 남은 결과가 모두 같은 주소면 하나로 본다.
  3. 잘못 캐시된 실패 행을 지우고 다시 실행했다. 상위 200곳 성공 27 → 183곳(91.5%).
- **재발 방지:** 외부 API의 "본문 안 오류 코드"는 주소별 실패와 일시 오류를 나눠 다룬다. 실패를 캐시하는 코드는 대량 실행 전에 수십 건으로 성공률을 먼저 본다. `tests/unit/test_geocode_juso.py`에 E0007 재시도 · 비캐시 테스트가 있다.

---

## TS-023. 마이그레이션이 중간에 실패해 테이블 하나만 남음(`lines` 예약어)

- **증상:** `alembic upgrade head`(0007)가 `station`을 만들다 실패했다. 다시 실행하자 앞에서 만든 테이블 때문에 다른 오류가 났다.

  ```
  (1064, "You have an error in your SQL syntax; ... near 'lines        VARCHAR(300) NOT NULL, ..."
  (1050, "Table 'raw_rent_contract' already exists")
  ```
- **원인:** `LINES`는 MariaDB 예약어다(`LOAD DATA ... LINES TERMINATED BY`). 역의 노선 목록 컬럼을 `lines`로 지었다. 또 MariaDB의 DDL은 트랜잭션으로 되돌릴 수 없어서, 실패 전에 만든 `raw_rent_contract`가 남았고 `alembic_version`은 0006 그대로였다.
- **해결:** 컬럼을 `line_names`로 바꾸고, 남은 테이블을 손으로 지운 뒤 다시 적용했다. `upgrade` → `downgrade 0006` → `upgrade`로 왕복도 확인했다.
- **재발 방지:** 컬럼 이름은 예약어 목록(`LINES`, `KEY`, `RANGE`, `RANK`, `ROWS` 등)을 피한다. 새 마이그레이션은 로컬에서 up · down · up을 한 번 돌려 본다. 중간에 실패하면 `alembic current`와 `SHOW TABLES`로 남은 테이블을 먼저 확인한다. 왕복은 목표 버전을 적어서 한다(`alembic downgrade 0006`, TS-024).

---

## TS-024. 마이그레이션 왕복 명령이 실패를 가려 0006 테이블이 지워짐

- **증상:** TS-023 직후 로컬 DB의 `geocode_cache`가 6,946 + 약 4,300행에서 수백 행으로, `company_location`이 약 1.6만 곳에서 수십 곳으로 줄었다. 배포 DB는 그대로였다.
- **원인:** 0007을 시험하려고 `alembic upgrade head | tail && alembic downgrade -1 && alembic upgrade head`를 한 줄로 실행했다.
  1. 첫 `upgrade`는 TS-023으로 실패했다. 그러나 파이프의 종료 코드는 `tail`의 것(0)이라 `&&`가 다음 명령을 실행했다.
  2. DB는 아직 0006이었으므로 `downgrade -1`이 **0006을 되돌려** `company_location` · `geocode_cache`를 DROP했다.
  3. 다음 `upgrade`가 두 테이블을 빈 채로 다시 만들었다.
- **해결:** Railway DB(0006, 오늘 반영한 본사 · 상호 좌표)에서 두 테이블을 데이터만(`mariadb-dump --no-create-info --replace`) 받아 로컬에 넣었다. `geocode_cache` 6,946행, `company_location` 본사 11,917 · 상호 44곳으로 돌아왔다. 그사이 지워진 도로 · 동 좌표 약 4,300건은 수집을 한 번 더 돌려 다시 받는다.
- **재발 방지:**
  - 마이그레이션 왕복은 상대 지정(`-1`) 대신 목표 버전을 적는다: `alembic downgrade 0006`. 실패하면 그 자리에서 멈춘다.
  - DB를 지우는 명령(downgrade · DROP · TRUNCATE)은 다른 명령과 한 줄로 잇지 않고, 앞 단계의 `alembic current`를 확인한 뒤 실행한다.
  - 파이프로 출력을 줄이면 앞 명령의 실패가 사라진다. 실패 여부가 중요한 명령은 파이프 없이 실행하거나 `set -o pipefail`을 쓴다.
  - 큰 수집을 돌리는 동안에는 로컬 DB 스키마를 바꾸지 않는다. 필요하면 테스트 DB에서 먼저 확인한다.

---

## TS-025. 역세권 공간 조인이 몇 분씩 걸림

- **증상:** q5 · q6를 붙인 `python -m pipeline.refresh_mart`가 10분을 넘겼다(전에는 23초). q5는 기간 하나에 150 ~ 320초, q6는 회사-역 쌍 만들기에만 284초가 걸렸다.
- **원인:**
  1. q5: 역 JOIN 건물(`MBRContains(ST_Buffer)`)을 윈도 함수가 있는 파생 테이블 안에 두자, MariaDB 11.4가 건물 공간 인덱스 대신 조인 버퍼(BNL)를 골라 역 × 건물 2,200만 쌍을 모두 비교했다. 같은 조인을 단순 SELECT로 쓰면 `Range checked for each record`로 1초 안에 끝난다. `STRAIGHT_JOIN` · `FORCE INDEX` · `join_cache_level = 0`으로도 바뀌지 않았다.
  2. q6: `company_location`은 숫자 좌표 열이라 공간 인덱스가 없다. 회사마다 `POINT` · `ST_Buffer`를 만드는 비용이 12.6만 번 들었다.
- **해결:** q5는 역-건물 쌍을 임시 테이블에 먼저 넣고(q5a) 그 쌍으로 백분위를 낸다. q6는 역을 바깥에 두고 회사 위도 · 경도 범위(약 1km 상자)로 거른 뒤 거리를 잰다. refresh_mart 전체 35초.
- **재발 방지:** 공간 조인은 윈도 함수 · 파생 테이블과 한 쿼리에 넣지 않는다. 공간 인덱스가 없는 좌표는 숫자 범위로 먼저 거른다(CLAUDE.md, SPEC 5.3). `tests/sql/test_station_rent.py`가 q5a EXPLAIN에 공간 인덱스 재확인 계획이 있는지 본다. 기록은 docs/explain.md 3장.

---

## TS-026. 역 시세 화면에서 역 위에 빈 회사 핀이 겹침

- **증상:** `/stations/[id]`를 열면 지도에서 그 역 표시 위에 역 이름만 있고 값이 빈 회사 핀이 하나 더 그려졌다.
- **원인:** 역 시세 화면은 지도를 역으로 옮기려고 회사 상세와 같은 `select()`를 쓰고, 회사 id와 겹치지 않게 역 id를 음수로 넘긴다. `MapPane`에는 "상세에서 연 회사가 지금 핀 목록에 없으면 핀을 더한다"는 규칙이 있는데, 음수 id는 회사 목록에 있을 수 없어 늘 핀이 추가됐다.
- **해결:** `selected.id < 0`(역)이면 회사 핀을 더하지 않고, 그 역 표시를 확대와 관계없이 강조한다. 역 표시의 "(비교함에 담음)" 안내는 강조(`selected`)와 나눠 `boxed`일 때만 붙인다(#80, `web/app/(explore)/MapPane.tsx`, `web/components/map/NaverMap.tsx`).
- **재발 방지:** `Selected`를 회사가 아닌 것에 쓸 때는 `MapPane`의 선택 핀 규칙을 함께 확인한다. 음수 id는 역이라는 약속을 `MapPane` 주석에 적었다.

---

## TS-027. 역 비교함에 없어진 역이 남으면 역 비교 화면이 계속 오류

- **증상:** 역 비교함(브라우저 저장소)에 지금 DB에 없는 역 id가 있으면 `/stations/compare`가 오류 상자만 보였다. "다시 시도"를 눌러도 같았고 "역 비교함 비우기"로만 풀렸다. 역을 빼거나 기간 버튼을 누를 때마다 표 전체가 로딩 상자로 깜박이기도 했다.
- **원인:** 역마다 부르는 `/stations/{id}/rent`를 `Promise.all`로 묶어, 한 역의 404가 전체 실패가 됐다. 역 id는 `pipeline.stations.load`로 다시 적재하면 바뀔 수 있는데, 브라우저에 담긴 id는 그대로 남는다. 깜박임은 다시 부를 때마다 상태를 `loading`으로 되돌려서였다.
- **해결:** `Promise.allSettled`로 바꾸고 404 · 422인 역은 비교함에서 뺀 뒤 나머지만 보여 준다. 다른 실패는 지금처럼 오류와 다시 시도. 다시 부르는 동안에는 앞 결과를 두고 뺀 역만 바로 지운다. effect에서 쓰도록 비교함의 `add` · `remove` · `clear`를 렌더마다 같은 함수로 바꿨다(#81, `web/components/compare/StationCompareView.tsx`, `web/lib/compare.ts`).
- **재발 방지:** 브라우저 저장소에 둔 id는 DB가 바뀌어도 남는다. 저장된 id로 여러 API를 부를 때는 없는 id 하나가 화면 전체를 막지 않게 한다.

---

## TS-028. 역세권 750m 추이 집계가 10분을 넘김

- **증상:** 반경 750m를 더한 뒤 `python -m pipeline.refresh_mart`가 10분을 넘겼다. 프로세스 목록에서 q5t가 `Removing duplicates` 상태로 500초 넘게 머물렀다. 같은 쿼리가 500m는 0.6초, 600m는 0.7초였다.
- **원인:** q5 · q5t는 `PERCENTILE_CONT … OVER` + `DISTINCT`라 윈도 결과를 임시 테이블에 모은다. MariaDB 기본 `tmp_table_size` · `max_heap_table_size`(16MB)를 넘자 디스크 임시 테이블로 바뀌어 중복 제거가 수백 배 느려졌다. 행 수는 1.5배만 늘었지만 한도를 넘는 순간 시간이 급격히 뛴다. 실행 계획(EXPLAIN)은 그대로라 계획만 봐서는 보이지 않는다.
- **해결:** `refresh_mart`가 q5 전에 이 연결에서만 `SET SESSION tmp_table_size = 256MB, max_heap_table_size = 256MB`를 실행한다. 750m 한 번 0.9초, `refresh_mart` 전체 48초.
- **재발 방지:** 집계 대상이 늘어나는 변경(반경 · 지역 · 기간 추가) 뒤에는 `refresh_mart` 시간을 재고, 갑자기 느려지면 프로세스 목록의 상태(`Removing duplicates`, `Creating sort index`)와 임시 테이블 한도부터 본다. 성남 확장 때도 확인한다.

---

## TS-029. 로컬 개발 서버에서 CSP가 네이버 지도를 막음

- **증상:** CSP 헤더를 넣은 뒤 로컬(`http://localhost:3000`)에서 지도 타일과 스타일이 뜨지 않았다. 브라우저 콘솔에 `Refused to load the script ... because it violates the following Content Security Policy directive`가 찍혔다. 배포(https)에서는 정상이었다.
- **원인:** 허용 목록을 `https://*.naver.com`처럼 scheme을 붙여 적었다. 네이버 지도 SDK는 페이지와 같은 방식으로 리소스를 부르므로 로컬 http에서는 `http://` 주소로 요청했다. 또 로컬에서는 타일 · 스타일(JSONP)을 `*.naver.net`에서도 받는데 이 도메인이 목록에 없었다.
- **해결:** 네이버 호스트를 scheme 없이 `*.naver.com *.naver.net *.pstatic.net *.navercorp.com`으로 적었다. 개발 서버에만 `'unsafe-eval'`과 `ws:`(새로 고침)를 더한다(#93, `web/next.config.ts`).
- **재발 방지:** 화면 테스트(`liveTest`, `web/e2e/fixtures.ts`)가 브라우저 콘솔의 CSP 위반을 모아 하나라도 있으면 실패한다. CSP를 바꾸면 로컬 `npm run test:e2e:map`과 배포 화면을 함께 확인한다.

---

## TS-030. 개발 서버가 떠 있을 때 빌드하면 개발 화면이 깨짐

- **증상:** `npm run dev`가 떠 있는 상태에서 `npm run build`를 하자, 개발 서버 화면의 스타일이 모두 빠지고 CSS · JS 요청이 404가 됐다. 개발 서버를 다시 켜도 그대로였다.
- **원인:** 두 명령이 같은 `web/.next` 폴더를 쓴다. 빌드가 개발 서버의 결과물을 운영 빌드로 덮어써 개발 서버가 찾는 파일이 없어졌다.
- **해결:** 개발 서버를 끄고 `web/.next`를 지운 뒤 다시 켰다. 운영 빌드 확인은 다른 폴더(git worktree)에서 하고, 화면 테스트는 `E2E_PORT=3100`으로 그 빌드에 붙인다(#91, `web/README.md`).
- **재발 방지:** `web/README.md` 화면 테스트 절에 "개발 서버가 떠 있을 때 `npm run build`를 하지 않는다"를 적었다.

---

## TS-031. 화면 테스트의 HAR 재생에 실패 응답이 섞임

- **증상:** Playwright의 `routeFromHAR`로 API 응답을 녹화해 재생하자, 매번 통과하던 smoke 테스트가 가끔 오류 화면을 보며 실패했다.
- **원인:** HAR에는 녹화 중 화면이 끊은 요청(상태 -1)과 일부러 띄운 오류 화면의 500 응답도 들어갔다. 재생은 같은 주소의 기록 중 하나를 고르므로 이 실패 기록이 돌아올 때가 있었다. HAR 파일도 커서 PR에서 바뀐 곳을 보기 어려웠다.
- **해결:** HAR 대신 주소마다 JSON 파일 하나로 저장하는 고정 파일 방식으로 바꿨다. 녹화(`npm run test:e2e:record`)는 성공한 응답(5xx 제외)만 저장하고, 재생은 파일이 없는 요청을 끊는다(abort). 지도 범위마다 주소가 달라지는 `/map/companies`는 저장하지 않는다(#91, `web/e2e/fixtures.ts`, `web/e2e/api/`).
- **재발 방지:** 화면이 부르는 API나 응답 형식이 바뀌면 녹화를 다시 하고 바뀐 JSON을 코드와 같은 PR에 넣는다(`web/README.md`). 빠뜨리면 요청이 끊겨 테스트가 실패하므로 바로 알 수 있다.

---

## TS-032. 회사 핀 옆의 지하철역을 눌러도 열리지 않음

- **증상:** 성남을 더한 뒤 분당구에서 서현역 같은 역 이름표를 눌러도 역 시세 화면이 열리지 않았다. 역은 보이고 마우스를 올리면 모양도 바뀌는데 클릭만 안 됐다. 강남역처럼 근처에 회사 핀이 없는 역은 됐다. 화면 테스트에서는 `<div>…</div> intercepts pointer events`.
- **원인:** 회사 핀과 역 이름표는 지도 오버레이(`CustomOverlay`) 안의 버튼이고, 기준점 위 · 옆에 보이도록 CSS `transform`으로 옮겨 그린다. `transform`은 그리는 위치만 바꾸고 자리는 그대로라, 지도가 만든 감싸는 칸(div)은 버튼의 원래 크기로 기준점 오른쪽 아래에 남는다. 이 보이지 않는 칸이 회사 핀(zIndex 1)과 함께 역(zIndex 0) 위에 놓여 클릭을 가로챘다. 성남만의 문제가 아니고, 분당처럼 핀과 역이 가까운 곳에서 드러났다.
- **해결:** 핀 · 역 버튼을 감싼 칸은 `pointer-events: none`, 버튼만 `auto`로 했다(`web/components/map/map.module.css`, `div:has(> .pin)`). 감싼 칸의 빈 자리는 이제 지도 끌기도 막지 않는다.
- **재발 방지:** 지도 화면 테스트 `map-station-click`(분당구 → 서현역 클릭)을 더했다. 지도 위 오버레이를 `transform`으로 옮길 때는 감싸는 칸의 클릭을 같이 확인한다.

---

## TS-033. 마곡역을 눌러도 열리지 않고 시세가 발산역과 같음

- **증상:** 5호선을 따라 보면 송정역 · 발산역 이름표는 눌리는데 마곡역은 눌리지 않았다. 마곡역과 발산역의 시세(월 74.9만 원, 786건)도 똑같았다. 4호선 신용산역과 이촌역도 같았다.
- **원인:** 원본 역사정보 표준데이터(`railway_stations_20260630.xlsx`)에서 마곡역(공항대로 지하163)의 위도 · 경도가 발산역(공항대로 지하267) 값과 거의 같고(7m), 이촌역 4호선(서빙고로 지하83)은 신용산역 값과 같았다(14m). 주소는 맞는데 좌표만 다른 역 것이 들어갔다. 그래서 두 이름표가 한 자리에 겹쳐 아래 것이 눌리지 않았고, 역세권 시세도 같은 건물로 계산됐다. 적재기는 범위 밖 좌표만 주소로 고치고 있었다.
- **해결:** 이름이 다른 두 행이 150m 안에 있으면 둘 다 주소로 juso에서 찾아, 파일 좌표와 300m 넘게 다른 행만 주소 좌표로 고친다(`pipeline/stations/load.py`의 `fix_twins`). 마곡은 1,086m, 이촌 4호선은 897m 옮겨졌다. 이촌 4호선은 경원선 이촌과 400m 안이 되어 한 역("이촌", 4호선 · 경원선)으로 묶였다. 적재기가 이번 파일에 없는 역(옛 키 "이촌(4호선)" · "이촌(경원선)")을 지우게 했다. 역 327 → 326곳.
- **재발 방지:** 단위 테스트(겹친 좌표 중 틀린 쪽만 고침, 없어진 역 삭제). 역사정보 파일을 새로 받으면 적재 로그의 "역 좌표가 다른 역과 겹쳐 주소로 고쳤다"를 확인한다. 브라우저 역 비교함에 지워진 역 id가 남아 있어도 화면은 그 역만 빼고 보여 준다(TS-027).

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
