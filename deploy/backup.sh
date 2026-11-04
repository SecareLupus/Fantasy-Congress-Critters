#!/usr/bin/env bash
# Nightly backup: a database dump, and the official roster snapshots (the only downloads
# that can't be fetched again). Kept in deploy/backups for BACKUP_KEEP_DAYS and copied to
# BACKUP_REMOTE with rclone when it's set. Run by critters-backup.timer; pings
# HEALTHCHECK_BACKUP_URL like update.sh.
set -euo pipefail
cd "$(dirname "$0")"
set -a; . ./.env; set +a
keep=${BACKUP_KEEP_DAYS:-30}

ping() {
    [ -n "${HEALTHCHECK_BACKUP_URL:-}" ] || return 0
    curl -fsS -m 10 --retry 3 -o /dev/null "$HEALTHCHECK_BACKUP_URL$1" || true
}
trap 'ping /fail' ERR

ping /start
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p backups
docker compose exec -T db pg_dump -U critters -Fc critters > "backups/critters-$stamp.dump.part"
mv "backups/critters-$stamp.dump.part" "backups/critters-$stamp.dump"
if [ -d ../data/raw/rosters/official ]; then
    tar -czf "backups/rosters-$stamp.tar.gz" -C .. data/raw/rosters/official
fi
find backups -type f -mtime +"$keep" -delete
if [ -n "${BACKUP_REMOTE:-}" ]; then
    rclone copy backups "$BACKUP_REMOTE"
    rclone delete --min-age "${keep}d" "$BACKUP_REMOTE"
fi
ls -lh backups | tail -n 3
ping ""
