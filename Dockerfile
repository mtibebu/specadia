FROM python:3.12-slim

LABEL description="Specadia: Requirements and Design Multi-Agent System"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    bash \
    gcc \
    g++ \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv && \
    git config --global --add safe.directory /app

WORKDIR /app

# Layer-cache deps before copying source
COPY pyproject.toml uv.lock ./

RUN uv venv /app/.venv && uv sync --frozen --no-install-project

COPY . .

RUN uv pip install -e . --no-deps

RUN mkdir -p runs .specadia/rag

ENTRYPOINT ["specadia"]
CMD ["--help"]
