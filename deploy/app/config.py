"""Konfigurasi service, seluruhnya dari environment variable.

Tidak ada satu pun angka model di sini yang di-hardcode ulang dari notebook.
Batas resolusi gambar (min/max pixels) sengaja TIDAK ada sebagai setting:
nilainya sudah tersimpan di `processor_config.json` dalam folder model hasil
merge, dan itulah satu-satunya sumber yang benar. Menyediakan env var untuk itu
berarti membuka jalan agar service membaca gambar pada resolusi berbeda dari
saat training - akurasi turun tanpa error apa pun.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return default if raw is None or not raw.strip() else int(raw)


def _env_list(name: str, default: List[str]) -> List[str]:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return [x.strip() for x in raw.split(",") if x.strip()]


@dataclass
class Settings:
    # Folder hasil `merge_adapter.py`. Di-mount sebagai volume, TIDAK ikut ke
    # dalam image: 4.4 GB bobot di image berarti setiap rebuild kode menyalin
    # ulang bobotnya dan registry-nya membengkak.
    model_dir: Path = field(default_factory=lambda: Path(
        os.getenv("NESTO_MODEL_DIR", "/models/merged")))

    # Muat model dalam 4-bit (~2.5 GB VRAM) atau bf16 penuh (~5 GB VRAM).
    # bf16 lebih cepat dan tanpa dependensi bitsandbytes; pakai 4-bit kalau
    # GPU dipakai bersama service lain.
    load_4bit: bool = field(default_factory=lambda: _env_bool("NESTO_LOAD_4BIT", False))

    # Menolak start kalau folder model bukan hasil merge_adapter.py. Folder base
    # model dan folder merged isinya nyaris identik: salah mount berarti service
    # menyajikan Qwen2-VL mentah - ter-load tanpa error, tapi tidak pernah
    # menghasilkan JSON sesuai skema. Lebih baik gagal keras saat startup.
    # Set false HANYA kalau kamu sengaja menyajikan bobot dari sumber lain.
    require_finetuned: bool = field(
        default_factory=lambda: _env_bool("NESTO_REQUIRE_FINETUNED", True))
    device: str = field(default_factory=lambda: os.getenv("NESTO_DEVICE", "cuda"))

    max_new_tokens: int = field(default_factory=lambda: _env_int("NESTO_MAX_NEW_TOKENS", 320))

    # Satu GPU = satu inference pada satu waktu. Request ke-2 menunggu di
    # semaphore, bukan bertabrakan jadi CUDA OOM. Naikkan hanya kalau VRAM lega
    # dan kamu sudah mengukur bahwa batch bersamaan memang lebih cepat.
    max_concurrent_inference: int = field(
        default_factory=lambda: _env_int("NESTO_MAX_CONCURRENCY", 1))

    # Panggil model sekali saat startup supaya request pertama dari user tidak
    # menanggung biaya kompilasi kernel CUDA (~10-20 detik).
    warmup: bool = field(default_factory=lambda: _env_bool("NESTO_WARMUP", True))

    max_upload_bytes: int = field(
        default_factory=lambda: _env_int("NESTO_MAX_UPLOAD_BYTES", 12 * 1024 * 1024))

    cors_origins: List[str] = field(
        default_factory=lambda: _env_list("NESTO_CORS_ORIGINS", ["http://localhost:3000"]))

    # Kalau di-set, semua endpoint /v1/* butuh header `X-API-Key`. Kosong = terbuka
    # (hanya aman kalau service tidak terekspos ke luar jaringan internal).
    api_key: str = field(default_factory=lambda: os.getenv("NESTO_API_KEY", ""))


settings = Settings()
