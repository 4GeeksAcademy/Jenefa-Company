FROM python:3.12-slim

# ── Runtime optimisation ──────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /services

# ── Install uv (fast dependency manager) ───────────────────────────────────
RUN pip install --no-cache-dir --quiet uv

# ── Layer 1: Install project dependencies ──────────────────────────────────
COPY services/api/requirements.txt ./api/requirements.txt
RUN uv pip install --no-cache -r api/requirements.txt

# ── Layer 2: Copy application code ─────────────────────────────────────────
COPY services/api/ ./api/
ENV PYTHONPATH=/:/services:/services/api

COPY services/celery_app.py /services/celery_app.py
# The API imports the shared data pipelines and incident analysis package.
COPY data/ /data/
COPY scripts/ /scripts/
COPY docs/ /docs/

# ── Layer 3: Mount points for hot-reload bind volumes ──────────────────────
# The docker-compose.yml bind-mounts ./services/ to /services/ so that
# code changes are reflected immediately via uvicorn --reload.

RUN groupadd --system hc-runtime \
    && useradd --system --gid hc-runtime --home-dir /nonexistent --shell /usr/sbin/nologin hc-runtime \
    && chown -R hc-runtime:hc-runtime /services /data /scripts /docs

USER hc-runtime

EXPOSE 8000

CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
