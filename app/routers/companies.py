from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.db import get_conn
from app.repositories import companies as repo
from app.schemas.common import Industry, Region
from app.schemas.company import (
    CompanyDetail,
    CompanyFinancials,
    CompanyList,
    CompanyListItem,
    CompanyTrend,
    DartLink,
    FinancialRow,
    Location,
    Percentiles,
    TrendPoint,
)
from app.services import cursor as cursors
from app.services.flags import company_flags, trend_flags
from pipeline.common.normalize import normalize_name

router = APIRouter(prefix="/companies", tags=["companies"])
Conn = Annotated[AsyncConnection, Depends(get_conn)]
CompanyId = Annotated[int, Path(ge=1)]
YM = Annotated[int | None, Query(ge=200001, le=209912, description="YYYYMM")]


def _industry(row) -> Industry:
    return Industry(code=row["industry_code"], name=row["industry_name"])


def _region(row) -> Region:
    return Region(sido=row["sido_name"], sigungu=row["sigungu_name"])


def _dart(link) -> DartLink | None:
    if link is None:
        return None
    return DartLink(corp_code=link["corp_code"], corp_name=link["corp_name"],
                    match_type=link["match_type"])


def _num(value):
    return None if value is None else float(value)


@router.get("", response_model=CompanyList, summary="회사 검색")
async def search_companies(
    conn: Conn,
    q: str | None = Query(None, max_length=100, description="회사명 앞부분. (주) · 공백은 무시"),
    biz_no6: str | None = Query(None, pattern=r"^\d{6}$", description="사업자번호 앞 6자리"),
    industry: str | None = Query(None, pattern=r"^\d{6}$", description="업종 코드 6자리"),
    region: str | None = Query(None, pattern=r"^\d{5}$", description="시군구 코드 5자리"),
    sort: Literal["name", "growth"] = "name",
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = None,
) -> CompanyList:
    """최신 월에 가입자가 있는 회사만 검색한다. 최근 자료 없는 회사는 결과에 없다(docs/05 A5)."""
    name_prefix = normalize_name(q) if q else None
    if q and not name_prefix:
        return CompanyList(as_of=await repo.latest_ym(conn), items=[], next_cursor=None)
    try:
        after = cursors.decode(cursor, sort) if cursor else None
    except cursors.InvalidCursor as e:
        raise HTTPException(422, str(e)) from e
    rows = await repo.search(conn, name_prefix=name_prefix, biz_no6=biz_no6, industry=industry,
                             region=region, sort=sort, limit=limit, after=after)
    page, more = rows[:limit], len(rows) > limit
    return CompanyList(
        as_of=await repo.latest_ym(conn),
        items=[
            CompanyListItem(
                company_id=r["company_id"], name=r["name"], industry=_industry(r),
                region=_region(r), members=r["members"], growth_12m=_num(r["growth_12m"]),
                quit_rate_12m=_num(r["quit_rate_12m"]), avg_salary_est=r["avg_salary_est"],
            )
            for r in page
        ],
        next_cursor=cursors.encode(sort, page[-1]["sort_value"], page[-1]["company_id"])
        if more else None,
    )


@router.get("/{company_id}", response_model=CompanyDetail, summary="회사 상세")
async def company_detail(company_id: CompanyId, conn: Conn):
    """최근 자료 없음(stale)이면 id · name · as_of · status · flags · last_seen_ym만 준다."""
    company = await repo.get_company(conn, company_id)
    if company is None:
        raise HTTPException(404, "회사를 찾을 수 없다")
    as_of = await repo.latest_ym(conn)
    s = await repo.get_summary(conn, company_id)
    link = await repo.dart_link(conn, company_id)
    if s is None:
        stale = CompanyDetail(company_id=company_id, name=company["name"], as_of=as_of,
                              status="stale", flags=company_flags(None),
                              last_seen_ym=await repo.last_seen_ym(conn, company_id))
        return JSONResponse(stale.model_dump(exclude_none=True))
    loc = await repo.location(conn, company_id)
    flags = company_flags(s)
    if loc is not None and loc["accuracy"] != "building":
        flags.append("approx_location")
    return CompanyDetail(
        company_id=company_id, name=s["name"], as_of=as_of, flags=flags,
        industry=_industry(s), region=_region(s),
        form_type={1: "corporation", 2: "individual"}.get(s["form_type"]),
        workplace_count=s["workplace_count"], members=s["members"],
        growth_12m=_num(s["growth_12m"]), quit_rate_12m=_num(s["quit_rate_12m"]),
        avg_salary_est=s["avg_salary_est"],
        percentiles=Percentiles(growth=s["pct_growth"], stability=s["pct_stability"],
                                salary=s["pct_salary"]),
        dart=_dart(link),
        rep_location=Location(**loc) if loc else None,
    )


@router.get("/{company_id}/trend", response_model=CompanyTrend, summary="월별 추이")
async def company_trend(
    company_id: CompanyId, conn: Conn, from_ym: YM = None, to_ym: YM = None,
) -> CompanyTrend:
    if await repo.get_company(conn, company_id) is None:
        raise HTTPException(404, "회사를 찾을 수 없다")
    if from_ym and to_ym and from_ym > to_ym:
        raise HTTPException(422, "from_ym이 to_ym보다 늦다")
    rows = await repo.trend(conn, company_id, from_ym, to_ym)
    summary = await repo.get_summary(conn, company_id)
    return CompanyTrend(
        company_id=company_id, as_of=await repo.latest_ym(conn),
        flags=trend_flags(rows, summary),
        points=[TrendPoint(ym=r["ym"], members=r["members"], new=r["new"], lost=r["lost"],
                           hire_rate=_num(r["hire_rate"]), quit_rate=_num(r["quit_rate"]),
                           avg_salary_est=r["avg_salary_est"]) for r in rows],
    )


@router.get("/{company_id}/financials", response_model=CompanyFinancials, summary="재무")
async def company_financials(
    company_id: CompanyId, conn: Conn, years: int = Query(5, ge=1, le=5),
) -> CompanyFinancials:
    """DART와 연결된 회사만 rows가 있다. 연결되지 않았으면 dart null, rows []."""
    if await repo.get_company(conn, company_id) is None:
        raise HTTPException(404, "회사를 찾을 수 없다")
    link = await repo.dart_link(conn, company_id)
    rows = await repo.financials(conn, link["corp_code"], years) if link else []
    return CompanyFinancials(
        company_id=company_id, as_of=await repo.latest_ym(conn),
        # 영문 · &를 한글로 읽어 같아진 1.0점 연결은 이름이 같은 것으로 본다(docs/matching.md)
        flags=["name_matched"] if link and link["match_type"] == "fuzzy"
        and link["match_score"] < 1 else [],
        dart=_dart(link),
        rows=[FinancialRow(year=r["year"], revenue=r["revenue"],
                           operating_income=r["operating_income"], net_income=r["net_income"],
                           debt_ratio=None if r["debt_ratio"] is None
                           else round(float(r["debt_ratio"]), 4)) for r in rows],
    )
