from fastapi import FastAPI
from sqlalchemy import text

from app.core.db import engine

app = FastAPI(title="다닐만한가 API")


@app.get("/health")
async def health() -> dict[str, str]:
    # Phase 0 접속 확인용. as_of 등은 T3-07에서 추가한다.
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}
