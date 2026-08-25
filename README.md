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
| [`ai-services/`](ai-services/) | riset: generator dataset, fine-tuning, evaluasi, BOM & nesting engine |
| [`be/`](be/) | HTTP API yang membungkus keempat tahap, plus Dockerfile |
| [`frontend/`](frontend/) | aplikasi Android (Jetpack Compose) |

Logika inti hidup di `ai-services/*.py`. `be/` tidak menyalin satu pun aturan
bengkel atau prompt; semuanya diimpor dari sana sebagai paket `nesto_core`.

## Menjalankan

```bash
uv sync

# 1. bobot: adapter (152 MB) + base model -> folder merged (4.2 GB)
uv run python "ai-services/merge_adapter.py"
uv run python be/verify_model.py

# 2. service (be + frontend) dari root repo
docker compose up -d --build
curl localhost:8000/ready
```

Untuk menjalankan backend saja: `cd be && docker compose up -d --build`.

Bobot dimuat sekali saat container start. Kalau `nesto-api` sudah jalan sebelum
folder `merged/` terisi, `docker compose up -d` tidak akan merestartnya karena
konfigurasi compose tidak berubah, dan `/ready` akan terus melaporkan model tidak
ditemukan. Paksa buat ulang containernya:

```bash
docker compose up -d --force-recreate nesto-api
curl localhost:8000/ready
```

`/ready` balas 503 selama bobot dimuat (~1-2 menit) dan menyertakan alasannya di
field `error`. Untuk memastikan inference benar-benar berjalan di GPU, pemakaian
VRAM harus naik ke ~5 GB:

```bash
docker exec nesto-api nvidia-smi
```

### APK

```bash
docker compose --profile build-fe up --build nesto-fe-builder
```

Alamat backend yang dipakai APK ditanam saat kompilasi, diambil dari
`WIFI_ADDRESS` di `.env` root: `10.0.2.2` untuk emulator, IP LAN laptop untuk HP
sejaringan, atau `127.0.0.1` bila memakai `adb reverse tcp:8000 tcp:8000` lewat
USB. Setiap perubahan alamat menuntut build ulang. Detailnya di
[`frontend/README.md`](frontend/README.md).

Detail ada di [`ai-services/README.md`](ai-services/README.md) untuk sisi riset
dan [`be/README.md`](be/README.md) untuk sisi service.

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
salah. `be/verify_model.py` memeriksa ini sekaligus menguji keluarannya.

## Prasyarat

Python 3.11, [uv](https://docs.astral.sh/uv/). Untuk inference: GPU NVIDIA
dengan ~5 GB VRAM (bf16) atau ~2.5 GB (`NESTO_LOAD_4BIT=true`). Langkah merge
berjalan di CPU dan butuh ~10 GB RAM.
