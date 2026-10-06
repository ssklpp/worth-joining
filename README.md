# 다닐만한가 (Worth Joining)

> 공공데이터로 보는 회사 · 채용 · 주거비
> "이 회사, 다닐 만한가?"에 숫자로 답하는 구직자용 웹 서비스

![status](https://img.shields.io/badge/status-설계%20단계-lightgrey)
![python](https://img.shields.io/badge/Python-3.12-3776AB)
![fastapi](https://img.shields.io/badge/FastAPI-backend-009688)
![mariadb](https://img.shields.io/badge/MariaDB-10.11%20LTS-003545)
![nextjs](https://img.shields.io/badge/Next.js-frontend-000000)

국민연금 가입 사업장 데이터와 DART 공시로 회사의 **인원 추이 · 입퇴사율 · 추정 연봉**을 보여줍니다. 여기에 **채용공고**(사람인 API)와 **회사 근처 역세권 전월세 시세**를 연결해, 지원부터 출근 이후의 생활비까지 한 화면에서 판단할 수 있게 합니다.

LLM·RAG 같은 AI 기능 없이 **데이터 수집 → 정제 → DB 모델링 → SQL 분석 → API 제공**의 전 과정을 직접 구현하는 프로젝트입니다.

---

## 목차

- [왜 만들었나](#왜-만들었나)
- [주요 기능](#주요-기능)
- [이 서비스만의 차별점](#이-서비스만의-차별점)
- [시스템 구조](#시스템-구조)
- [기술 스택](#기술-스택)
- [데이터 출처](#데이터-출처)
- [핵심 지표 계산 방법](#핵심-지표-계산-방법)
- [API](#api)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [로드맵](#로드맵)
- [한계와 면책](#한계와-면책)

---

## 왜 만들었나

구직자가 회사를 판단할 때 쓰는 정보는 대부분 **채용공고**(회사가 쓴 글)와 **익명 리뷰**(개인 경험)입니다.

반면 국민연금공단은 사업장별 가입자 수, 신규 취득자, 상실자, 고지금액을 **매월 공개**하고, DART에는 재무제표가 있으며, 국토교통부는 전월세 실거래가를 공개합니다. 근거가 될 공식 데이터는 이미 있지만 그대로 쓰기는 어렵습니다.

| 공공데이터의 문제 | 이 프로젝트의 해결 |
|---|---|
| 한 달치 스냅샷이라 추이를 볼 수 없음 | 월별 파일을 누적 적재해 시계열로 만듦 |
| 사업장 단위라 회사 단위로 볼 수 없음 | 사업자번호 + 정규화 상호로 회사 단위 집계 |
| 고지금액을 연봉으로 바꾸려면 보험료율·상한을 알아야 함 | 기간별 기준표로 역산하고 한계를 함께 표시 |
| 국민연금, DART, 채용공고 사이에 공통 키가 없음 | 단계별 매칭 규칙과 매칭 신뢰도 기록 |
| 실거래가가 지번 단위라 "역 주변 시세"를 알 수 없음 | 주소 → 좌표 변환 후 역 반경 500m로 집계 |

---

## 주요 기능

### MVP

| 기능 | 설명 |
|---|---|
| 회사 검색 | 회사명, 사업자번호 앞 6자리, 업종으로 검색 |
| 인원 추이 | 월별 가입자 수 그래프와 12개월 증감률 |
| 입사율 · 퇴사율 | 월별 입퇴사 인원과 비율, 연간 퇴사율 |
| 추정 평균 연봉 | 고지금액 역산 추정치(하한)와 계산 방식 |
| 체력 요약 카드 | 성장 · 안정 · 급여의 **업종 내 백분위** |
| 채용공고 바로가기 | 사람인 검색 결과로 이동 (API 없이 동작) |

### MVP 이후

| 기능 | 설명 |
|---|---|
| 재무 지표 | DART 매출, 영업이익, 부채비율 |
| 회사 비교 | 최대 3곳의 추이를 지수(12개월 전 = 100)로 겹쳐 비교 |
| 지도 비교 | 지도에서 회사 핀을 눌러 요약 그래프 확인 |

### 확장 기능

<details>
<summary><b>역세권 전월세 (서울)</b></summary>

- 역 반경 500m, 전용 33㎡ 이하 원룸의 **월세 · 전세 시세**(중위값, p25~p75)
- 최근 **24개월 이내** 계약만 사용 (6 / 12 / 24개월 선택, 기본 12개월)
- 회사 대표 사업장에서 1km 안의 역 최대 3곳 연결
- **주거비 부담률** = 역세권 환산 월세 ÷ 추정 월급(세전), 범위로 표시

</details>

<details>
<summary><b>채용 정보 연계 (사람인 API)</b></summary>

- 회사별 진행 중 공고 수, 마감일, 제시 연봉, 원문 링크
- **채용 신호**: 공고 여부와 인원 추이 · 퇴사율을 겹쳐 "성장형 채용" / "결원 충원형 채용" 가능성 표시
- 공고 제시 연봉과 회사 추정 평균 연봉 · 업종 중위값 비교
- "현재 채용 중" 필터, 마감 임박 순 · 체력 점수 순 정렬

</details>

---

## 이 서비스만의 차별점

국민연금 데이터로 회사 연봉·인원을 보여주는 서비스는 이미 있습니다. 이 프로젝트는 아래에 집중합니다.

1. **회사와 생활을 한 화면에:** 회사 체력과 그 회사에 다닐 때의 주거비를 함께 봅니다.
2. **절대값보다 상대 위치:** "퇴사율 19%"가 아니라 "같은 업종 중 몇 번째인지"를 보여줍니다.
3. **채용의 성격까지:** 인원이 늘면서 뽑는지, 사람이 떠나서 메우는지 가능성을 보여줍니다.
4. **숫자의 한계를 숨기지 않음:** 추정 연봉은 하한, 표본이 적으면 "표본 부족"으로 표시합니다.
5. **바로 조회:** 회원가입 · 결제 없이 회사명만 검색하면 됩니다.

> 팀 분위기, 업무 강도, 직무별 연봉처럼 통계에 나타나지 않는 정보는 알 수 없습니다. 이 서비스는 리뷰를 대체하는 도구가 아니라 **숫자로 교차 확인하는 도구**입니다.

---

## 시스템 구조

```mermaid
flowchart LR
  subgraph Sources[데이터 출처]
    NPS[국민연금<br/>사업장 CSV]
    DART[OpenDART]
    RENT[국토부<br/>전월세 실거래가]
    STN[도시철도<br/>역사 표준데이터]
    JUSO[주소정보누리집<br/>좌표 API]
    SRM[사람인 API]
  end

  subgraph Pipeline[수집 파이프라인 - Python, APScheduler]
    COL[수집 · 정제<br/>멱등 적재]
  end

  subgraph DB[MariaDB 10.11]
    RAW[(raw)]
    CORE[(core<br/>정규화 테이블)]
    MART[(mart<br/>집계 테이블)]
  end

  API[FastAPI<br/>읽기 전용 REST]
  WEB[Next.js<br/>+ 카카오맵 또는 네이버 지도]

  NPS & DART & RENT & STN & JUSO & SRM --> COL
  COL --> RAW --> CORE --> MART
  MART --> API --> WEB
```

- **3계층 DB:** 원본을 `raw`에 보존하고, `core`에서 정규화하고, `mart`에 미리 집계합니다. API는 `mart`만 읽습니다.
- **멱등 적재:** 같은 달을 다시 넣어도 결과가 같도록 `INSERT ... ON DUPLICATE KEY UPDATE`와 해시 키를 씁니다.
- **월 단위 배치:** 수집 · 집계는 별도 프로세스에서 돌아가 API 응답 속도에 영향을 주지 않습니다.

---

## 기술 스택

| 영역 | 기술 | 용도 |
|---|---|---|
| 수집 · 가공 | Python 3.12, httpx, pandas, openpyxl | API 호출, CSV · XLSX 정제, 인코딩(CP949) 처리 |
| | rapidfuzz | 국민연금 · DART · 사람인 회사명 유사도 매칭 |
| | pyproj | 좌표계 변환 (UTM-K → WGS84 경위도) |
| | APScheduler | 월 1회 · 일 1회 배치 스케줄링 |
| DB | MariaDB 10.11 LTS (InnoDB) | 윈도 함수 · CTE, 파티셔닝, 생성 컬럼, SPATIAL 인덱스 |
| | Alembic | 스키마 마이그레이션 |
| 백엔드 | FastAPI, uvicorn, Pydantic v2 | REST API, 파라미터 검증, 자동 문서 |
| | SQLAlchemy 2.0 (async) + asyncmy | DB 연결. 통계 쿼리는 SQL을 직접 작성 |
| 프론트엔드 | Next.js, Recharts | 검색 · 상세 · 비교 화면, 그래프 |
| | 카카오맵 SDK 또는 네이버 지도 SDK (선택 예정) | 지도, 핀, 팝업 |
| 테스트 | pytest, testcontainers(MariaDB), locust | 단위 · SQL 회귀 · API · 성능 테스트 |
| 배포 | Railway, Vercel, GitHub Actions | API · 배치 · DB, 프론트엔드, CI |

---

## 데이터 출처

| 데이터 | 제공 기관 | 갱신 | 용도 |
|---|---|---|---|
| 국민연금 가입 사업장 내역 | 국민연금공단 (공공데이터포털) | 월 | 인원 추이, 입퇴사율, 추정 연봉 |
| OpenDART 고유번호 · 기업개황 · 주요계정 | 금융감독원 | 수시 | 회사 매칭, 재무 지표 |
| 연립다세대 · 오피스텔 전월세 실거래가 | 국토교통부 (공공데이터포털) | 월 | 역세권 전월세 시세 |
| 전국도시철도역사정보 표준데이터 | 국가철도공단 | 연 | 역 위치 |
| 도로명주소 검색 · 좌표제공 API | 행정안전부 주소정보누리집 | 수시 | 주소 → 좌표 (저장 허용) |
| 전월세전환율 | 한국부동산원 R-ONE | 월 | 보증금 → 월세 환산 |
| 법정동 코드 | 행정표준코드관리시스템 | 수시 | 시군구 코드 |
| 채용공고 검색 API | 사람인 | 일 1회 배치 | 채용 현황, 채용 신호 |

**이용 조건 메모**

- **좌표 저장:** 카카오 · 네이버 · 브이월드 지오코딩 결과는 실시간 사용만 허용되므로, **저장하는 좌표는 주소정보누리집에서만** 가져옵니다. 카카오 · 네이버 지도는 화면 표시에만 씁니다.
- **사람인 API:** 1일 500회 한도, 출처 표시 필수, 재판매 · 유료화 금지 조건을 따릅니다. 공고는 요약과 원문 링크만 표시하고 본문은 저장하지 않습니다.
- 모든 출처는 서비스 화면 하단과 `/meta/methodology`에 표시합니다.

---

## 핵심 지표 계산 방법

**추정 평균 연봉** (스냅샷 월 t)

```
추정 연봉 = 고지금액 ÷ 가입자 수 ÷ 보험료율(t) × 12
```

- 보험료율은 2025년까지 9%, 2026년 9.5%이고, 소득 상한은 매년 7월에 갱신됩니다. 두 값 모두 `nps_rate` 기준표로 관리합니다.
- 소득 상한 때문에 고연봉 회사일수록 **낮게 추정**됩니다. 화면에는 "하한 추정치"로 표시합니다.

**입사율 · 퇴사율**

```
입사율(t) = 신규 취득자(t) ÷ 가입자(t-1)
퇴사율(t) = 상실자(t) ÷ 가입자(t-1)
연간 퇴사율 = 최근 12개월 상실자 합 ÷ 같은 기간 평균 가입자
```

- 직전 달 데이터가 빠졌으면 비율을 계산하지 않습니다(NULL).
- 가입자 10명 미만은 "표본 부족"으로 표시합니다.

**환산 월세와 주거비 부담률**

```
환산 월세 = 월세 + 보증금 × 연 전월세전환율 ÷ 12
주거비 부담률 = 역세권 환산 월세 ÷ (추정 연봉 ÷ 12)
```

**SQL 예시: 회사별 월 지표 (빈 달 처리 포함)**

```sql
SELECT company_id, snapshot_ym, members,
       CASE WHEN prev_ym = PERIOD_ADD(snapshot_ym, -1)
            THEN lost_m / NULLIF(prev_members, 0) END AS quit_rate
FROM (
  SELECT a.*,
         LAG(members)     OVER (PARTITION BY company_id ORDER BY snapshot_ym) AS prev_members,
         LAG(snapshot_ym) OVER (PARTITION BY company_id ORDER BY snapshot_ym) AS prev_ym
  FROM company_monthly_agg a
) t;
```

**공간 인덱스를 타는 반경 검색**

```sql
-- ST_Distance_Sphere만 쓰면 전체 스캔 → MBR로 후보를 먼저 거른다
WHERE MBRContains(ST_Buffer(s.pt, 0.006), b.pt)
  AND ST_Distance_Sphere(s.pt, b.pt) <= 500
```

---

## API

| 메서드 · 경로 | 설명 |
|---|---|
| `GET /companies?q=&industry=&hiring=&cursor=` | 회사 검색 (커서 페이지네이션) |
| `GET /companies/{id}` | 체력 요약 카드 (백분위, 플래그 포함) |
| `GET /companies/{id}/trend?from_ym=&to_ym=` | 월별 가입자 · 입퇴사율 · 추정 연봉 |
| `GET /companies/{id}/financials` | DART 재무 지표 |
| `GET /companies/{id}/jobs` | 진행 중 공고, 채용 신호, 제시 연봉 비교 |
| `GET /companies/{id}/housing` | 근처 역별 전월세 시세와 주거비 부담률 |
| `GET /stations/{id}/rent?months=12&contract=all` | 역세권 시세 (`months` 1~24) |
| `GET /industries/{code}/distribution` | 업종 내 분포 (p25 · p50 · p75) |
| `GET /compare?ids=1,2,3` | 회사 비교 (최대 3곳) |
| `GET /meta/methodology` | 계산식 · 한계 · 데이터 기준월 · 출처 |
| `GET /health` | DB 연결, 마지막 적재 월 |

추정치가 들어간 응답에는 `flags`(예: `salary_is_lower_bound`, `small_sample`)를 함께 내려줍니다.

---

## 프로젝트 구조

> 계획 중인 구조이며, 구현하면서 바뀔 수 있습니다.

```
worth-joining/
├─ app/                  # FastAPI
│  ├─ main.py
│  ├─ core/              # 설정, DB 연결
│  ├─ routers/           # companies, stations, industries, meta
│  ├─ schemas/           # Pydantic 응답 모델
│  ├─ repositories/      # SQL
│  └─ services/          # 플래그 · 문구 생성
├─ pipeline/             # 수집 · 정제 · mart 갱신 배치
│  ├─ nps/  dart/  rent/  stations/  geocode/  saramin/
│  └─ scheduler.py
├─ migrations/           # Alembic
├─ sql/                  # mart 갱신 SQL
├─ web/                  # Next.js
├─ tests/                # pytest (unit, sql, api)
├─ docker-compose.yml    # 로컬 MariaDB
└─ .env.example
```

---

## 시작하기

> 구현 전 단계라 아래는 예정된 실행 방법입니다.

**필요한 것:** Python 3.12, Node.js 20+, Docker

**1. 환경 변수**

```bash
cp .env.example .env
```

```dotenv
DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/worth_joining
DATA_GO_KR_SERVICE_KEY=   # 공공데이터포털 (국토부 실거래가 등)
OPENDART_API_KEY=         # OpenDART
JUSO_SEARCH_KEY=          # 주소정보누리집 검색 API
JUSO_COORD_KEY=           # 주소정보누리집 좌표제공 API
SARAMIN_ACCESS_KEY=       # 사람인 API (승인 후)
NEXT_PUBLIC_MAP_KEY=      # 카카오맵 또는 네이버 지도 (도메인 등록 필요)
```

API 키는 저장소에 올리지 않습니다. `.env`는 `.gitignore`에 포함합니다.

**2. DB와 스키마**

```bash
docker compose up -d mariadb
alembic upgrade head
```

**3. 데이터 적재**

```bash
python -m pipeline.nps.load --ym 202608     # 국민연금 월 파일 적재
python -m pipeline.refresh_mart             # mart 갱신
```

**4. 실행**

```bash
uvicorn app.main:app --reload               # http://localhost:8000/docs
cd web && npm install && npm run dev        # http://localhost:3000
```

**5. 테스트**

```bash
pytest
```

---

## 로드맵

- [ ] **1~5주: 회사 체력 (MVP)**
  - [ ] 데이터 프로파일링, ERD 확정
  - [ ] 국민연금 적재 파이프라인, 과거 월 백필
  - [ ] mart SQL (월별 지표, 요약 · 백분위)
  - [ ] FastAPI 엔드포인트, 테스트
  - [ ] DART 연동 · 매칭, 배포
  - [ ] 채용공고 바로가기 링크
- [ ] **확장: 역세권 전월세 (+3주)**
  - [ ] 서울 전월세 24개월 수집, 월 단위 파티션
  - [ ] 주소정보누리집 좌표 변환, 역별 시세 집계
  - [ ] 회사 ↔ 역 연결, 주거비 부담률 API
- [ ] **확장: 채용 정보 연계 (+2주, 사람인 API 승인 후)**
  - [ ] 일 1회 공고 수집, 회사 매칭
  - [ ] 채용 신호, 제시 연봉 비교
- [ ] 지도 SDK 선택 (카카오맵 / 네이버 지도)

---

## 한계와 면책

- **추정 연봉:** 국민연금 고지금액에서 역산한 회사 전체 평균의 **하한 추정치**입니다. 개인 · 직무별 연봉이 아니며, 성과급 · 상여는 반영되지 않습니다.
- **입퇴사 수치:** 국민연금 신규 · 상실 인원은 연속된 두 달을 비교해 산출한 값이라 실제 입퇴사와 다를 수 있습니다.
- **공개 범위:** 법인은 가입자 3인 이상, 개인사업장은 10인 이상만 공개되어 소규모 사업장은 빠집니다.
- **회사 매칭:** 상호 기반 매칭이라 동명 회사를 잘못 연결할 수 있으며, 매칭 방식과 신뢰도를 화면에 표시합니다.
- **전월세 시세:** 신고된 실거래가 기준이라 현재 매물 호가와 다를 수 있습니다. 단독 · 다가구는 제외됩니다.
- **채용 신호:** 통계로 추정한 **가능성**이며 회사의 실제 채용 사유를 뜻하지 않습니다.
- 이 서비스의 정보는 참고용이며, 투자 · 법률 · 고용 판단의 근거로 단독 사용해서는 안 됩니다.

---

## 라이선스

- 코드: MIT License (예정)
- 데이터: 각 제공 기관의 이용 조건을 따르며, 출처를 서비스 내에 표시합니다.
