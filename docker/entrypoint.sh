#!/bin/sh
set -e

echo "[entrypoint] Aplicando migrações..."
alembic upgrade head

echo "[entrypoint] Iniciando servidor na porta ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
