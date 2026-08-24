"""Merge adapter LoRA ke bobot penuh (bf16) untuk deploy tanpa dependensi peft.

Merge WAJIB di atas base model non-quantized. Merge di atas bobot 4-bit
menghasilkan model rusak karena dequantize-nya lossy.

    python merge_adapter.py
    python merge_adapter.py --adapter outputs/.../checkpoint-225 --out outputs/.../merged-e3

Butuh ~10 GB RAM (CPU, bukan VRAM) dan menulis ~4.4 GB ke disk.

Prinsip: script ini tidak menyimpan satu pun angka konfigurasi sendiri. base model,
chat template, dan batas resolusi gambar semuanya dibaca dari folder adapter, karena
di situlah nilai yang BENAR-BENAR dipakai saat training tersimpan. Menyalin ulang
MIN/MAX_PIXELS ke sini akan bocor jadi bug tak terlihat begitu notebook diubah.
"""

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

BASE = Path(__file__).resolve().parent
DEFAULT_RUN = BASE / "outputs" / "qwen2vl-2b-nesto-lora"

# Penanda bahwa sebuah folder memang hasil merge kita, bukan folder lain yang
# kebetulan ditunjuk --out. Dipakai sebelum rmtree.
MERGE_MARKERS = {"config.json", "model.safetensors", "model.safetensors.index.json"}

# Ditulis ke folder hasil merge. Gunanya satu: membuktikan saat runtime bahwa
# yang di-mount service memang bobot fine-tuned, bukan base model atau hasil
# merge lain. Folder base dan folder merged isinya mirip sekali - tanpa berkas
# ini keduanya ter-load tanpa satu pun pesan error, cuma keluarannya yang beda.
MERGE_INFO = "nesto_merge_info.json"


def adapter_fingerprint(adapter: Path) -> str:
    """SHA-256 bobot adapter, dipotong. Menjawab "adapter versi mana yang menyatu"."""
    f = adapter / "adapter_model.safetensors"
    if not f.exists():
        return ""
    h = hashlib.sha256()
    with f.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def write_merge_info(out: Path, adapter: Path, model_id: str, adapter_cfg: dict) -> None:
    (out / MERGE_INFO).write_text(json.dumps({
        "merged": True,
        "base_model": model_id,
        "adapter_dir": adapter.name,
        "adapter_path": str(adapter),
        "adapter_sha256_16": adapter_fingerprint(adapter),
        "lora_r": adapter_cfg.get("r"),
        "lora_alpha": adapter_cfg.get("lora_alpha"),
        "merged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=2), encoding="utf-8")


def resolve_out_dir(out: Path, force: bool) -> None:
    """Kosongkan folder tujuan, tapi tolak menghapus apa pun yang bukan hasil merge.

    Folder lama harus dihapus, bukan ditimpa: kalau merge sebelumnya menghasilkan
    beberapa shard dan yang sekarang hanya satu file, shard sisa membuat
    model.safetensors.index.json tidak konsisten dan model gagal di-load.
    """
    if not out.exists():
        return
    if any(out.iterdir()) and not (MERGE_MARKERS & {f.name for f in out.iterdir()}):
        if not force:
            raise SystemExit(
                f"{out} tidak tampak seperti hasil merge (tidak ada config.json/"
                f"model.safetensors) dan tidak kosong. Menolak menghapusnya.\n"
                f"Pakai --force kalau kamu memang yakin, atau pilih --out lain."
            )
        print(f"[--force] menghapus folder non-merge: {out}")
    else:
        print(f"Menghapus hasil merge lama: {out}")
    shutil.rmtree(out)


def load_processor(adapter: Path, model_id: str):
    """Ambil processor dari folder adapter kalau ada; kalau tidak, dari base model.

    Folder adapter hasil `processor.save_pretrained()` di notebook sudah memuat
    min_pixels/max_pixels (tersimpan sebagai size.shortest_edge/longest_edge) dan
    chat template yang identik dengan training. Memakainya berarti nol duplikasi
    konfigurasi dan nol kebutuhan jaringan.
    """
    if (adapter / "processor_config.json").exists():
        print(f"Processor: dari adapter ({adapter.name})")
        return AutoProcessor.from_pretrained(adapter)
    print(f"Processor: dari base model {model_id} "
          f"(adapter tidak menyimpan processor -- cek batas resolusinya sendiri)")
    return AutoProcessor.from_pretrained(model_id)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adapter", type=Path, default=DEFAULT_RUN / "adapter")
    ap.add_argument("--out", type=Path, default=DEFAULT_RUN / "merged")
    ap.add_argument("--model-id", default=None,
                    help="default: base_model_name_or_path dari adapter_config.json")
    ap.add_argument("--force", action="store_true",
                    help="izinkan menghapus folder --out yang bukan hasil merge")
    args = ap.parse_args()

    cfg_path = args.adapter / "adapter_config.json"
    if not cfg_path.exists():
        raise SystemExit(f"Adapter tidak ditemukan: {cfg_path}")
    adapter_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    trained_on = adapter_cfg.get("base_model_name_or_path")

    # Merge ke base yang berbeda dari base saat training menghasilkan model yang
    # ter-load tanpa error tapi keluarannya sampah -- jadi ini dijadikan hard stop.
    model_id = args.model_id or trained_on
    if model_id is None:
        raise SystemExit("adapter_config.json tidak punya base_model_name_or_path; "
                         "berikan --model-id secara eksplisit.")
    if trained_on and model_id != trained_on:
        raise SystemExit(
            f"--model-id ({model_id}) beda dari base saat training ({trained_on}).\n"
            f"Merge lintas base menghasilkan model rusak tanpa pesan error. "
            f"Hapus --model-id, atau perbaiki adapter_config.json kalau base-nya "
            f"memang cuma pindah path."
        )

    resolve_out_dir(args.out, args.force)

    print(f"Load base bf16 di CPU: {model_id}")
    base = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id, dtype=torch.bfloat16, device_map="cpu",
    )

    print(f"Terapkan adapter: {args.adapter}  (r={adapter_cfg.get('r')}, "
          f"alpha={adapter_cfg.get('lora_alpha')})")
    merged = PeftModel.from_pretrained(base, args.adapter).merge_and_unload()

    print(f"Simpan ke: {args.out}")
    merged.save_pretrained(args.out)
    load_processor(args.adapter, model_id).save_pretrained(args.out)
    write_merge_info(args.out, args.adapter, model_id, adapter_cfg)

    size_gb = sum(f.stat().st_size for f in args.out.rglob("*") if f.is_file()) / 1e9
    print(f"\nSelesai: {args.out} ({size_gb:.2f} GB)")
    for f in sorted(args.out.iterdir()):
        print(f"  {f.name:40s} {f.stat().st_size / 1e6:9.2f} MB")
    print("\nVerifikasi sebelum dipakai -- jangan diasumsikan setara adapter:")
    print(f'  uv run python "AI Services/evaluate.py" --model-id "{args.out}" '
          f"--no-adapter --limit 40 --no-downstream")


if __name__ == "__main__":
    main()
