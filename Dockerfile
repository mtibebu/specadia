FROM python:3.12-slim@sha256:09f7da3bc104798d0afb40bc08d23ab2da20a76130cec1f2ef170848f5d85217

LABEL description="Specadia: READ-MAS artifact to coding-agent contract converter"

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

RUN pip install --no-cache-dir uv==0.12.0 && \
    git config --global --add safe.directory /app

WORKDIR /app

# Layer-cache deps before copying source
COPY pyproject.toml uv.lock ./

RUN uv venv /app/.venv && uv sync --frozen --no-install-project

COPY . .

RUN uv pip install -e . --no-deps

RUN mkdir -p .specadia/contracts

ENTRYPOINT ["specadia"]
CMD ["--help"]
