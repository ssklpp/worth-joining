"""국민연금 월 적재 품질 검사 (SPEC Phase 2-4, T2-02, 기준은 docs/decisions/003).

적재 트랜잭션 안에서 raw · core를 넣은 뒤 실행한다. 하나라도 실패하면 QualityError를 던져
그 달의 raw · core를 되돌리고(이전 상태 유지) ingestion_log에 failed로 남긴다.
"""

from dataclasses import dataclass

from sqlalchemy import Connection, text

ROW_CHANGE_LIMIT = 0.10  # 전월 대비 raw 행 수 변동
ACTIVE_ZERO_LIMIT = 0.01  # 등록 행 중 members <= 0 비율


@dataclass
class Check:
    """검사 하나의 결과. detail은 ingestion_log.message에 그대로 남는다."""
    name: str
    passed: bool
    detail: str


class QualityError(Exception):
    """실패한 검사 목록. 적재 트랜잭션을 되돌리라는 신호다."""
    def __init__(self, failed: list[Check]):
        self.failed = failed
        super().__init__("; ".join(f"{c.name}: {c.detail}" for c in failed))


def _one(conn: Connection, sql: str, ym: int):
    return conn.execute(text(sql), {"ym": ym}).one()


def check_row_change(conn: Connection, ym: int) -> Check:
    """전월 대비 raw 행 수가 ±10%를 넘으면 실패. 파일이 잘렸거나 다른 범위로 추출된 경우를 잡는다.
    전월 raw가 없는 첫 달은 통과시킨다.
    """
    cur, prev = _one(conn, """
        SELECT SUM(snapshot_ym = :ym), SUM(snapshot_ym = PERIOD_ADD(:ym, -1))
          FROM raw_nps_workplace WHERE snapshot_ym IN (:ym, PERIOD_ADD(:ym, -1))
    """, ym)
    if not prev:
        return Check("row_change", True, "전월 raw 없음, 건너뜀")
    change = int(cur or 0) / int(prev) - 1
    return Check("row_change", round(abs(change), 6) <= ROW_CHANGE_LIMIT,
                 f"전월 대비 {change:+.2%} (기준 ±{ROW_CHANGE_LIMIT:.0%})")


def check_active_zero(conn: Connection, ym: int) -> Check:
    """등록(status 1) 행 중 가입자 0명 이하가 1%를 넘으면 실패.
    탈퇴 행은 0명이 정상이라 등록 행만 본다(decisions/003).
    """
    active, zero = _one(conn, """
        SELECT COUNT(*), SUM(members <= 0)
          FROM raw_nps_workplace WHERE snapshot_ym = :ym AND status_code = '1'
    """, ym)
    ratio = int(zero or 0) / active if active else 1.0  # 등록 행이 없는 달은 파일 이상으로 본다
    return Check("active_zero", ratio <= ACTIVE_ZERO_LIMIT,
                 f"등록 {active:,}행 중 0명 이하 {int(zero or 0):,}행 ({ratio:.3%}, 기준 "
                 f"{ACTIVE_ZERO_LIMIT:.0%})")


def check_billed_cap(conn: Connection, ym: int) -> Check:
    """고지금액이 가입자 수 × 소득 상한 × 보험료율을 넘는 등록 행이 있으면 실패.
    열 밀림 · 단위 오류를 잡는다.
    """
    (over,) = _one(conn, """
        SELECT COUNT(*)
          FROM raw_nps_workplace r
          JOIN nps_rate n ON :ym BETWEEN n.valid_from_ym AND n.valid_to_ym
         WHERE r.snapshot_ym = :ym AND r.status_code = '1'
           AND r.billed_amount > r.members * n.income_cap * n.rate
    """, ym)
    return Check("billed_cap", over == 0, f"상한 초과 {over:,}행")


def check_rate_covered(conn: Connection, ym: int) -> Check:
    """그 달에 맞는 nps_rate 행이 정확히 1개여야 한다. 없으면 추정 연봉을 계산할 수 없다."""
    (n,) = _one(conn, """
        SELECT COUNT(*) FROM nps_rate WHERE :ym BETWEEN valid_from_ym AND valid_to_ym
    """, ym)
    return Check("rate_covered", n == 1, f"nps_rate 기간 행 {n}개 (1개여야 함)")


CHECKS = [check_rate_covered, check_row_change, check_active_zero, check_billed_cap]


def run_checks(conn: Connection, ym: int) -> list[Check]:
    """모든 검사를 실행하고, 하나라도 실패하면 QualityError."""
    results = [check(conn, ym) for check in CHECKS]
    failed = [c for c in results if not c.passed]
    if failed:
        raise QualityError(failed)
    return results
