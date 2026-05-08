FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser -d /app -m appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser . .

# Download model files at build time — baked into image permanently
RUN python main.py download-files

USER appuser

EXPOSE 8000

CMD ["python", "main.py", "start"]
