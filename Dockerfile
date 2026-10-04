FROM python:3.12.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
COPY src ./src
COPY docs/upstream ./docs/upstream
COPY dashboard ./dashboard
COPY configs ./configs
COPY scripts ./scripts
RUN pip install --no-cache-dir . && useradd -m appuser && mkdir -p /app/outputs /app/data && chown appuser /app/outputs /app/data
USER appuser
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')"
CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.maxUploadSize=20"]
