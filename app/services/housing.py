"""역 시세 고르기 · 주거비 부담률 (SPEC 6장, Phase 9-12, decisions/007)."""

from collections.abc import Mapping

from app.schemas.housing import Burden, StationRent, StationTrendPoint

SMALL_SAMPLE = 20  # 역 계약 20건 미만이면 표본 부족(SPEC 6장)
TREND_MONTHS = 24
MONTHLY_MIN = 5  # 24개월 모두 월세 계약이 이만큼 있어야 월 단위로 보여 준다(FR-HOUS-04)


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


def pick_trend(rows: list[Mapping]) -> tuple[str | None, list[StationTrendPoint]]:
    """월 단위 추이는 24개월 모두 월세 계약이 5건 이상일 때만 쓴다. 아니면 분기 단위.
    건수가 적은 달의 중앙값은 계약 몇 건에 크게 흔들리기 때문이다."""
    months = [r for r in rows if r["grain"] == "month"]
    full = len(months) == TREND_MONTHS and all(r["n_monthly"] >= MONTHLY_MIN for r in months)
    grain = "month" if full else "quarter"
    points = [StationTrendPoint(**{k: r[k] for k in StationTrendPoint.model_fields})
              for r in rows if r["grain"] == grain]
    return (grain if points else None), points
