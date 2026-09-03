# ============================================================
# Dockerfile — multi-stage otimizado com uv
# Uso:
#   docker build -t tg-forwarder .
#   docker compose up -d
# Mantem consumo <150MB (sem GUI), ideal para e2-micro
# ============================================================

# ---- Stage 1: builder ----
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependencias primeiro (cache eficiente)
COPY pyproject.toml uv.lock README.md ./
# uv.lock pode nao existir em forks antigos; fallback sem --frozen
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --extra daemon || \
    uv sync --no-install-project --extra daemon

# Copia o projeto e instala o pacote
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --extra daemon || uv sync --extra daemon

# ---- Stage 2: runtime ----
FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependencias minimas de runtime (sem build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY . .

# Garante diretorios de runtime (mesmo que volumes vazios)
RUN mkdir -p /app/data /app/account /app/downloads /app/delete

# Daemon headless por padrao; para GUI use outro CMD/target
CMD ["python", "-m", "telegram_forwarder.daemon.daemon"]
