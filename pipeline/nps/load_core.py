"""raw_nps_workplace → company · workplace · workplace_monthly (SPEC Phase 2-3, T1-04).

규칙은 docs/decisions/003:
- company · workplace는 등록(status_code='1') 행에서만 만든다.
- 자연키 (biz_no6, name_norm, workplace_name, legal_dong_code)가 같은 행은 합산한다.
- 탈퇴 행은 그 사업장이 전월에 가입자가 있었을 때만 월별에 넣는다(탈퇴한 달의 상실자).
월을 오름차순으로 적재해야 전월 조건이 맞는다. 같은 월을 다시 넣어도 결과가 같다.
"""

from sqlalchemy import Connection, text

RAW_COMPANY_JOIN = """
  FROM raw_nps_workplace r
  JOIN company c ON c.biz_no6 = r.biz_no6 AND c.name_norm = r.name_norm
"""

STEPS: list[tuple[str, str]] = [
    ("industry", """
INSERT INTO industry (industry_code, industry_name)
SELECT industry_code, MAX(industry_name)
  FROM raw_nps_workplace
 WHERE snapshot_ym = :ym AND industry_code IS NOT NULL AND industry_name IS NOT NULL
 GROUP BY industry_code
ON DUPLICATE KEY UPDATE industry_name = VALUES(industry_name)
"""),
    ("company", """
INSERT INTO company (biz_no6, name_norm, display_name)
SELECT biz_no6, name_norm, MIN(workplace_name)
  FROM raw_nps_workplace
 WHERE snapshot_ym = :ym AND status_code = '1' AND name_norm <> ''
 GROUP BY biz_no6, name_norm
ON DUPLICATE KEY UPDATE display_name = VALUES(display_name)
"""),
    ("workplace", f"""
INSERT INTO workplace (company_id, workplace_name, form_type, industry_code, legal_dong_code,
                       road_address, joined_on, left_on)
SELECT c.company_id, r.workplace_name, MIN(r.form_type), MAX(r.industry_code), r.legal_dong_code,
       MAX(r.road_address), MIN(r.joined_on), NULL
{RAW_COMPANY_JOIN}
 WHERE r.snapshot_ym = :ym AND r.status_code = '1'
 GROUP BY c.company_id, r.workplace_name, r.legal_dong_code
ON DUPLICATE KEY UPDATE form_type = VALUES(form_type), industry_code = VALUES(industry_code),
                        road_address = VALUES(road_address), left_on = NULL,
                        joined_on = LEAST(COALESCE(joined_on, VALUES(joined_on)),
                                          COALESCE(VALUES(joined_on), joined_on))
"""),
    ("workplace_monthly_delete", """
DELETE FROM workplace_monthly WHERE snapshot_ym = :ym
"""),
    ("workplace_monthly", f"""
INSERT INTO workplace_monthly (workplace_id, snapshot_ym, members, billed_amount,
                               new_members, lost_members)
SELECT w.workplace_id, :ym, SUM(r.members), SUM(r.billed_amount),
       SUM(r.new_members), SUM(r.lost_members)
{RAW_COMPANY_JOIN}
  JOIN workplace w ON w.company_id = c.company_id AND w.workplace_name = r.workplace_name
                  AND w.legal_dong_code = r.legal_dong_code
 WHERE r.snapshot_ym = :ym
   AND (r.status_code = '1'
        OR EXISTS (SELECT 1 FROM workplace_monthly p
                    WHERE p.workplace_id = w.workplace_id
                      AND p.snapshot_ym = PERIOD_ADD(:ym, -1) AND p.members > 0))
 GROUP BY w.workplace_id
"""),
    ("workplace_left_on", f"""
UPDATE workplace w
  JOIN (SELECT c.company_id, r.workplace_name, r.legal_dong_code, MAX(r.left_on) AS left_on
        {RAW_COMPANY_JOIN}
         WHERE r.snapshot_ym = :ym
         GROUP BY c.company_id, r.workplace_name, r.legal_dong_code
        HAVING SUM(r.status_code = '1') = 0) t
    ON t.company_id = w.company_id AND t.workplace_name = w.workplace_name
   AND t.legal_dong_code = w.legal_dong_code
   SET w.left_on = COALESCE(t.left_on, w.left_on)
"""),
]


def load_core(conn: Connection, ym: int) -> dict[str, int]:
    """한 달치 raw를 core에 반영한다. 단계별 영향 행 수를 돌려준다."""
    return {name: conn.execute(text(sql), {"ym": ym}).rowcount for name, sql in STEPS}
