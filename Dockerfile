# API 이미지(Railway api 서비스). 웹은 Vercel, DB는 Railway mariadb 서비스에서 따로 돈다(docs/runbook.md)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv

COPY pyproject.toml README.md LICENSE ./
COPY app ./app
COPY pipeline ./pipeline
COPY sql ./sql
RUN pip install .

# Railway가 PORT를 넣어 준다. 로컬에서는 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
