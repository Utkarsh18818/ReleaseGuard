FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
RUN apt-get update && apt-get install -y --no-install-recommends redis-server && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-lock.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY backend ./backend
COPY fixtures ./fixtures
COPY environment/hosted.py ./environment/hosted.py
RUN pip install --no-cache-dir --no-deps . && useradd --create-home app && mkdir -p /app/.local/locks && chown -R app:app /app
USER app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend/src RELEASEGUARD_PUBLIC_DEMO=1 RELEASEGUARD_DEMO=0
EXPOSE 10000
CMD ["python", "environment/hosted.py"]
