FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY packages/vault /app/packages/vault
COPY packages/object-store /app/packages/object-store
COPY apps/api /app/apps/api

RUN pip install --no-cache-dir /app/packages/vault /app/packages/object-store /app/apps/api

ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8080

EXPOSE 8080

CMD ["uvicorn", "studio_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
