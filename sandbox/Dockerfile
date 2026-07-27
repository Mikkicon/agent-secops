FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# UV faster startup
ENV UV_COMPILE_BYTECODE=1 

COPY pyproject.toml uv.lock ./

# Only dependencies without the code - cache layer
RUN uv sync --frozen --no-install-project --no-dev

COPY . .

# Install the code
RUN uv sync --frozen --no-dev

EXPOSE 8000

# create data volume if no -v
VOLUME /data

ENTRYPOINT ["uv", "run"]
CMD ["python", "-m", "tools.main"]

# cd sandbox && docker run -p 8000:8000 -v "$(pwd)/unsafe-sandbox-data:/data" -t flagship-sandbox
