# Build context = ROOT repo (bukan folder deploy/), karena image butuh
# "AI Services"/*.py. Selalu:  docker build -f deploy/Dockerfile .
# Pastikan .dockerignore di root aktif, kalau tidak 4.4 GB bobot + 1500 gambar
# dataset ikut terkirim sebagai build context.

# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
# Wheel torch dari index cu130 sudah membundel runtime CUDA-nya sendiri, jadi
# base image CUDA tidak diperlukan. Host hanya perlu driver NVIDIA + container
# toolkit. Ini menghemat beberapa GB dibanding nvidia/cuda:*-devel.
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# git dibutuhkan HANYA untuk memasang transformers dari commit yang di-pin.
# Karena itu dia tinggal di stage builder dan tidak ikut ke image akhir.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY deploy/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/srv \
    # Cache HF diarahkan ke volume: tanpa ini setiap container baru mengunduh
    # ulang file processor kalau ada yang belum lengkap di folder model.
    HF_HOME=/cache/huggingface \
    NESTO_MODEL_DIR=/models/merged

COPY --from=builder /opt/venv /opt/venv

WORKDIR /srv

# Layer kode dipisah dari layer dependensi (di atas) supaya mengubah app/
# tidak memicu reinstall torch 3 GB.
COPY deploy/app /srv/app

# Logika Tahap 3 & 4 dipakai apa adanya dari folder riset - tidak disalin-tempel
# ke dalam app/, supaya aturan bengkel tidak pernah bercabang jadi dua versi.
COPY ["AI Services/schema.py",         "/srv/nesto_core/"]
COPY ["AI Services/bom_engine.py",     "/srv/nesto_core/"]
COPY ["AI Services/nesting_engine.py", "/srv/nesto_core/"]
COPY ["AI Services/evaluate.py",       "/srv/nesto_core/"]
RUN touch /srv/nesto_core/__init__.py

# Non-root. Folder cache & model dibuat di sini supaya mount volume tidak
# berakhir jadi milik root dan bikin permission error.
RUN useradd --create-home --uid 10001 nesto \
    && mkdir -p /cache/huggingface /models \
    && chown -R nesto:nesto /cache /models /srv
USER nesto

EXPOSE 8000

# Dipakai /health (liveness), bukan /ready: container yang masih memuat model
# 4.4 GB belum ready tapi jelas belum mati. start-period memberi kelonggaran
# untuk load + warmup.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=4).status==200 else 1)"

# 1 worker, bukan lebih: setiap worker memuat salinan model sendiri ke VRAM
# yang sama. Untuk menaikkan throughput, tambah GPU/replika - bukan worker.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
