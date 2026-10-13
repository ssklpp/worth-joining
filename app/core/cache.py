"""응답 캐시 헤더(NFR-OPS-02, SPEC 8장). 데이터는 월 1회 다시 적재할 때만 바뀌므로
성공한 GET 응답에 Cache-Control(1시간)과 본문 해시 ETag를 붙이고, If-None-Match가 같으면 304를 준다.
/health(배포 상태 확인 · 화면 하단 기준월)와 문서 화면은 제외한다."""

import hashlib

from starlette.requests import Request
from starlette.responses import Response

CACHE_CONTROL = "public, max-age=3600"
SKIP = ("/health", "/docs", "/redoc", "/openapi.json")


async def cache_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    if (request.method != "GET" or response.status_code != 200
            or request.url.path.startswith(SKIP)):
        return response
    body = b"".join([chunk async for chunk in response.body_iterator])
    etag = f'W/"{hashlib.md5(body).hexdigest()}"'
    headers = {k: v for k, v in response.headers.items()
               if k.lower() not in ("content-length", "etag", "cache-control")}
    headers |= {"ETag": etag, "Cache-Control": CACHE_CONTROL}
    if request.headers.get("if-none-match") == etag:
        headers.pop("content-type", None)
        return Response(status_code=304, headers=headers)
    return Response(body, status_code=200, headers=headers)
