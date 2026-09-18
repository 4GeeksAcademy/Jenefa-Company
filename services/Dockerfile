FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /services/api

ENV PYTHONPATH=/services:/services/api

RUN pip install --no-cache-dir uv

COPY api/requirements.txt ./requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

COPY api/ ./
COPY celery_app.py /services/celery_app.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
