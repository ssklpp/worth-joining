"""company ↔ dart_corp 매칭 → company_dart_link (SPEC 6장 매칭 순서, Phase 5-4).

python -m pipeline.dart.match

① 정확: 사업자번호 앞 6자리와 정규화 이름이 모두 같다 → exact, 1.000
② 유사: ①에서 안 된 회사 중 사업자번호 앞 6자리가 같은 법인과 rapidfuzz token_sort_ratio ≥ 85
   → fuzzy, 점수 ÷ 100. 6자리가 같은 법인끼리만 비교한다(전체 비교는 16만 × 12만이라 하지 않음).
   - 비교 전에 "&"는 "앤"으로, 영문 대문자는 한글 읽기로 바꾼다. DART는 "LG디스플레이",
     "F&F", 국민연금은 "엘지디스플레이(주)", "에프앤에프"처럼 적는 경우가 많다
   - 85 ~ 89점은 한쪽 이름이 다른 쪽으로 시작할 때만 연결한다("엘지유플러스(영업)" → "LG유플러스").
     같은 6자리를 쓰는 새마을금고 · 신협끼리("봉천" → "은천")나 비슷한 다른 회사("한오션" →
     "한화오션")가 이 구간에 몰려 있었다(docs/matching.md)
③ 그 외는 연결하지 않는다.
한 회사에 후보가 여럿이면 상장사, corp_code 순. manual 연결은 지우지 않고 다시 계산하지도 않는다.
사업자번호는 company.json으로 받은 법인만 있으므로 그 범위 안에서만 연결된다.
"""

import logging
import sys
from collections import defaultdict

from rapidfuzz import fuzz
from sqlalchemy import Connection, Engine, text

from pipeline.common.db import sync_engine
from pipeline.common.ingestion import finish_run, start_run
from pipeline.common.normalize import normalize_name

log = logging.getLogger(__name__)

SOURCE = "dart_match"
THRESHOLD = 85
SURE = 90  # 이 점수 이상은 앞부분 일치 없이도 연결한다
LETTERS = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", (
    "에이 비 씨 디 이 에프 지 에이치 아이 제이 케이 엘 엠 엔 오 피 큐 알 에스 티 유 브이 더블유"
    " 엑스 와이 지").split(), strict=True))

EXACT = """
INSERT INTO company_dart_link (company_id, corp_code, match_type, match_score)
SELECT company_id, corp_code, 'exact', 1.000
  FROM (SELECT c.company_id, d.corp_code,
               ROW_NUMBER() OVER (PARTITION BY c.company_id
                                  ORDER BY d.stock_code IS NULL, d.corp_code) AS rn
          FROM company c
          JOIN dart_corp d ON d.bizr6 = c.biz_no6 AND d.corp_name_norm = c.name_norm
         WHERE NOT EXISTS (SELECT 1 FROM company_dart_link l WHERE l.company_id = c.company_id)
       ) t
 WHERE rn = 1
"""


def match_key(name: str) -> str:
    """유사 비교용 이름. "LG디스플레이" → "엘지디스플레이", "(주)F&F" → "에프앤에프"."""
    return "".join(LETTERS.get(ch, ch) for ch in normalize_name(name.replace("&", "앤")))


def similar(a: str, b: str) -> float | None:
    """연결할 만하면 점수(0 ~ 100), 아니면 None."""
    score = fuzz.token_sort_ratio(a, b)
    if score >= SURE or (score >= THRESHOLD and (a.startswith(b) or b.startswith(a))):
        return score
    return None


def fuzzy_links(conn: Connection) -> list[dict]:
    """정확 연결이 안 된 회사를 같은 사업자번호 6자리의 법인과만 비교한다(similar,
    docs/matching.md).
    동점이면 상장사 · corp_code 순으로 앞선 법인을 고른다.
    """
    corps = defaultdict(list)
    for code, bizr6, name in conn.execute(text(
        "SELECT corp_code, bizr6, corp_name FROM dart_corp"
        " WHERE bizr6 IS NOT NULL ORDER BY stock_code IS NULL, corp_code"
    )):
        corps[bizr6].append((code, match_key(name)))
    links = []
    for company_id, biz_no6, display_name in conn.execute(text(
        "SELECT company_id, biz_no6, display_name FROM company c WHERE NOT EXISTS"
        " (SELECT 1 FROM company_dart_link l WHERE l.company_id = c.company_id)"
    )):
        best, key = None, match_key(display_name)
        for code, corp_key in corps.get(biz_no6, ()):
            score = similar(key, corp_key)
            if score is not None and (best is None or score > best[1]):  # 동점이면 앞(상장사)
                best = (code, score)
        if best:
            links.append({"id": company_id, "code": best[0], "score": round(best[1] / 100, 3)})
    return links


def match(conn: Connection) -> dict[str, int]:
    """manual 연결은 남기고 exact → fuzzy 순으로 다시 만든다. 몇 번을 돌려도 결과가 같다."""
    conn.execute(text("DELETE FROM company_dart_link WHERE match_type <> 'manual'"))
    exact = conn.execute(text(EXACT)).rowcount
    links = fuzzy_links(conn)
    if links:
        conn.execute(text(
            "INSERT INTO company_dart_link (company_id, corp_code, match_type, match_score)"
            " VALUES (:id, :code, 'fuzzy', :score)"
        ), links)
    return {"exact": exact, "fuzzy": len(links)}


def run(engine: Engine) -> dict[str, int]:
    with engine.begin() as conn:
        run_id = start_run(conn, SOURCE, "all", None)
    try:
        with engine.begin() as conn:
            counts = match(conn)
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", sum(counts.values()), str(counts))
        log.info("company_dart_link %s", counts)
        return counts
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run(sync_engine())
    return 0


if __name__ == "__main__":
    sys.exit(main())
