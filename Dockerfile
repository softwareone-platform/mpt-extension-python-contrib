FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

WORKDIR /workspace

# Build toolchain for dependencies that ship only sdists with C extensions
# (e.g. mpt-extension-sdk -> openziti, hdrhistogram) on platforms without wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN uv venv /opt/venv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH=/opt/venv/bin:$PATH

FROM base AS dev

COPY . .

RUN uv sync --frozen --no-cache --all-groups --no-install-workspace

CMD ["bash"]
