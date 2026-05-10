#!/usr/bin/env bash
# Cria backup do PostgreSQL (local ou Render)
# Uso: ./scripts/backup_db.sh
# Requer: DATABASE_URL no ambiente ou no .env
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Carrega .env se DATABASE_URL não estiver no ambiente
if [ -z "${DATABASE_URL:-}" ] && [ -f "${PROJECT_DIR}/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "${PROJECT_DIR}/.env"
    set +a
fi

: "${DATABASE_URL:?DATABASE_URL não definida. Exporte-a ou crie um .env}"

BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

mkdir -p "${BACKUP_DIR}"

echo "[backup] Destino : ${BACKUP_FILE}"
pg_dump "${DATABASE_URL}" --no-owner --no-acl -Fp > "${BACKUP_FILE}"

SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "[backup] Concluído: ${SIZE}"
