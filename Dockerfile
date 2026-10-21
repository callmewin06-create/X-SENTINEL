# syntax=docker/dockerfile:1
FROM python:3.12.10-slim@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=4
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
# Keep third-party packages cached when application code or UI changes.
# pyproject.toml remains the only source of runtime dependency declarations.
RUN --mount=type=cache,target=/root/.cache/pip <<'SH'
set -eu
python - <<'PY'
from pathlib import Path
import tomllib

project = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))['project']
if {'dependencies', 'optional-dependencies'} & set(project.get('dynamic', [])):
    raise ValueError('Docker dependency export requires static dependencies')
requirements = list(project['dependencies'])
for extra in ('service', 'binary-v3'):
    requirements.extend(project['optional-dependencies'][extra])
if not requirements or not all(isinstance(item, str) and item.strip() for item in requirements):
    raise ValueError('Expected nonempty PEP 508 dependency declarations')
Path('/tmp/xsentinel-requirements.txt').write_text('\n'.join(requirements) + '\n', encoding='utf-8')
PY
python -m pip install -r /tmp/xsentinel-requirements.txt
rm /tmp/xsentinel-requirements.txt
SH
COPY src ./src
COPY docs/upstream ./docs/upstream
RUN --mount=type=cache,target=/root/.cache/pip python -m pip install --no-deps .
COPY dashboard ./dashboard
COPY .streamlit ./.streamlit
COPY configs ./configs
COPY scripts ./scripts
COPY database ./database
RUN useradd -m appuser && mkdir -p /app/outputs /app/data && chown appuser /app/outputs /app/data
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health',timeout=2)"
CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.maxUploadSize=50"]
