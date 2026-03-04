# Stage 1: Build Microsandbox (Rust) - Only for target=microsandbox
FROM rust:1.75-slim-bookworm as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone specific version of microsandbox with volume support
WORKDIR /usr/src
RUN git clone https://github.com/TJKlein/microsandbox.git
WORKDIR /usr/src/microsandbox
# Build release binary
RUN cargo build --release

# -----------------------------------------------------------------------------
# Base Python Stage (for both python-only and microsandbox)
# -----------------------------------------------------------------------------
FROM python:3.10-slim-bookworm as python-only

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
# Additional dependencies
RUN pip install fastapi uvicorn httpx sse-starlette pydantic-monty
COPY . .
RUN pip install --no-cache-dir -e .

# Configure environment
ENV PYTHONPATH=/app
ENV SANDBOX_TYPE=opensandbox

# Default command
CMD ["python", "-m", "server.http_server"]

# -----------------------------------------------------------------------------
# Microsandbox Stage (includes rust binary)
# -----------------------------------------------------------------------------
FROM python-only as microsandbox

# Setup Microsandbox
COPY --from=builder /usr/src/microsandbox/target/release/msbserver /usr/local/bin/msbserver
ENV MICROSANDBOX_PATH=/usr/local/bin/msbserver
ENV SANDBOX_TYPE=microsandbox

CMD ["python", "-m", "server.http_server"]
