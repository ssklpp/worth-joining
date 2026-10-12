# tests/fixtures

실제 API 키 · 원본 파일 없이 모든 테스트가 돌아가도록 쓰는 샘플 데이터(SPEC 12.3). 실제 회사 이름이나 개인 정보는 넣지 않는다.

## 지금 방식

국민연금 CSV는 파일로 두지 않고 테스트가 그때그때 만든다.

- `tests/nps_csv.py`의 `Row`, `write_nps_csv(path, ym, rows)`: 실제 헤더 22개(`pipeline/nps/columns.py`)와 CP949 인코딩으로 가상 회사 CSV를 `tmp_path`에 쓴다.
- 법정동코드 파일도 `tests/unit/test_region_load.py`가 몇 줄짜리 샘플을 직접 쓴다.

테스트마다 필요한 행만 적어 두면 무엇을 검사하는지가 테스트 안에서 바로 보인다.

## 앞으로 둘 파일

| 파일 (예정) | 내용 | 담당 |
|---|---|---|
| `nps/*.csv` | mart SQL 회귀 테스트용 국민연금 축소 CSV. 가상 회사 20~40개, 20개월(T2-06) | T2 |
| `dart/*.json`, `dart/*.xml` | OpenDART 응답 샘플 | T1 |
| `rent/*.json` | 서울시 전월세 응답 샘플 | T1 |
| `saramin/*.json` | 사람인 검색 응답 샘플 | T1 |
