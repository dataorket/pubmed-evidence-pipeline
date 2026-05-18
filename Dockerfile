FROM python:3.11-slim AS base

WORKDIR /app
RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system .

# ── User code (Dagster gRPC server) ──────────────────────────
FROM base AS user-code
COPY src/ /app/src/
ENV PYTHONPATH=/app/src
CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-m", "dagster_pipeline.definitions"]

# ── Dagster webserver / daemon base ──────────────────────────
FROM base AS dagster-base
COPY dagster.yaml /app/dagster.yaml
ENV DAGSTER_HOME=/app

# ── Streamlit dashboard ───────────────────────────────────────
FROM base AS streamlit
COPY src/ /app/src/
ENV PYTHONPATH=/app/src
CMD ["streamlit", "run", "src/web/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
