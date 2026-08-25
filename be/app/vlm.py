"""Pembungkus model VL: load sekali, generate per gambar, serialisasi akses GPU."""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

# Diimpor, bukan disalin: prompt yang bergeser = akurasi turun tanpa pesan error.
from nesto_core.evaluate import DEFAULT_PROMPT

from .config import settings

log = logging.getLogger("nesto.vlm")


class ModelNotReady(RuntimeError):
    pass


class VLM:
    """Singleton pemegang model + processor; load lazy dan dilindungi lock."""

    def __init__(self) -> None:
        self._model = None
        self._processor = None
        self._load_lock = threading.Lock()
        self._gpu_lock = threading.Semaphore(settings.max_concurrent_inference)
        self.load_error: Optional[str] = None
        self.model_dir = settings.model_dir
        self.merge_info: Optional[dict] = None

    @property
    def ready(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return

            # Import ditunda ke sini supaya /health tetap menjawab walau bobot belum ada.
            import torch
            from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

            model_dir = Path(self.model_dir)
            if not (model_dir / "config.json").exists():
                raise ModelNotReady(
                    f"Model tidak ditemukan di {model_dir}. Jalankan "
                    f"`merge_adapter.py` lalu mount folder `merged/` ke path itu."
                )

            # Penanda dari merge_adapter.py: bukti bobot ini hasil merge, bukan base model.
            info_path = model_dir / "nesto_merge_info.json"
            if info_path.exists():
                self.merge_info = json.loads(info_path.read_text(encoding="utf-8"))
                log.info("Bobot fine-tuned: base=%s adapter=%s (%s) merged_at=%s",
                         self.merge_info.get("base_model"),
                         self.merge_info.get("adapter_dir"),
                         self.merge_info.get("adapter_sha256_16"),
                         self.merge_info.get("merged_at"))
            elif settings.require_finetuned:
                raise ModelNotReady(
                    f"{model_dir} tidak punya nesto_merge_info.json, jadi tidak bisa "
                    f"dipastikan ini bobot fine-tuned. Jalankan ulang `merge_adapter.py`, "
                    f"atau set NESTO_REQUIRE_FINETUNED=false kalau memang sengaja "
                    f"menyajikan bobot dari sumber lain."
                )
            else:
                log.warning("%s tanpa nesto_merge_info.json - tidak terverifikasi "
                            "sebagai bobot fine-tuned (NESTO_REQUIRE_FINETUNED=false).",
                            model_dir)

            quant = None
            if settings.load_4bit:
                from transformers import BitsAndBytesConfig
                quant = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                )

            t0 = time.perf_counter()
            log.info("Memuat model dari %s (4bit=%s)", model_dir, settings.load_4bit)

            # Dari folder model, agar min/max pixels persis sama dengan saat training.
            self._processor = AutoProcessor.from_pretrained(model_dir)
            self._processor.tokenizer.padding_side = "left"

            self._model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_dir,
                quantization_config=quant,
                dtype=torch.bfloat16,
                device_map={"": 0} if settings.device == "cuda" else settings.device,
                attn_implementation="sdpa",
            )
            self._model.eval()
            log.info("Model siap dalam %.1f detik", time.perf_counter() - t0)

    def resolution_limits(self) -> dict:
        """Batas resolusi efektif dari processor (untuk endpoint /v1/config)."""
        size = self._processor.image_processor.size
        return {
            "min_pixels": size.get("shortest_edge"),
            "max_pixels": size.get("longest_edge"),
            "prompt": DEFAULT_PROMPT,
        }

    def extract(self, image: Image.Image, max_new_tokens: Optional[int] = None) -> Tuple[str, float]:
        """Gambar sketsa -> teks mentah dari model. Kembalikan (teks, detik)."""
        if self._model is None:
            raise ModelNotReady("Model belum dimuat")

        import torch
        from qwen_vl_utils import process_vision_info

        messages = [{"role": "user", "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": DEFAULT_PROMPT},
        ]}]

        text = self._processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)
        images, _ = process_vision_info(messages)
        inputs = self._processor(text=[text], images=images, padding=True, return_tensors="pt")
        inputs = inputs.to(self._model.device)

        t0 = time.perf_counter()
        with self._gpu_lock:
            with torch.inference_mode():
                out = self._model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens or settings.max_new_tokens,
                    do_sample=False,          # greedy: ekstraksi harus deterministik
                )
        elapsed = time.perf_counter() - t0

        trimmed = out[0][inputs.input_ids.shape[1]:]
        raw = self._processor.decode(trimmed, skip_special_tokens=True)
        return raw, elapsed


vlm = VLM()
