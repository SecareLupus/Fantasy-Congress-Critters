# The site and the API in one image. Build from the repo root:
#   docker build -t critters .
# The repo layout is kept under /app, so the pipeline finds its rulesets, presets and
# web/dist as it does in a checkout. Data (downloads, roster snapshots) lives in
# /app/data, a volume.

FROM node:22-slim AS web
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.15 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app/pipeline
# Dependencies first, so code changes don't reinstall them.
COPY pipeline/pyproject.toml pipeline/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY pipeline/ ./
RUN uv sync --frozen --no-dev
COPY --from=web /app/web/dist /app/web/dist
# Runs as uid 1000, which should own the data directory on the host.
RUN useradd --uid 1000 --home-dir /app --no-create-home critters && mkdir -p /app/data && chown critters /app/data
USER critters
EXPOSE 8000
# Only Caddy can reach the app, so it trusts Caddy's X-Forwarded-For.
CMD ["critters", "serve", "--host", "0.0.0.0", "--forwarded-allow-ips", "*"]
