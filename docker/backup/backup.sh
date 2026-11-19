#!/bin/sh
set -eu
TS=$(date -u +"%Y%m%dT%H%M%SZ")
OUT="/backups/sajona_${TS}.sql.gz"
pg_dump -h "${PGHOST:-sajona-db}" -U "${PGUSER:-sajona}" -d "${PGDATABASE:-sajona}" | gzip > "$OUT"
ln -sf "$OUT" /backups/latest.sql.gz
# Retención de últimos 14 respaldos
ls -1t /backups/sajona_*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm -f
echo "[backup] Respaldo generado: $OUT"
