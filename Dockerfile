# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS dashboard
WORKDIR /build
RUN npm install --global pnpm@12.18.0
COPY apps/dashboard/package.json apps/dashboard/pnpm-lock.yaml apps/dashboard/pnpm-workspace.yaml ./apps/dashboard/
RUN cd apps/dashboard && pnpm install --frozen-lockfile --ignore-scripts
COPY apps/dashboard ./apps/dashboard
COPY packages/design-system ./packages/design-system
ENV VITE_API_BASE_URL=same-origin
RUN cd apps/dashboard && pnpm build

FROM python:3.11-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FORWARDED_ALLOW_IPS=* \
    JAVO_PORT=8000 \
    JAVO_DATABASE_URL=sqlite+aiosqlite:////data/javo_agents.db \
    JAVO_SCHEDULER_DB_URL=sqlite:////data/scheduler_jobs.db \
    JAVO_CONTENT_ROOT=/data/content \
    JAVO_UPLOAD_DIR=/data/uploads \
    JAVO_BACKUP_DIR=/data/backups \
    JAVO_THUMBNAIL_DIR=/data/thumbnails \
    JAVO_DASHBOARD_DIST=/srv/dashboard \
    JAVO_MAX_CONCURRENT_AGENTS=1 \
    JAVO_AI_DAILY_BUDGET=0 \
    JAVO_AI_MONTHLY_BUDGET=0
RUN apt-get update \
    && apt-get install --yes --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 javo \
    && useradd --uid 10001 --gid javo --create-home javo \
    && mkdir -p /data /srv/runtime \
    && chown javo:javo /data
WORKDIR /srv/runtime
COPY services/local-runtime/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY services/local-runtime/app ./app
COPY skills /srv/skills
COPY --from=dashboard /build/apps/dashboard/dist /srv/dashboard
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"
CMD ["python", "-m", "app.cloud"]
