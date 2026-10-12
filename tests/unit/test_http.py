import httpx
import pytest
from sqlalchemy import text

from pipeline.common.http import ApiClient, ApiError, QuotaExceeded

URL = "https://api.example.test/x"


def client(engine, handler, limit=100, secret="SECRETKEY"):
    return ApiClient(engine, "test", limit, secret=secret,
                     transport=httpx.MockTransport(handler), backoff=0)


def calls(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT SUM(count) FROM api_call_log")).scalar()


def test_retries_server_error_then_succeeds(clean_tables):
    statuses = iter([500, 503, 200])
    c = client(clean_tables, lambda req: httpx.Response(next(statuses), text="ok"))

    assert c.get(URL, {"k": "SECRETKEY"}).text == "ok"
    assert calls(clean_tables) == 3


def test_gives_up_after_retries(clean_tables):
    c = client(clean_tables, lambda req: httpx.Response(502))

    with pytest.raises(ApiError, match="HTTP 502"):
        c.get(URL, {})
    assert calls(clean_tables) == 4  # 처음 1번 + 재시도 3번


def test_client_error_is_not_retried_and_hides_key(clean_tables):
    c = client(clean_tables, lambda req: httpx.Response(401))

    with pytest.raises(ApiError) as e:
        c.get(URL, {"crtfc_key": "SECRETKEY"})
    assert "SECRETKEY" not in str(e.value) and "***" in str(e.value)
    assert calls(clean_tables) == 1


def test_network_error_message_hides_key(clean_tables):
    def fail(req):
        raise httpx.ConnectError(f"cannot connect {req.url}")

    with pytest.raises(ApiError) as e:
        client(clean_tables, fail).get(URL, {"crtfc_key": "SECRETKEY"})
    assert "SECRETKEY" not in str(e.value)


def test_stops_at_daily_limit(clean_tables):
    c = client(clean_tables, lambda req: httpx.Response(200), limit=2)
    c.get(URL, {})
    c.get(URL, {})

    with pytest.raises(QuotaExceeded):
        c.get(URL, {})
    assert calls(clean_tables) == 2


def test_counts_each_key_separately_without_storing_key(clean_tables):
    first = client(clean_tables, lambda req: httpx.Response(200), limit=1, secret="KEY_A")
    second = client(clean_tables, lambda req: httpx.Response(200), limit=1, secret="KEY_B")
    first.get(URL, {})

    with pytest.raises(QuotaExceeded):
        first.get(URL, {})
    second.get(URL, {})  # 다른 키는 한도가 따로다

    with clean_tables.connect() as conn:
        sources = [r[0] for r in conn.execute(text("SELECT source FROM api_call_log"))]
    assert len(sources) == 2 and all(s.startswith("test:") and "KEY" not in s for s in sources)
