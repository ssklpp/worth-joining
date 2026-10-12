"""응답 flags 생성 (SPEC 8장, docs/05 1장). 화면 문구는 docs/03 7장."""

from collections.abc import Mapping


def company_flags(summary: Mapping | None) -> list[str]:
    """회사 요약 행 기준 flags. 요약이 없으면(최근 자료 없음) stale."""
    if summary is None:
        return ["stale"]
    flags = []
    if summary["avg_salary_est"] is not None:
        flags.append("salary_is_lower_bound")  # 소득 상한 때문에 항상 하한 추정치
    if summary["small_sample"]:
        flags.append("small_sample")
    if summary["short_history"]:
        flags.append("short_history")
    return flags


def trend_flags(points: list[Mapping], summary: Mapping | None) -> list[str]:
    """추이 응답 flags. 이력 길이는 기간 필터와 관계없이 회사 요약 기준이다."""
    flags = [f for f in company_flags(summary) if f != "salary_is_lower_bound"]
    if any(p["avg_salary_est"] is not None for p in points):
        flags.insert(0, "salary_is_lower_bound")
    return flags
