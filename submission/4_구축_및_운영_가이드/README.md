# 4. 구축 및 운영 가이드

서비스 실행, 데이터 갱신, 기본 점검 방법을 정리한 문서입니다.

| 목적 | 파일 | 볼 곳 |
|---|---|---|
| **로컬에서 실행** | [로컬_실행.md](./로컬_실행.md) | 설치 · 환경 변수 · DB 준비(덤프 복원 또는 적재) · API · 웹 실행 · 테스트 |
| **배포 구축** | [runbook.md](./runbook.md) | 2장: Railway(mariadb · api) · Vercel(web) 처음 배포, DB 복원, 3장: 환경 변수 전체 |
| **데이터 갱신** | [runbook.md](./runbook.md) | 4장: 월 갱신(국민연금 · DART · 좌표 · 전월세 → mart → 배포 DB 반영), 다음 갱신 일정 |
| **백업 · 복구** | [runbook.md](./runbook.md) | 5장 백업, [10_deployment.md](./10_deployment.md) 10장 되돌리기 |
| **배포 현황 · 기본 점검** | [10_deployment.md](./10_deployment.md) | 1장 현황, 6장 최종 기능 확인(배포 API 26개 점검 · 웹 · 보안 헤더), 배포 승인 점검표 |
| **장애 대응** | [runbook.md](./runbook.md) | 7장 증상별 볼 곳 |
| **테스트 방법 · 결과** | [07_test_plan.md](./07_test_plan.md) · [09_test_result.md](./09_test_result.md) | 시나리오 · 화면 점검 항목, pytest 234 · 화면 테스트 15 결과 |
| **성능 점검** | [performance.md](./performance.md) · [explain.md](./explain.md) | 부하 측정 방법(locust) · 결과, 쿼리 실행 계획 |

## 매일 · 매월 기본 점검

| 언제 | 점검 | 정상 |
|---|---|---|
| 수시 | `https://api-production-30254.up.railway.app/health` | `status: ok`, `db: ok`, `latest_nps_ym` = 최신 기준월 |
| 수시 | 웹 첫 화면 하단 기준월 | API의 `latest_nps_ym`과 같음(웹 → API → DB 연결) |
| 코드 병합 뒤 | GitHub Actions CI(`test` · `web` · `api-image`) | 모두 성공, Vercel · Railway 자동 배포 성공 |
| 월 갱신 뒤 | `ingestion_log`의 품질 검사 결과, `/health` 기준월, 회사 몇 곳의 추이에 새 달 | `success`, 새 달 |
| 스키마 변경 뒤 | 배포 DB `SELECT version_num FROM alembic_version` | 코드의 `alembic heads`와 같음 |
| 데이터 반영 뒤 | Railway TCP Proxy | 꺼짐(DB 공개 포트 없음) |
