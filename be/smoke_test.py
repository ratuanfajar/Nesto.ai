"""Smoke test service Nesto, tanpa framework test.

    uv run python be/smoke_test.py                        # in-process, tanpa GPU/model
    uv run python be/smoke_test.py --url http://localhost:8000 --image sketsa.png

Mode in-process memetakan `nesto_core` ke "ai-services" persis seperti Dockerfile,
supaya layout import yang diuji sama dengan di container.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AI_SERVICES = ROOT / "ai-services"
DEFAULT_SPEC = (AI_SERVICES / "dataset_generator" / "synthetic_furniture_dataset_v2"
                / "ground_truth" / "synth_0001.json")

API_KEY = "smoke-test-key"
HEADERS = {"X-API-Key": API_KEY}

_failures: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {name}{'  ' + extra if extra else ''}")
    if not ok:
        _failures.append(name)
    return ok


def install_nesto_core_alias() -> None:
    """Petakan `nesto_core.*` -> "ai-services"/*.py, seperti COPY di Dockerfile."""
    pkg = types.ModuleType("nesto_core")
    pkg.__path__ = [str(AI_SERVICES)]
    sys.modules["nesto_core"] = pkg
    sys.path.insert(0, str(ROOT / "be"))


def make_client(url):
    if url:
        import httpx
        return httpx.Client(base_url=url.rstrip("/"), timeout=300.0)

    install_nesto_core_alias()
    # Env harus di-set sebelum app.config diimpor - Settings dibaca saat import.
    os.environ["NESTO_MODEL_DIR"] = str(ROOT / "be" / "__no_model__")
    os.environ["NESTO_WARMUP"] = "false"
    os.environ["NESTO_API_KEY"] = API_KEY

    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app, raise_server_exceptions=False)


def run_cpu_checks(c, spec, live):
    check("/health 200", c.get("/health").status_code == 200)

    r = c.get("/ready")
    if live:
        check("/ready 200 (service dengan model)", r.status_code == 200, r.text[:120])
    else:
        check("/ready 503 saat model absen", r.status_code == 503)

    if not live:
        check("/v1/config tanpa X-API-Key -> 401", c.get("/v1/config").status_code == 401)

    r = c.get("/v1/config", headers=HEADERS)
    if check("/v1/config 200", r.status_code == 200, r.text[:120]):
        check("config memuat bom_defaults & nest_defaults",
              {"bom_defaults", "nest_defaults"} <= set(r.json()))

    r = c.post("/v1/bom", headers=HEADERS, json={"spec": spec})
    parts = []
    if check("/v1/bom 200", r.status_code == 200, r.text[:200]):
        parts = r.json()["parts"]
        check("/v1/bom menghasilkan part", len(parts) > 0, f"({len(parts)} jenis part)")

    # Option salah nama harus ditolak, bukan diam-diam diabaikan.
    r = c.post("/v1/bom", headers=HEADERS, json={"spec": spec, "options": {"kerf_mm": 3}})
    check("/v1/bom menolak option asing -> 422", r.status_code == 422, r.text[:120])

    r = c.post("/v1/nest", headers=HEADERS, json={"parts": parts, "include_svg": True})
    if check("/v1/nest dari parts 200", r.status_code == 200, r.text[:200]):
        n = r.json()
        s = n["summary"]
        check("nesting menghasilkan lembar", len(n["sheets"]) > 0,
              f"({s.get('sheets_used')} lembar, waste {s.get('total_waste_pct')}%)")
        check("tidak ada part yang gagal ditempatkan", s.get("pieces_unplaced", 0) == 0,
              str(s.get("unplaced", "")))
        check("SVG ikut terkirim",
              bool(n.get("svg")) and n["svg"].lstrip().startswith("<svg"))

    check("/v1/nest dari spec 200",
          c.post("/v1/nest", headers=HEADERS, json={"spec": spec}).status_code == 200)
    check("/v1/nest tanpa parts maupun spec -> 422",
          c.post("/v1/nest", headers=HEADERS, json={}).status_code == 422)

    r = c.post("/v1/nest/svg", headers=HEADERS, json={"spec": spec})
    check("/v1/nest/svg balas image/svg+xml",
          r.status_code == 200
          and r.headers.get("content-type", "").startswith("image/svg+xml"),
          r.headers.get("content-type", ""))
    return parts


def run_gpu_checks(c, image_path):
    """Hanya dijalankan kalau --image diberikan: butuh model termuat."""
    blob = image_path.read_bytes()

    r = c.post("/v1/extract", headers=HEADERS,
               files={"image": (image_path.name, blob, "image/png")})
    if check("/v1/extract 200", r.status_code == 200, r.text[:300]):
        d = r.json()
        dim = d["spec"].get("overall_dimensions", {})
        check("spec punya dimensi global",
              all(k in dim for k in ("length_cm", "width_cm", "height_cm")),
              f"{dim.get('length_cm')}x{dim.get('width_cm')}"
              f"x{dim.get('height_cm')} cm, {d['inference_seconds']}s")

    r = c.post("/v1/analyze", headers=HEADERS,
               files={"image": (image_path.name, blob, "image/png")},
               data={"include_nesting": "true", "include_svg": "true"})
    if check("/v1/analyze 200", r.status_code == 200, r.text[:300]):
        d = r.json()
        check("analyze memuat parts + nesting",
              len(d["parts"]) > 0 and d["nesting"] is not None,
              f"{len(d['parts'])} part, {d['nesting']['summary'].get('sheets_used')} lembar, "
              f"total {d['timings']['total']}s")

    r = c.post("/v1/extract", headers=HEADERS,
               files={"image": ("rusak.png", b"ini jelas bukan PNG", "image/png")})
    check("gambar rusak -> 400", r.status_code == 400, r.text[:150])

    r = c.post("/v1/extract", headers=HEADERS,
               files={"image": ("kosong.png", b"", "image/png")})
    check("file kosong -> 400", r.status_code == 400, r.text[:150])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=None,
                    help="uji service yang sudah jalan, mis. http://localhost:8000")
    ap.add_argument("--api-key", default=None, help="X-API-Key untuk mode --url")
    ap.add_argument("--spec", type=Path, default=DEFAULT_SPEC,
                    help="ground truth JSON untuk menguji /v1/bom dan /v1/nest")
    ap.add_argument("--image", type=Path, default=None,
                    help="sketsa untuk menguji /v1/extract & /v1/analyze (butuh model)")
    args = ap.parse_args()

    if args.api_key is not None:
        HEADERS["X-API-Key"] = args.api_key
    if not args.spec.exists():
        print(f"Spec tidak ditemukan: {args.spec}")
        return 2
    if args.image and not args.image.exists():
        print(f"Gambar tidak ditemukan: {args.image}")
        return 2

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    live = args.url is not None
    print(f"Mode: {'live ' + args.url if live else 'in-process (tanpa model)'}")
    print(f"Spec: {args.spec.name}\n")

    client = make_client(args.url)
    # TestClient perlu context manager supaya lifespan (load model) ikut jalan.
    with client as c:
        run_cpu_checks(c, spec, live)
        if args.image:
            print()
            run_gpu_checks(c, args.image)
        elif live:
            print("\n(lewati /v1/extract & /v1/analyze - berikan --image untuk mengujinya)")

    print()
    if _failures:
        print(f"{len(_failures)} GAGAL: " + ", ".join(_failures))
        return 1
    print("SEMUA LULUS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
