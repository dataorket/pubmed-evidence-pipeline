FROM python:3.11-slim AS base

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system .

# ── User code (Dagster gRPC server) ──────────────────────────
FROM base AS user-code
COPY src/ /app/src/
COPY seed_partitions.py init_db.py /app/
ENV PYTHONPATH=/app
CMD ["sh", "-c", "python /app/init_db.py && python /app/seed_partitions.py ${PARTITION_START:-1200} ${PARTITION_END:-1210} && dagster api grpc -h 0.0.0.0 -p 4000 -m src.dagster_pipeline.definitions"]

# ── Dagster webserver / daemon base ──────────────────────────
FROM base AS dagster-base
COPY dagster.yaml /app/dagster.yaml
ENV DAGSTER_HOME=/app

# ── Streamlit dashboard ───────────────────────────────────────
FROM base AS streamlit
COPY src/ /app/src/
ENV PYTHONPATH=/app/src
CMD ["streamlit", "run", "src/web/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
