FROM python:3.12-alpine AS builder

RUN apk add --no-cache build-base

RUN pip install --no-cache-dir "poetry==2.1.3"

WORKDIR /app
ENV POETRY_VIRTUALENVS_CREATE=false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

FROM python:3.12-alpine

RUN apk add --no-cache bash curl

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH"

COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

RUN adduser -D appuser && \
    chmod +x /app/docker-entrypoint.sh && \
    chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["/app/docker-entrypoint.sh"]
