FROM python:3.11-slim-bookworm

# Create non-root system identity
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/bash appuser

WORKDIR /app

COPY pyproject.toml README.md ./
COPY backend ./backend
COPY frontend ./frontend

RUN pip install --no-cache-dir streamlit httpx pandas && \
    chown -R appuser:appgroup /app

ENV PYTHONPATH="/app/backend/src:/app" \
    PYTHONUNBUFFERED="1"

USER appuser
EXPOSE 8501

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]

