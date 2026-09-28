#!/bin/sh
set -eu

cd /workspace

# ── Ensure dependencies are present ──────────────────────────────────────
# When the repo is bind-mounted over the image layer, node_modules may not
# exist. Re-run install so the container is always consistent with the
# current package.json state.
echo "[start.sh] Installing workspace dependencies (if needed)..."
npm install --no-audit --no-fund -w website -w web 2>&1 | tail -2

# ── Start website (public-facing patient portal) on port 3000 ────────────
echo "[start.sh] Starting website on http://0.0.0.0:3000..."
npm run dev -w website -- --hostname 0.0.0.0 --port 3000 &
WEBSITE_PID=$!

# ── Start web / backoffice (internal admin panel) on port 3001 ───────────
echo "[start.sh] Starting backoffice on http://0.0.0.0:3001..."
npm run dev -w web -- --hostname 0.0.0.0 --port 3001 &
WEB_PID=$!

# ── Trap: graceful shutdown on SIGINT / SIGTERM ──────────────────────────
cleanup() {
  echo "[start.sh] Shutting down..."
  kill "$WEBSITE_PID" "$WEB_PID" 2>/dev/null || true
  wait "$WEBSITE_PID" "$WEB_PID" 2>/dev/null || true
  echo "[start.sh] Both processes exited."
}

trap cleanup INT TERM

# ── Wait for either child to exit ────────────────────────────────────────
wait "$WEBSITE_PID" "$WEB_PID"
echo "[start.sh] Container stopped."
