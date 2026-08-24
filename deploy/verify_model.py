"""Buktikan bahwa bobot yang akan disajikan deploy memang model hasil fine-tune.

Bedanya dengan `AI Services/evaluate.py`: yang di sana mengukur *kualitas* model di
banyak sampel. Yang di sini menjawab satu pertanyaan operasional dengan cepat -
"folder yang di-mount ini fine-tuned atau base model?" - dan menjawabnya lewat
`app/vlm.py`, jalur kode yang sama persis dengan yang dipakai service.

Base model mentah tidak akan pernah menghasilkan JSON yang lolos `schema.py`, jadi
"parse sukses + angka mendekati ground truth" sudah cukup jadi bukti.

    # default: 2 sampel validasi di CPU, tidak merebut VRAM
    uv run python deploy/verify_model.py

    # lebih banyak sampel, di GPU
    uv run python deploy/verify_model.py --limit 10 --device cuda

Jalankan ini setiap kali `merged/` diganti, SEBELUM container di-restart.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AI_SERVICES = ROOT / "AI Services"
DEFAULT_MODEL = AI_SERVICES / "outputs" / "qwen2vl-2b-nesto-lora" / "merged"
DEFAULT_DATASET = (AI_SERVICES / "dataset_generator" / "synthetic_furniture_dataset_v2")

# Dibandingkan ke ground truth. Sengaja hanya field yang punya garis dimensi di
# gambar - field tanpa label visual mengukur hafalan model, bukan pembacaannya.
COMPARED = [("overall_dimensions", "length_cm"),
            ("overall_dimensions", "width_cm"),
            ("overall_dimensions", "height_cm"),
            ("partitions", "shelves_count"),
            ("partitions", "doors_count"),
            ("partitions", "drawers_count")]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    ap.add_argument("--dataset", type=Path, default=DEFAULT_DATASET,
                    help="folder berisi val.jsonl, images/, ground_truth/")
    ap.add_argument("--limit", type=int, default=2, help="jumlah sampel validasi")
    ap.add_argument("--device", default="cpu",
                    help="cpu (default, ~30 detik/gambar) atau cuda (~2 detik)")
    args = ap.parse_args()

    if not (args.model_dir / "config.json").exists():
        print(f"Model tidak ditemukan: {args.model_dir}")
        return 2
    val_file = args.dataset / "val.jsonl"
    if not val_file.exists():
        print(f"val.jsonl tidak ditemukan: {val_file}")
        return 2

    # Env dibaca saat app.config diimpor, jadi harus di-set lebih dulu.
    os.environ["NESTO_MODEL_DIR"] = str(args.model_dir)
    os.environ["NESTO_DEVICE"] = args.device
    os.environ["NESTO_WARMUP"] = "false"

    # `nesto_core` -> "AI Services", pemetaan yang sama dengan Dockerfile.
    pkg = types.ModuleType("nesto_core")
    pkg.__path__ = [str(AI_SERVICES)]
    sys.modules["nesto_core"] = pkg
    sys.path.insert(0, str(ROOT / "deploy"))

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    from PIL import Image
    from app.vlm import vlm
    from nesto_core.schema import parse_model_output

    rows = [json.loads(line) for line in
            val_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = rows[:args.limit]

    vlm.load()
    if vlm.merge_info:
        print("Penanda merge:", json.dumps(vlm.merge_info, indent=2))
    print(f"\nMenguji {len(rows)} sampel validasi di {args.device}...")

    valid = exact = total_fields = 0
    for i, row in enumerate(rows, 1):
        img_name = Path(next(c["image"] for c in row["messages"][0]["content"]
                             if c["type"] == "image")).name
        img = Image.open(args.dataset / "images" / img_name).convert("RGB")
        gt = json.loads((args.dataset / "ground_truth"
                         / f"{Path(img_name).stem}.json").read_text(encoding="utf-8"))

        raw, secs = vlm.extract(img)
        print(f"\n[{i}/{len(rows)}] {img_name}  ({secs:.1f}s)")
        try:
            spec = parse_model_output(raw).model_dump()
        except Exception as exc:                              # noqa: BLE001
            print(f"  SKEMA GAGAL: {type(exc).__name__}: {str(exc)[:160]}")
            print(f"  raw: {raw[:300]}")
            continue

        valid += 1
        print(f"  skema VALID   furniture_type pred={spec['furniture_type']} "
              f"gt={gt['furniture_type']}")
        for grp, field in COMPARED:
            pred, truth = spec[grp][field], gt[grp][field]
            total_fields += 1
            same = pred == truth
            exact += same
            note = "sama" if same else f"SELISIH {abs(pred - truth):g}"
            print(f"  {grp}.{field:<15} pred={pred!s:<9} gt={truth!s:<9} {note}")

    print(f"\nSkema valid : {valid}/{len(rows)}")
    if total_fields:
        print(f"Field tepat : {exact}/{total_fields} ({100 * exact / total_fields:.0f}%)")

    if valid == 0:
        print("\nTIDAK LOLOS. Nol sampel menghasilkan JSON sesuai skema - ini pola khas "
              "base model mentah atau hasil merge yang rusak. Jangan di-deploy; "
              "jalankan ulang merge_adapter.py.")
        return 1
    if valid < len(rows):
        print("\nSebagian sampel gagal. Model jelas sudah fine-tuned, tapi kualitasnya "
              "perlu diukur dengan `AI Services/evaluate.py` sebelum dipakai produksi.")
        return 1
    print("\nLOLOS. Bobot ini berperilaku sebagai model fine-tuned dan aman di-mount "
          "ke service.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
