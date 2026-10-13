"""역 시세 고르기 · 주거비 부담률 (SPEC 6장, Phase 9-12, decisions/007)."""

from collections.abc import Mapping

from app.schemas.housing import Burden, StationRent

SMALL_SAMPLE = 20  # 역 계약 20건 미만이면 표본 부족(SPEC 6장)


def pick_rent(rents: Mapping[tuple[int, int], Mapping], station_id: int,
              months: int) -> tuple[StationRent | None, list[str]]:
    """요청 기간의 시세. 월세 계약이 20건 미만이면 24개월로 넓히고 flag를 단다.
    24개월에도 20건 미만이면 small_sample."""
    row, flags = rents.get((station_id, months)), []
    if months != 24 and (row is None or row["n_monthly"] < SMALL_SAMPLE):
        wider = rents.get((station_id, 24))
        if wider is not None:
            row = wider
            flags.append("period_extended_to_24m")
    if row is None:
        return None, flags
    if row["n_monthly"] < SMALL_SAMPLE:
        flags.append("small_sample")
    return StationRent(
        months=row["window_months"], n_monthly=row["n_monthly"], n_jeonse=row["n_jeonse"],
        monthly_p25=row["monthly_p25"], monthly_median=row["monthly_median"],
        monthly_p75=row["monthly_p75"], deposit_median_man=row["deposit_median_man"],
        rent_median_man=row["rent_median_man"], jeonse_p25_man=row["jeonse_p25_man"],
        jeonse_median_man=row["jeonse_median_man"], jeonse_p75_man=row["jeonse_p75_man"],
    ), flags


def burden(rent: StationRent | None, monthly_pay: int | None) -> Burden | None:
    """환산 월세(p25 · 중앙값 · p75) ÷ 추정 월급.
    추정 월급이 하한이라 부담률은 실제보다 높게 나온다."""
    if rent is None or not monthly_pay or rent.monthly_median is None:
        return None

    def ratio(v):
        return None if v is None else round(v / monthly_pay, 4)
    return Burden(low=ratio(rent.monthly_p25), mid=ratio(rent.monthly_median),
                  high=ratio(rent.monthly_p75))
