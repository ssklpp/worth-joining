from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.db import get_conn
from app.repositories import companies as company_repo
from app.schemas.meta import Health, Methodology
from app.services import methodology

router = APIRouter(tags=["meta"])
Conn = Annotated[AsyncConnection, Depends(get_conn)]


@router.get("/meta/methodology", response_model=Methodology, summary="계산 방법 · 한계 · 출처")
async def get_methodology(conn: Conn) -> Methodology:
    period_from = (await conn.execute(
        text("SELECT MIN(snapshot_ym) FROM mart_company_monthly")
    )).scalar()
    return Methodology(as_of=await company_repo.latest_ym(conn), period_from=period_from,
                       formulas=methodology.FORMULAS, limitations=methodology.LIMITATIONS,
                       sources=methodology.SOURCES)


@router.get("/health", response_model=Health, summary="상태 확인")
async def health(conn: Conn) -> Health:
    """DB에 접속하지 못하면 500이다. latest_nps_ym이 null이면 mart가 비어 있다."""
    return Health(latest_nps_ym=await company_repo.latest_ym(conn))
