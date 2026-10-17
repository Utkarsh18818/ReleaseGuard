FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
WORKDIR /app
COPY requirements-lock.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY backend ./backend
COPY fixtures ./fixtures
COPY demo ./demo
RUN pip install --no-cache-dir --no-deps .
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend/src
