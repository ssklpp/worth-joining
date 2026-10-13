# 운영 절차 (runbook)

| 항목 | 내용 |
|---|---|
| 대상 | 배포 · 월 갱신을 맡은 사람 (팀장, T1 · T3) |
| 기준 | SPEC Phase 7, [06_architecture.md](./06_architecture.md) 4장 |
| 상태 | 첫 배포 완료 · 2026-10-12 (웹 https://web-chi-flax-46.vercel.app, API https://api-production-30254.up.railway.app) |

이 문서만 보고 배포를 처음부터 다시 만들 수 있어야 한다. 비밀번호 · 키는 이 문서와 저장소에 적지 않는다.

---

## 1. 구성

```
Vercel   web   (Next.js, 저장소의 web/)  ──HTTPS──▶  Railway api (Dockerfile, uvicorn)
                                                         │ 사설망 mariadb.railway.internal:3306
                                                         ▼
                                                   Railway mariadb (mariadb:11.4 + 볼륨)
```

- 데이터는 로컬에서 적재 · 검증한 DB를 덤프해 Railway에 복원한다. Railway에서 적재 작업(cron)은 돌리지 않는다(2026-10-12 결정, 6장).
- API는 읽기 전용이다. Railway DB에 쓰는 것은 복원 작업뿐이다.

## 2. 처음 배포

순서대로 한다. 앞 단계의 값(도메인, 비밀번호)을 뒤 단계에서 쓴다.

### 2.1 Railway: mariadb

1. Railway에서 새 프로젝트를 만들고 **Docker Image** 서비스를 추가한다. 이미지: `mariadb:11.4`, 서비스 이름: `mariadb`.
2. 볼륨을 붙인다. 마운트 경로: `/var/lib/mysql`.
3. 환경 변수(Variables):

   | 이름 | 값 |
   |---|---|
   | `MARIADB_ROOT_PASSWORD` | 새로 만든 긴 무작위 값 |
   | `MARIADB_DATABASE` | `worth_joining` |
   | `MARIADB_USER` | `wj` |
   | `MARIADB_PASSWORD` | 새로 만든 긴 무작위 값 (로컬 `.env`와 다르게) |

4. 복원하는 동안만 **TCP Proxy**를 켠다(Settings → Networking, 포트 `3306`). `xxxx.proxy.rlwy.net:12345`처럼 호스트와 포트가 한 줄로 나온다. 클라이언트에는 `-h xxxx.proxy.rlwy.net -P 12345`로 나눠 넣는다(합쳐 넣으면 `Unknown server host`).

### 2.2 DB 복원

팀 공유 드라이브의 최신 덤프(예: `worth_joining_20261012_phase5.zip`)를 풀고, 로컬 MariaDB 클라이언트로 TCP Proxy에 붙어 복원한다. PowerShell:

```powershell
& "C:\Program Files\MariaDB 11.4\bin\mariadb.exe" -h <프록시 호스트> -P <프록시 포트> -u wj -p `
  --skip-ssl-verify-server-cert --default-character-set=utf8mb4 worth_joining `
  -e "source worth_joining_20261012_phase5.sql"
```

- 비밀번호는 물어볼 때 `MARIADB_PASSWORD`를 넣는다. 740MB라 회선에 따라 수십 분 걸린다.
- 확인: 같은 접속으로 `SELECT version_num FROM alembic_version;` → 덤프의 `README.txt`에 적힌 버전, `SELECT COUNT(*) FROM mart_company_summary;` → README의 행 수.
- 끝나면 **TCP Proxy를 끈다.** API는 사설망으로 붙으므로 공개 포트가 필요 없다.

### 2.3 Railway: api

1. 같은 프로젝트에 **GitHub Repo** 서비스를 추가한다. 저장소 `ssklpp/worth-joining`, 브랜치 `main`, 서비스 이름 `api`. 루트의 `railway.json`이 `Dockerfile` 빌드와 `/health` 헬스 체크를 지정한다.
2. 환경 변수:

   | 이름 | 값 |
   |---|---|
   | `DATABASE_URL` | `mysql+asyncmy://wj:${{mariadb.MARIADB_PASSWORD}}@${{mariadb.RAILWAY_PRIVATE_DOMAIN}}:3306/worth_joining` |
   | `DATABASE_URL_SYNC` | `mysql+pymysql://wj:${{mariadb.MARIADB_PASSWORD}}@${{mariadb.RAILWAY_PRIVATE_DOMAIN}}:3306/worth_joining` |
   | `DB_SSL_VERIFY` | `false` (사설망 안이라 TLS 없이 붙는다. 6장 참고) |
   | `CORS_ORIGINS` | 처음엔 `["http://localhost:3000"]`, 2.4 뒤에 `["https://<웹 도메인>.vercel.app","http://localhost:3000"]`. 대괄호 · 큰따옴표까지 그대로, 주소 끝에 `/` 없이 |
   | `PORT` | `8080` (3에서 도메인에 넣는 포트와 같게. Dockerfile은 `PORT`를 읽는다) |

3. Settings → Networking에서 **Generate Domain**, 포트 `8080`(위 `PORT`와 같은 값). 지금 주소: `api-production-30254.up.railway.app`.
   - 서비스를 만든 직후에는 Networking 칸이 `Could not load public networking`으로 나올 수 있다. 새로고침하거나 첫 배포가 끝난 뒤 다시 연다.
   - DB 복원 전에 배포되면 헬스 체크가 실패한다. 복원 뒤 다시 배포(Redeploy)하면 된다.
4. 확인: `https://<api 도메인>/health` → `{"status":"ok","db":"ok","latest_nps_ym":202608}`. `/docs`에서 엔드포인트가 보이는지.

### 2.4 Vercel: web

1. Vercel에서 저장소를 Import한다. **Root Directory: `web`**, Framework: Next.js(자동). 지금 프로젝트 주소: `web-chi-flax-46.vercel.app`(프로젝트 이름을 바꾸면 주소도 바뀌므로 `CORS_ORIGINS`를 함께 고친다).
   - Vercel은 보안 취약 버전의 Next.js 배포를 거부한다(troubleshooting TS-019). 의존성을 올릴 때 패치 버전을 쓴다.
2. 환경 변수(Production · Preview 모두):
   - `NEXT_PUBLIC_API_BASE_URL` = `https://<api 도메인>` (끝에 `/` 없이)
   - `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` = NCP Maps Application의 Client ID(공개 값). NCP 콘솔 Application의 Web 서비스 URL에 `http://localhost:3000`과 웹 도메인을 등록해야 지도 인증이 된다. Client Secret은 쓰지 않는다
   - `NEXT_PUBLIC_*`는 빌드할 때 코드에 들어간다. 값을 바꾸면 **다시 배포**해야 한다.
3. 배포 후 나온 Production 도메인을 Railway `api`의 `CORS_ORIGINS`에 넣는다. api가 다시 시작된다.
   - Preview 배포 주소는 CORS에 없으므로 데이터가 안 보인다. 필요하면 그 주소를 배열에 더한다.

### 2.5 확인 (Phase 7 완료 조건)

- [ ] `https://<api>/health`가 `db: "ok"`, `latest_nps_ym`이 덤프 기준월
- [ ] 웹 첫 화면 하단에 데이터 기준월이 나온다(= 웹 → API → DB 연결)
- [ ] 회사 검색 → 상세 → "사람인에서 채용공고 보기"가 동작한다
- [ ] 없는 회사 주소(`/companies/999999999`)에 "회사를 찾을 수 없습니다"가 나온다
- [ ] 휴대폰에서 가로 스크롤이 없다(표 · 그래프 제외)

## 3. 환경 변수 전체

| 서비스 | 이름 | 비밀 | 설명 |
|---|---|---|---|
| mariadb | `MARIADB_ROOT_PASSWORD`, `MARIADB_PASSWORD` | 예 | Railway Variables에만 |
| mariadb | `MARIADB_DATABASE`, `MARIADB_USER` | 아니오 | `worth_joining`, `wj` |
| api | `DATABASE_URL`, `DATABASE_URL_SYNC` | 예(비밀번호 포함) | Railway 참조 변수로 mariadb 값을 가져온다 |
| api | `DB_SSL_VERIFY` | 아니오 | `false` |
| api | `CORS_ORIGINS` | 아니오 | JSON 배열 |
| web | `NEXT_PUBLIC_API_BASE_URL` | 아니오(공개) | api 공개 주소 |
| web | `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` | 아니오(공개) | 네이버 지도 Client ID. NCP 콘솔에 도메인 등록으로 보호 |

API 키(DART · 공공데이터포털 등)는 배포 서비스에 넣지 않는다. 수집은 로컬에서만 한다.

## 4. 월 갱신 (수동)

국민연금 월 파일은 자동으로 받을 수 없어(06 문서 R2) 매월 사람이 한다. 담당: T1, 확인: 팀장.

1. 공공데이터포털에서 새 달 파일을 받아 `data/raw/nps/all/`에 둔다. 파일 이름은 **자료 월**로 바꾼다(SPEC 4장: 파일 이름이 한 달 늦을 수 있다).
2. 로컬에서 적재 · 검증:
   ```bash
   python -m pipeline.nps.extract_seoul data/raw/nps/all/YYYYMM.csv
   python -m pipeline.nps.load --ym YYYYMM      # 품질 검사에 걸리면 failed로 멈춘다. 원인을 보고 고친다
   python -m pipeline.refresh_mart
   python -m pipeline.dart.company_info         # 새로 이름이 맞는 법인만 부른다(선택)
   python -m pipeline.dart.match
   python -m pipeline.geocode.company_location  # 새 회사 좌표. 본사 · 상호는 캐시, 도로 · 동은 파일로 계산
   python -m pipeline.refresh_mart              # 좌표가 바뀌었으면 회사 근처 역(q6)을 다시 만든다
   ```
   분기마다(4월 이후 첫 갱신 등) `python -m pipeline.dart.financials`도 실행한다.
   - 회사 좌표의 도로 · 동 중심은 `data/raw/juso/`의 주소정보누리집 서울 파일 두 개로 계산한다: "도로명주소 한글"(`rnaddrkor_seoul.txt`)과 "도로명주소 출입구"(`RNENTDATA_YYMM_11000.txt`, 가장 최근 YYMM을 쓴다). 둘 다 `.gitignore` 대상이라 각자 받는다. 새 도로가 많이 생기면(분기에 한 번 정도) 같은 달 파일 두 개를 다시 받아 바꾼다.
   - **전월세(분기 또는 필요할 때):** 서울 열린데이터광장 OA-21276에서 올해 CSV를 다시 받아 `data/raw/rent/seoul_rent_YYYY.csv`로 바꾸고, R-ONE 전월세전환율(서울 연립다세대, 월)을 `conversion_rate_seoul.csv`로 받는다. 그다음 `python -m pipeline.rent.seoul --as-of <받은 날>` → `python -m pipeline.rent.conversion` → `python -m pipeline.refresh_mart`. 보관 기간이 지난 달은 `python -m pipeline.rent.partitions --drop-before <기준월 - 23개월>`로 지운다. Open API 증분 수집과 자동 순환은 하지 않는다(decisions/007).
3. 로컬 API와 웹으로 회사 몇 곳을 열어 본다(기준월이 바뀌었는지, 추이에 새 달이 붙었는지).
4. 덤프를 만들어 공유 드라이브에 올린다(이름 `worth_joining_YYYYMMDD.zip`, zip 안에 행 수 · Alembic 버전을 적은 `README.txt`).
5. 2.1의 TCP Proxy를 켜고 2.2처럼 복원한 뒤 끈다. 복원하는 몇 분 동안은 API가 오류를 낼 수 있다. 사용자가 적은 시간에 한다.
   - **스키마 버전을 맞춘다.** main에 새 마이그레이션이 병합됐는데 배포 DB에 없으면 그 테이블을 읽는 API가 500을 낸다(2026-10-13 `/map/companies`, 배포 DB 0005 · 코드 0006). 복원한 뒤 `SELECT version_num FROM alembic_version`이 `python -m alembic heads`와 같은지 본다. 로컬 DB에서 만든 덤프면 같다
   - **일부 테이블만 반영할 때(2026-10-13 Phase 9):** 배포 API가 읽는 테이블만 데이터로 올려도 된다. `alembic upgrade <목표 버전>`을 Railway에 먼저 적용하고(TS-024: 목표 버전을 적는다), 로컬에서 `mariadb-dump --no-create-info --replace <테이블들>`로 받아 넣는다. 전월세는 `station` · `company_station` · `mart_station_rent` · `conversion_rate`만 올린다. raw · `rent_contract` · `building`은 집계용이라 배포 DB에는 비어 있다.
   - TCP Proxy가 연결은 되는데 MariaDB 응답이 없으면(`ERROR 2013 … reading initial communication packet`) 프록시를 껐다가 다시 켜고 새 주소를 `.env`에 넣는다(2026-10-13).
6. 2.5 확인 목록을 다시 본다. `/health`의 `latest_nps_ym`이 새 달이어야 한다.

### 다음 갱신 확인 계획

| 언제 | 할 일 | 담당 |
|---|---|---|
| 2026-11 둘째 주 | 공공데이터포털에 2026-09 자료가 올라왔는지 확인. 올라왔으면 위 절차로 갱신 | T1 |
| 갱신 직후 | `/health`의 `latest_nps_ym` = 202609, 품질 검사 결과(`ingestion_log`)를 PR이나 이슈에 기록 | T1 · 팀장 |
| 매월 반복 | 같은 주에 확인. 자동 수집 방법이 생기면 Railway cron으로 옮긴다(06 문서 R1 · R2) | T1 |

## 5. 백업

- 월 갱신 때 만든 덤프가 곧 백업이다. 공유 드라이브에 최근 3개를 둔다.
- Railway 볼륨이 망가지면 2.1(새 볼륨) → 2.2(최신 덤프 복원)로 되돌린다.

## 6. 결정과 이유

- **Railway에서 적재 cron을 돌리지 않는다(2026-10-12).** 국민연금 파일 자동 수집이 정해지지 않았고(R2), 적재 · 품질 검사를 로컬에서 보고 확인한 데이터만 올리는 편이 MVP 기간에 안전하다. SPEC Phase 7의 "다음 달 cron 실행 확인 계획"은 4장의 수동 갱신 계획으로 대신한다.
- **API ↔ DB는 TLS 없이 붙는다(`DB_SSL_VERIFY=false`).** 두 서비스가 Railway 사설망(`*.railway.internal`) 안에서만 통신하고 DB 포트는 공개하지 않는다. 06 문서 4장의 `DB_SSL_VERIFY=true`는 공개망으로 붙는 경우의 값이다.

## 7. 문제가 생기면

| 증상 | 볼 곳 |
|---|---|
| 웹은 뜨는데 데이터가 안 보이고 하단 기준월이 "확인하지 못함" | 브라우저 개발자 도구 콘솔의 CORS 오류 → `CORS_ORIGINS`에 웹 도메인이 정확히 있는지(끝 `/` 없이) |
| `/health`가 500 | api 로그의 DB 접속 오류 → `DATABASE_URL`, mariadb 서비스 상태 |
| api 배포가 헬스 체크에서 실패 | DB가 아직 복원되지 않았거나 mariadb가 꺼져 있다 |
| 특정 API만 500, 웹에는 "Failed to fetch" | 배포 DB에 그 API가 읽는 테이블이 없다(스키마 버전이 코드보다 낮다). 4장 5단계로 맞춘다. 500 응답에는 CORS 헤더가 없어 브라우저는 요청 실패로만 보인다 |
| api 로그에 `Can't connect` · `Connection refused` (사설 도메인) | 사설망 주소가 IPv6로 풀리는데 DB가 IPv4만 받는 경우다. mariadb 서비스의 시작 명령(Custom Start Command)에 `mariadbd --bind-address=::`를 넣고 다시 시작한다 |
| 그 밖의 에러 | [troubleshooting.md](./troubleshooting.md)에서 찾고, 해결하면 TS 항목을 추가한다 |
