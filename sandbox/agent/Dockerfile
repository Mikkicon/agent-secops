FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# UV faster startup
ENV UV_COMPILE_BYTECODE=1 

COPY pyproject.toml uv.lock ./

# Only dependencies without the code - cache layer
RUN uv sync --frozen --no-install-project --no-dev

# copy and trust mitmproxy's CA - TLS handshake to mitmproxy cert-verify
COPY mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitm.crt
# httpx/openai ignore the OS store
RUN update-ca-certificates && \
    cat /usr/local/share/ca-certificates/mitm.crt >> "$(uv run python -c 'import certifi; print(certifi.where())')"


COPY . .

# Install the code
RUN uv sync --frozen --no-dev

EXPOSE 8080

# create data volume if no -v
VOLUME /data

ENTRYPOINT ["uv", "run"]
CMD ["python", "-m", "agent"]

# cd sandbox/agent && docker run -p 8080:8080 -v "$(pwd)/unsafe-sandbox-data:/data" -t sandbox-agent
