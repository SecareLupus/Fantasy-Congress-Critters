#!/usr/bin/env bash
# Restore a backup made by backup.sh, replacing the database:
#   ./restore.sh backups/critters-STAMP.dump [backups/rosters-STAMP.tar.gz]
# The roster snapshots are unpacked over data/raw/rosters/official. The app is stopped
# while the database is replaced.
set -euo pipefail
cd "$(dirname "$0")"
dump=${1:?usage: restore.sh DUMP [ROSTERS_TAR]}
rosters=${2:-}
read -r -p "This replaces the database with $dump. Type 'restore' to go on: " answer
[ "$answer" = restore ] || { echo "stopped"; exit 1; }

docker compose stop app
docker compose exec -T db dropdb -U critters --if-exists critters
docker compose exec -T db createdb -U critters critters
docker compose exec -T db pg_restore -U critters -d critters --no-owner < "$dump"
if [ -n "$rosters" ]; then
    tar -xzf "$rosters" -C ..
fi
docker compose start app
echo "restored $dump${rosters:+ and $rosters}"
