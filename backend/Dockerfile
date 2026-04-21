# syntax=docker/dockerfile:1.6
# Multi-stage build for the DeepShiva backend (Qdrant Cloud mode, no local LLM).

ARG PYTHON_VERSION=3.11-slim

# ============================
# Builder stage
# ============================
FROM python:${PYTHON_VERSION} AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /install

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch — explicit +cpu tag + PyTorch index to avoid the 2GB CUDA wheel
RUN pip install --prefix=/install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.2+cpu

COPY requirements.prod.txt ./
RUN pip install --prefix=/install --no-cache-dir -r requirements.prod.txt

# Pre-download the MiniLM embedding model so first request doesn't block
ENV SENTENCE_TRANSFORMERS_HOME=/install/hf_cache
RUN PYTHONPATH=/install/lib/python3.11/site-packages python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='/install/hf_cache')"

# ============================
# Runtime stage
# ============================
FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SENTENCE_TRANSFORMERS_HOME=/opt/hf_cache \
    HF_HOME=/opt/hf_cache \
    PORT=8000 \
    ENV=production

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        curl \
        ffmpeg \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /install/hf_cache /opt/hf_cache

# App code (context is backend/)
COPY --chown=app:app . /app

# Strip files that should never land in the image even if .dockerignore misses them
RUN rm -rf /app/localmodel /app/cache /app/tools/hotel_cache /app/tests \
    && chown -R app:app /opt/hf_cache

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
