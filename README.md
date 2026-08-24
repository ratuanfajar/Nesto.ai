# Nesto AI

Foto sketsa teknis furnitur masuk, rencana potong triplek keluar. Model
vision-language (Qwen2-VL-2B + QLoRA) membaca dimensi dari gambar, rule engine
menerjemahkannya jadi part list, lalu 2D nesting menyusunnya di lembaran.

```
sketsa  ->  spesifikasi JSON  ->  part list (mm)  ->  layout potong + waste %
            Tahap 1              Tahap 3            Tahap 4
```

## Isi repo

| Folder | Isi |
|---|---|
| [`AI Services/`](AI%20Services/) | riset: generator dataset, fine-tuning, evaluasi, BOM & nesting engine |
| [`deploy/`](deploy/) | HTTP API yang membungkus keempat tahap, plus Dockerfile |
| [`Frontend/`](Frontend/) | aplikasi Android (Jetpack Compose) |

Logika inti hidup di `AI Services/*.py`. `deploy/` tidak menyalin satu pun aturan
bengkel atau prompt; semuanya diimpor dari sana sebagai paket `nesto_core`.

## Menjalankan

```bash
uv sync

# 1. bobot: adapter (152 MB) + base model -> folder merged (4.2 GB)
uv run python "AI Services/merge_adapter.py"
uv run python deploy/verify_model.py

# 2. service
cd deploy && docker compose up -d --build
curl localhost:8000/ready
```

Detail ada di [`AI Services/README.md`](AI%20Services/README.md) untuk sisi riset
dan [`deploy/README.md`](deploy/README.md) untuk sisi service.

## Bobot model tidak ada di repo ini

Repo hanya memuat kode, dataset, dan `eval_report.json`. Bobot hasil training
didistribusikan terpisah karena ukurannya:

| | Ukuran | Dari mana |
|---|---|---|
| Adapter LoRA | 152 MB | dikirim terpisah (HuggingFace Hub / Release / Drive) |
| Base Qwen2-VL-2B-Instruct | 4.4 GB | otomatis diunduh saat `merge_adapter.py` |
| Hasil merge | 4.2 GB | dibuat di mesin masing-masing, tidak pernah dikirim |

Yang perlu berpindah tangan hanya adapter. Isinya seluruh perubahan bobot hasil
fine-tuning; sisanya bobot publik yang sama untuk semua orang.

Setelah merge, `nesto_merge_info.json` mencatat sidik jari adapter yang menyatu.
Nilainya harus cocok dengan adapter sumber - kalau tidak, checkpoint yang dipakai
salah. `deploy/verify_model.py` memeriksa ini sekaligus menguji keluarannya.

## Prasyarat

Python 3.11, [uv](https://docs.astral.sh/uv/). Untuk inference: GPU NVIDIA
dengan ~5 GB VRAM (bf16) atau ~2.5 GB (`NESTO_LOAD_4BIT=true`). Langkah merge
berjalan di CPU dan butuh ~10 GB RAM.
