# 2. 풀스택 서비스 코드 저장소

이 GitHub 저장소(https://github.com/ssklpp/worth-joining) 전체가 2번 산출물입니다. 제출용 로컬 사본에는 `worth-joining/`에 저장소 클론을 두지만 GitHub에는 올리지 않습니다. 기준 커밋은 `main`의 `eed4966`(2026-10-21, 릴리스 `v1.4.0` 이후 문서 갱신)입니다.

| 폴더 | 내용 |
|---|---|
| `pipeline/` | 데이터 수집 · 정제 · 적재(국민연금 · DART · 전월세 · 역 · 좌표), 품질 검사, mart 갱신 |
| `migrations/` | Alembic 마이그레이션 0001 ~ 0011(DB 스키마) |
| `sql/` | 핵심 통계 SQL(월별 지표, 요약 · 백분위, 역세권 시세, 회사-역) |
| `app/` | FastAPI 백엔드(읽기 전용 API): routers · repositories · services · schemas |
| `web/` | Next.js 15 프론트엔드(대시보드: 지도 + 패널, 상세 · 비교 · 역 시세) |
| `tests/` | pytest(단위 · SQL 회귀 · API), 부하 측정(locust) |
| `docs/` | 설계 · 테스트 · 배포 · 보고서 문서 |
| `README.md` | 서비스 소개, 구조, 기술 스택, 지표 계산, API, 시작하기 |

- 실행 방법은 저장소 루트 `README.md`의 "시작하기"와 4번 가이드를 봅니다.
- 포함하지 않은 것: `.env`(API 키 · DB 비밀번호), `data/`(원본 데이터 · 덤프), `node_modules/`. 둘 다 `.gitignore` 대상입니다.
- 로컬 사본을 최신으로 맞추려면 `worth-joining` 폴더에서 `git pull`을 실행합니다.
