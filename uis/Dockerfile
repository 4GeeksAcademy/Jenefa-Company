FROM node:20-alpine

RUN apk add --no-cache curl

WORKDIR /workspace

# ── Layer 1: Install root workspace manifest ──────────────────────────────
# Keep installation boundaries clean: each workspace installs only its own
# dependencies so Docker layer caching is maximised.
COPY package.json ./
COPY src/package.json ./src/package.json
COPY packages/shared/package.json ./packages/shared/package.json
COPY uis/website/package.json ./uis/website/package.json
COPY uis/web/package.json ./uis/web/package.json

# ── Layer 2: Install workspace dependencies ────────────────────────────────
# website  → public-facing patient portal (port 3000)
# web      → internal clinical / admin backoffice panel (port 3001)
RUN npm install -w website -w web

# ── Layer 3: Copy start script ─────────────────────────────────────────────
COPY uis/start.sh ./uis/start.sh
RUN chmod +x ./uis/start.sh

CMD ["/bin/sh", "/workspace/uis/start.sh"]
