FROM python:3.11-slim AS dev

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

# Source must be bind-mounted at /app — see docker-compose.override.yml
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


FROM python:3.11-slim AS production

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY app/ ./app/

RUN mkdir -p /app/data/decisions \
    && adduser --disabled-password --no-create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

# Single worker is fine for initial deployment; scale with --workers $(nproc) or gunicorn when needed
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
