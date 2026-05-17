FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install --no-cache-dir uv

WORKDIR /srv
COPY pyproject.toml .python-version* ./
RUN uv sync

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts
COPY tests ./tests

EXPOSE 8080
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
