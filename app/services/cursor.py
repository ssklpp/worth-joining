"""키셋 페이지네이션 커서: (정렬 이름, 정렬 값, company_id)를 base64url JSON으로(docs/05 A1)."""

import base64
import json
from decimal import Decimal


class InvalidCursor(ValueError):
    pass


def encode(sort: str, value: object, company_id: int) -> str:
    if isinstance(value, Decimal):
        value = str(value)
    raw = json.dumps([sort, value, company_id], ensure_ascii=False).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode(cursor: str, sort: str) -> tuple[object, int]:
    """다른 정렬에서 만든 커서이거나 형식이 틀리면 InvalidCursor."""
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        cursor_sort, value, company_id = json.loads(raw)
    except (ValueError, TypeError) as e:
        raise InvalidCursor("cursor 형식이 올바르지 않다") from e
    if cursor_sort != sort or not isinstance(company_id, int):
        raise InvalidCursor("cursor가 현재 sort와 맞지 않는다")
    return value, company_id
