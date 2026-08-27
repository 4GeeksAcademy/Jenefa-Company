#!/bin/sh
set -eu

cd /workspace

# Ensure dependencies are present when the repo bind mount overlays image layers.
npm install -w website
npm install -w web

npm run dev -w website -- --hostname 0.0.0.0 --port 3000 &
WEBSITE_PID=$!

npm run dev -w web -- --hostname 0.0.0.0 --port 3001 &
WEB_PID=$!

cleanup() {
  kill "$WEBSITE_PID" "$WEB_PID" 2>/dev/null || true
}

trap cleanup INT TERM

wait "$WEBSITE_PID" "$WEB_PID"
