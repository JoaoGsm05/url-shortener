#!/usr/bin/env bash
# Restaura backup do PostgreSQL (local ou Render)
# Uso: ./scripts/restore_db.sh backups/backup_20260504_120000.sql
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BACKUP_FILE="${1:?Uso: ./scripts/restore_db.sh <arquivo.sql>}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[restore] Arquivo não encontrado: ${BACKUP_FILE}" >&2
    exit 1
fi

# Carrega .env se DATABASE_URL não estiver no ambiente
if [ -z "${DATABASE_URL:-}" ] && [ -f "${PROJECT_DIR}/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "${PROJECT_DIR}/.env"
    set +a
fi

: "${DATABASE_URL:?DATABASE_URL não definida. Exporte-a ou crie um .env}"

echo "[restore] Arquivo  : ${BACKUP_FILE}"
echo "[restore] Destino  : ${DATABASE_URL%%@*}@***"
echo ""
echo "  ATENÇÃO: os dados existentes serão substituídos."
echo ""
read -r -p "[restore] Confirmar? (s/N): " resp
[[ "${resp}" =~ ^[Ss]$ ]] || { echo "[restore] Cancelado."; exit 0; }

psql "${DATABASE_URL}" < "${BACKUP_FILE}"
echo "[restore] Concluído."
