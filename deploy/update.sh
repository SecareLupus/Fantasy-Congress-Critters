#!/usr/bin/env bash
# The daily update (`critters update`): new data, rescore, settle weeks. Run by
# critters-update.timer. Pings HEALTHCHECK_UPDATE_URL at the start and with the exit
# status, so a failure or a missed day emails you.
set -uo pipefail
cd "$(dirname "$0")"
set -a; . ./.env; set +a

ping() {  # ping <suffix> [body]
    [ -n "${HEALTHCHECK_UPDATE_URL:-}" ] || return 0
    curl -fsS -m 10 --retry 3 -o /dev/null --data-raw "${2:-}" "$HEALTHCHECK_UPDATE_URL$1" || true
}

ping /start
log=$(docker compose run --rm -T app critters update 2>&1)
status=$?
echo "$log"
ping "/$status" "$(tail -c 10000 <<<"$log")"
exit $status
