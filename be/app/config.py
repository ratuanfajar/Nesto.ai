"""Konfigurasi service, seluruhnya dari environment variable."""

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
    model_dir: Path = field(default_factory=lambda: Path(
        os.getenv("NESTO_MODEL_DIR", "/models/merged")))

    load_4bit: bool = field(default_factory=lambda: _env_bool("NESTO_LOAD_4BIT", False))

    # Tolak start kalau folder model bukan hasil merge: salah mount = Qwen2-VL mentah.
    require_finetuned: bool = field(
        default_factory=lambda: _env_bool("NESTO_REQUIRE_FINETUNED", True))

    device: str = field(default_factory=lambda: os.getenv("NESTO_DEVICE", "cuda"))

    max_new_tokens: int = field(default_factory=lambda: _env_int("NESTO_MAX_NEW_TOKENS", 320))

    max_concurrent_inference: int = field(
        default_factory=lambda: _env_int("NESTO_MAX_CONCURRENCY", 1))

    warmup: bool = field(default_factory=lambda: _env_bool("NESTO_WARMUP", True))

    max_upload_bytes: int = field(
        default_factory=lambda: _env_int("NESTO_MAX_UPLOAD_BYTES", 12 * 1024 * 1024))

    cors_origins: List[str] = field(
        default_factory=lambda: _env_list("NESTO_CORS_ORIGINS", ["http://localhost:3000"]))

    api_key: str = field(default_factory=lambda: os.getenv("NESTO_API_KEY", ""))


settings = Settings()
