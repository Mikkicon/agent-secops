FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation for faster startup times
ENV UV_COMPILE_BYTECODE=1 

COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
RUN uv sync --frozen --no-install-project --no-dev

COPY . .

# Install the project
RUN uv sync --frozen --no-dev

EXPOSE 8000

ENTRYPOINT ["uv", "run"]
CMD ["python", "-m", "tools.web"]
