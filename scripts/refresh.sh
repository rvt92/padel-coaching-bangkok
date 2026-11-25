#!/usr/bin/env bash
# Daily refresh on the server: pull sessions from Book&Go (read-only) and rebuild the
# static files in place. The web server just serves this folder.
# Cron (server clock in Asia/Bangkok):  15 5 * * *  /var/www/padel/scripts/refresh.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
exec 9>/tmp/padel-refresh.lock
flock -n 9 || exit 0                       # skip if a previous run is still going
echo "== $(date '+%F %T')" >> logs/refresh.log
python3 scripts/build_sessions.py >> logs/refresh.log 2>&1
