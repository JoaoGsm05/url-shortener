# ── Stage 1: instala dependências ────────────────────────────────────────────
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
# Instala deps sem o projeto para aproveitar cache de layer
RUN uv sync --frozen --no-dev --no-install-project

COPY app/ app/
RUN uv sync --frozen --no-dev

# ── Stage 2: imagem de runtime (sem uv, sem cache de build) ───────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app   /app/app
COPY migrations/               migrations/
COPY alembic.ini               .
COPY docker/entrypoint.sh      entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
