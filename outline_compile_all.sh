#!/usr/bin/env bash
#
# outline_compile_all.sh — cron entrypoint for the Outline document compiler.
#
# Deploys as-is: everything is located relative to this file's directory,
# so the whole repo can live anywhere on the target server (e.g. /opt/outline-compiler).
#
# Cron (on the server, as the user that owns the repo):
#
#   crontab -e
#   # then add:
#   0 2 * * *  /opt/outline-compiler/outline_compile_all.sh
#
#   (minute hour day month weekday — adjust the time as you like;
#    e.g. "17 6 * * *" = daily at 06:17. The script logs to <repo>/logs/cron.log
#    and skips a tick if a previous run is still going.)
#
# Config it reads, from this repo:
#   .env              OUTLINE_API_KEY, OUTLINE_API_URL, OUTLINE_EXPORT_DIR
#   collections.txt   one "slug  collection-id" per line
#
# Output:
#   $OUTLINE_EXPORT_DIR/<slug>/index.html   +   attachments/
#
# Manual runs (any extra args pass through to run_all.py, e.g. --check):
#   ./outline_compile_all.sh             # compile every collection in collections.txt
#   ./outline_compile_all.sh --check     # validate config, print plan, no network
#   ./outline_compile_all.sh --slug foo  # just one collection

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO"

# --- logging (append; rotate with logrotate if it grows) ---
LOG_DIR="$REPO/logs"
mkdir -p "$LOG_DIR"
exec >>"$LOG_DIR/cron.log" 2>&1

# --- single instance: skip if a previous run is still going ---
if command -v flock >/dev/null 2>&1; then
    exec 9>"$REPO/.cron.lock"
    if ! flock -n 9; then
        echo "[$(date -Is)] skipped: a previous run still holds the lock"
        exit 0
    fi
fi

# --- Python environment: reuse .venv, or bootstrap it on first run ---
PY="$REPO/.venv/bin/python"
if [ ! -x "$PY" ]; then
    echo "[$(date -Is)] no .venv found — bootstrapping (first run)"
    if command -v uv >/dev/null 2>&1; then
        uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
    else
        python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    fi
    if [ ! -x "$PY" ]; then
        echo "[$(date -Is)] FATAL: could not create .venv in $REPO"
        exit 1
    fi
fi

# --- compile every configured collection ---
echo "[$(date -Is)] starting compile run"
"$PY" "$REPO/run_all.py" "$@"
STATUS=$?
echo "[$(date -Is)] finished with status $STATUS"
exit $STATUS
