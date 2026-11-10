FROM python:3.11-slim-bookworm

# Create non-root system identity
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/bash appuser

# Install system dependencies: ODBC drivers, unixodbc, OpenMP for LightGBM
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    unixodbc \
    unixodbc-dev \
    libgomp1 \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
    && apt-get purge -y --auto-remove curl gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy packaging and backend source needed by setuptools
COPY pyproject.toml README.md ./
COPY backend ./backend
RUN pip install --no-cache-dir .

# Copy application layers
COPY database ./database
COPY configs ./configs
COPY scripts ./scripts
COPY infrastructure ./infrastructure

# Prepare runtime artifact directories and permissions
RUN mkdir -p /app/artifacts /app/models && \
    chown -R appuser:appgroup /app

ENV PYTHONPATH="/app/backend/src:/app" \
    PYTHONUNBUFFERED="1" \
    PYTHONDONTWRITEBYTECODE="1" \
    XS_BACKEND_HOST="0.0.0.0" \
    XS_BACKEND_PORT="8000"

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/ready')"

CMD ["uvicorn", "x_sentinel.main:app", "--host", "0.0.0.0", "--port", "8000"]

