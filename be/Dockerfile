# Build context = ROOT repo:  docker build -f be/Dockerfile .
# .dockerignore di root wajib aktif, kalau tidak bobot + dataset ikut terkirim.

# Stage 1: builder
# Wheel torch cu130 membundel runtime CUDA sendiri, jadi base image CUDA tidak perlu.
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Hanya untuk memasang transformers dari commit yang di-pin; tidak ikut ke runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY be/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Stage 2: runtime
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/srv \
    # Ke volume, supaya container baru tidak mengunduh ulang file processor.
    HF_HOME=/cache/huggingface \
    NESTO_MODEL_DIR=/models/merged

COPY --from=builder /opt/venv /opt/venv

WORKDIR /srv

# Dipisah dari layer dependensi supaya mengubah app/ tidak memicu reinstall torch.
COPY be/app /srv/app

# Dipakai apa adanya dari folder riset, supaya aturan bengkel tidak bercabang dua.
COPY ["ai-services/schema.py",         "/srv/nesto_core/"]
COPY ["ai-services/bom_engine.py",     "/srv/nesto_core/"]
COPY ["ai-services/nesting_engine.py", "/srv/nesto_core/"]
COPY ["ai-services/evaluate.py",       "/srv/nesto_core/"]
RUN touch /srv/nesto_core/__init__.py

# Non-root. Folder dibuat di sini agar mount volume tidak jadi milik root.
RUN useradd --create-home --uid 10001 nesto \
    && mkdir -p /cache/huggingface /models \
    && chown -R nesto:nesto /cache /models /srv
USER nesto

EXPOSE 8000

# /health (liveness), bukan /ready: container yang memuat bobot belum siap, belum mati.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=4).status==200 else 1)"

# 1 worker: tiap worker memuat salinan model sendiri ke VRAM yang sama.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
