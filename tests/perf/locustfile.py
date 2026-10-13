"""API 부하 측정 (SPEC Phase 4 · 11, NFR-PERF-01 · 02). 결과는 docs/performance.md.

    python -m uvicorn app.main:app --port 8000
    python -m locust -f tests/perf/locustfile.py --host http://127.0.0.1:8000 \
        --headless -u 20 -r 5 -t 60s --only-summary

Windows에서 gevent DLL이 막히면 PURE_PYTHON=1, PYTHONUTF8=1을 함께 준다(TS-014).
localhost 대신 127.0.0.1을 쓴다. localhost는 새 연결마다 약 2초 늦어진다(TS-015).
"""

import random

import httpx
from locust import HttpUser, between, events, task

PREFIXES = ["삼성", "엘지", "현대", "에스케이", "카카오", "네이버", "한국", "서울", "대한", "우리"]
company_ids: list[int] = []


@events.test_start.add_listener
def load_company_ids(environment, **_):
    """검색 결과 여러 페이지에서 상세 조회에 쓸 회사 ID를 모은다."""
    cursor = None
    with httpx.Client(base_url=environment.host) as client:
        for _ in range(10):
            params = {"sort": "growth", "limit": 50} | ({"cursor": cursor} if cursor else {})
            body = client.get("/companies", params=params).json()
            company_ids.extend(i["company_id"] for i in body["items"])
            cursor = body["next_cursor"]


class ApiUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(5)
    def detail(self):
        self.client.get(f"/companies/{random.choice(company_ids)}", name="/companies/{id}")

    @task(3)
    def trend(self):
        self.client.get(f"/companies/{random.choice(company_ids)}/trend",
                        name="/companies/{id}/trend")

    @task(3)
    def search_prefix(self):
        self.client.get("/companies", params={"q": random.choice(PREFIXES)},
                        name="/companies?q=")

    @task(1)
    def search_growth(self):
        self.client.get("/companies", params={"sort": "growth"}, name="/companies?sort=growth")

    @task(3)
    def map_pins(self):
        """지도를 옮길 때마다 부르는 요청. 서울 안 약 3km 범위(확대 15 정도)."""
        lon, lat = random.uniform(126.85, 127.12), random.uniform(37.47, 37.62)
        bbox = f"{lon:.5f},{lat:.5f},{lon + 0.035:.5f},{lat + 0.022:.5f}"
        self.client.get("/map/companies", params={"metric": "growth", "bbox": bbox},
                        name="/map/companies?bbox=")

    @task(2)
    def housing(self):
        self.client.get(f"/companies/{random.choice(company_ids)}/housing",
                        name="/companies/{id}/housing")

    @task(1)
    def compare(self):
        ids = ",".join(str(i) for i in random.sample(company_ids, 3))
        self.client.get("/compare", params={"ids": ids}, name="/compare?ids=")

    @task(1)
    def stations(self):
        self.client.get("/stations", params={"sort": "monthly_median"}, name="/stations")
