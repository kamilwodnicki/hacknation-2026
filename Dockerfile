# CPU-only image. README organizatora wymaga Python 3.13+.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Biblioteki systemowe potrzebne OpenCV / ONNX Runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY config ./config
# Model detekcji tekstu OCR (PP-OCRv6 tiny, Apache-2.0) — w repozytorium, bez pobierania w trakcie działania
COPY models ./models
COPY src ./src
COPY ui ./ui
COPY tests ./tests

RUN mkdir -p /app/input /app/output

EXPOSE 8000 8501

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
