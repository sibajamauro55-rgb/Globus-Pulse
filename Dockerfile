FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config ./config
COPY templates ./templates
COPY src ./src

ENV PYTHONPATH=/app/src
ENV DATABASE_URL=sqlite:////app/data/pulse.db
VOLUME ["/app/data", "/app/outbound"]

CMD ["python", "-m", "pulse", "worker"]
