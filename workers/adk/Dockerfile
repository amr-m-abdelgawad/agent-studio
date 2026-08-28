FROM python:3.12-slim

WORKDIR /app

COPY workers/adk /app/workers/adk

RUN pip install --no-cache-dir /app/workers/adk

ENV PYTHONUNBUFFERED=1
ENV TEMPORAL_HOST=temporal:7233
ENV TEMPORAL_NAMESPACE=studio-dev
ENV TEMPORAL_TASK_QUEUE=studio-default

CMD ["python", "-m", "studio_worker_adk.main"]
