FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

WORKDIR /extension

RUN uv venv /opt/venv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH=/opt/venv/bin:$PATH

FROM base AS dev

COPY . .

RUN uv sync --frozen --no-cache --all-groups --no-install-workspace

CMD ["bash"]
