# Nesto AI - Service

HTTP API yang membungkus Tahap 1-4 dari folder `ai-services/`: foto sketsa masuk,
spesifikasi JSON + part list + rencana potong triplek keluar.

Yang ada di sini hanyalah **lapisan HTTP**. Tidak ada satu pun aturan bengkel,
prompt, atau angka konfigurasi yang disalin ulang ke `app/` - semuanya diimpor
dari `ai-services/*.py` (di dalam container namanya `nesto_core`). Kalau aturan
BOM berubah, ia berubah di satu tempat saja.

```
app/config.py      setting, seluruhnya dari environment variable
app/vlm.py         load model sekali, generate per gambar, serialisasi akses GPU
app/pipeline.py    perekat Tahap 1 -> 3 -> 4
app/api_models.py  bentuk request/response
app/main.py        endpoint
smoke_test.py      uji endpoint, dengan atau tanpa GPU
verify_model.py    buktikan bobot yang di-mount memang model fine-tuned
```

## Prasyarat

Bobot hasil merge harus sudah ada - image tidak memuatnya, folder itu di-mount
sebagai volume read-only. Kalau yang kamu punya baru folder `adapter/` (152 MB,
dikirim terpisah dari repo), langkah merge inilah yang mengubahnya jadi bobot penuh:

```bash
uv run python "ai-services/merge_adapter.py"
# -> ai-services/outputs/qwen2vl-2b-nesto-lora/merged/  (~4.4 GB)

uv run python be/verify_model.py          # wajib: bobotnya fine-tuned atau bukan?
```

Untuk mode GPU: driver NVIDIA + NVIDIA Container Toolkit di host (di Windows:
Docker Desktop dengan backend WSL2). VRAM yang dibutuhkan ~5 GB pada bf16, atau
~2.5 GB dengan `NESTO_LOAD_4BIT=true`.

## Menjalankan

```powershell
cd be
copy .env.example .env      # lalu isi NESTO_API_KEY di dalamnya
docker compose up -d --build
curl localhost:8000/health          # langsung 200
curl localhost:8000/ready           # 503 sampai model selesai dimuat (~1-2 menit)
```

Setting dibaca dari file `.env`, bukan dari env var di depan perintah:
`NESTO_API_KEY=x docker compose up` adalah sintaks bash dan **error** di PowerShell.

Compose membaca `.env` di direktori tempat perintahnya dijalankan. Dari folder
`be/` yang terpakai adalah `be/.env`; dari root repo yang terpakai adalah `.env`
root, dan `be/.env` diabaikan sepenuhnya. Isi file yang sesuai dengan cara
menjalankannya.

Dari seluruh variabel di bagian Environment variable, yang benar-benar bisa
diatur lewat `.env` hanya `NESTO_API_KEY`. Sisanya disetel langsung di blok
`environment:` pada `docker-compose.yml` dan menimpa isi `.env`; untuk
mengubahnya, sunting compose file-nya.

Dokumentasi interaktif: <http://localhost:8000/docs>.

`docker build` **harus** memakai root repo sebagai context, karena image butuh
`ai-services/*.py`. `docker-compose.yml` sudah mengatur ini (`context: ..`); kalau
membangun manual: `docker build -f be/Dockerfile -t nesto-ai:1.0.0 .` dari root.

### Tanpa Docker (pengembangan)

```bash
uv sync --extra serve
uv run python be/smoke_test.py        # endpoint CPU, model tidak dimuat
```

Untuk menjalankan server sungguhan dari venv riset, `nesto_core` perlu menunjuk ke
folder `ai-services` - `smoke_test.py` melakukannya lewat alias; di luar itu lebih
mudah memakai container.

### Tanpa GPU

Hapus blok `deploy:` di `docker-compose.yml` dan set `NESTO_DEVICE=cpu`. Jalan,
tapi ~20-60 detik per gambar - hanya masuk akal untuk uji fungsional.

## Environment variable

| Variabel | Default | Arti |
|---|---|---|
| `NESTO_MODEL_DIR` | `/models/merged` | folder hasil `merge_adapter.py` |
| `NESTO_LOAD_4BIT` | `false` | `true` = ~2.5 GB VRAM, lebih lambat |
| `NESTO_REQUIRE_FINETUNED` | `true` | tolak start kalau folder model bukan hasil `merge_adapter.py` |
| `NESTO_DEVICE` | `cuda` | `cpu` kalau host tanpa GPU |
| `NESTO_MAX_NEW_TOKENS` | `320` | cukup untuk satu spesifikasi JSON |
| `NESTO_MAX_CONCURRENCY` | `1` | inference paralel; >1 hanya kalau VRAM lega |
| `NESTO_WARMUP` | `true` | satu generate saat startup, agar request pertama tidak lambat |
| `NESTO_MAX_UPLOAD_BYTES` | `12582912` | batas ukuran unggahan (12 MB) |
| `NESTO_CORS_ORIGINS` | `http://localhost:3000` | daftar origin, dipisah koma |
| `NESTO_API_KEY` | kosong | kalau diisi, semua `/v1/*` butuh header `X-API-Key` |

### Memastikan yang disajikan adalah model fine-tuned

Folder base model dan folder hasil merge isinya nyaris identik - salah mount berarti
service menyajikan Qwen2-VL mentah: ter-load tanpa satu pun pesan error, hanya
keluarannya yang tidak pernah sesuai skema. Karena itu `merge_adapter.py` menulis
`nesto_merge_info.json` ke folder hasil merge, dan service **menolak start** kalau
berkas itu tidak ada (`NESTO_REQUIRE_FINETUNED=true`, default).

Model yang sedang disajikan bisa dicek tanpa masuk ke container:

```bash
curl -s localhost:8000/ready
# {"status":"ready","model_dir":"/models/merged","load_4bit":false,
#  "model":{"merged":true,"base_model":"Qwen/Qwen2-VL-2B-Instruct",
#           "adapter_dir":"adapter","adapter_sha256_16":"13bb66d864e2537a",
#           "lora_r":32,"lora_alpha":64,"merged_at":"..."}}
```

`adapter_sha256_16` adalah sidik jari `adapter_model.safetensors` - dengan itu
"adapter versi mana yang menyatu di bobot ini" bisa dijawab pasti, bukan ditebak
dari nama folder.

Penanda itu membuktikan *asal* bobot, bukan *perilakunya*. Untuk yang kedua,
`verify_model.py` menembakkan beberapa sampel validasi lewat `app/vlm.py` - jalur
kode yang sama dengan service - lalu membandingkan hasilnya ke ground truth:

```bash
uv run python be/verify_model.py              # 2 sampel di CPU, ~30 detik/gambar
uv run python be/verify_model.py --limit 10 --device cuda
```

Nol sampel yang lolos skema = pola khas base model mentah atau merge yang rusak;
skrip keluar dengan kode 1 dan bobot itu tidak boleh di-deploy.

Batas resolusi gambar sengaja **bukan** env var: nilainya dibaca dari
`processor_config.json` di folder model, karena itu satu-satunya nilai yang identik
dengan saat training. Membacanya pada resolusi lain menurunkan akurasi tanpa
memunculkan error apa pun.

## Endpoint

| Method | Path | Butuh GPU | Isi |
|---|---|---|---|
| GET | `/health` | - | liveness, selalu 200 selama proses hidup |
| GET | `/ready` | - | 503 selama model belum termuat |
| GET | `/v1/config` | - | seluruh default BOM & nesting, agar frontend tidak hardcode |
| POST | `/v1/extract` | ya | gambar -> spesifikasi JSON (Tahap 1) |
| POST | `/v1/bom` | tidak | spesifikasi -> part list (Tahap 3) |
| POST | `/v1/nest` | tidak | part list atau spesifikasi -> penempatan di lembaran (Tahap 4) |
| POST | `/v1/nest/svg` | tidak | sama, tapi balas `image/svg+xml` langsung |
| POST | `/v1/analyze` | ya | **endpoint utama frontend**: seluruh pipeline sekali jalan |

`/health` dipakai healthcheck container (liveness), `/ready` dipakai load balancer.
Keduanya berbeda dengan sengaja: container yang sedang memuat bobot 4.4 GB belum
siap menerima traffic, tapi jelas belum mati.

```bash
curl -X POST localhost:8000/v1/analyze \
  -H "X-API-Key: ganti-ini" \
  -F "image=@sketsa.jpg" \
  -F "include_nesting=true" -F "include_svg=true"
```

Balasannya memuat `spec`, `parts`, `bom_summary`, `nesting`, `raw_output` (teks asli
model, untuk debugging), dan `timings` per tahap.

## Kode error

Frontend sebaiknya bercabang pada field `error`, bukan pada teks pesan.

| HTTP | `error` | Penanganan yang disarankan |
|---|---|---|
| 400 | `invalid_image`, `empty_file` | minta user memilih berkas lain |
| 401 | `unauthorized` | `X-API-Key` salah atau tidak dikirim |
| 413 | `file_too_large` | kompres gambar di sisi klien |
| 422 | `model_output_invalid` | model gagal membaca sketsa - minta foto lain; `raw_output` disertakan untuk di-log |
| 422 | `invalid_options`, `missing_input` | bug di klien |
| 503 | `model_unavailable` | model belum siap atau gagal dimuat - coba lagi setelah `/ready` hijau |

Perhatikan `model_output_invalid` sengaja **422, bukan 500**: service-nya sehat,
yang gagal adalah pembacaan gambar oleh model.

Generasi bersifat greedy (`do_sample=False` di `app/vlm.py`), jadi deterministik:
gambar yang sama selalu menghasilkan keluaran yang sama, termasuk kegagalan yang
sama. Mengulang request dengan berkas yang identik tidak akan mengubah apa pun -
yang dibutuhkan adalah foto yang benar-benar berbeda. `raw_output` menunjukkan
apa yang sebenarnya ditulis model, dan seringkali kegagalannya berupa nama field
yang meleset, bukan angka yang tidak terbaca.

## Menguji

```bash
# tanpa GPU, tanpa Docker - endpoint CPU + perilaku saat model absen
uv run python be/smoke_test.py

# terhadap container yang jalan; dengan --image ikut menguji /v1/extract & /v1/analyze
uv run python be/smoke_test.py --url http://localhost:8000 --api-key ganti-ini \
    --image <foto-sketsa>.png
```

Gambar apa pun bisa dipakai. Untuk pengujian yang berarti, foto sketsa nyata dengan
label manual sebaiknya dikumpulkan di `ai-services/gold_test/` - folder itu tidak
disertakan di repo dan diisi sendiri.

## Catatan operasional

- **Satu worker, satu model.** Setiap uvicorn worker memuat salinan bobotnya sendiri
  ke VRAM yang sama. Untuk menaikkan throughput, tambah replika/GPU - bukan worker.
- **Inference diserialisasi** oleh semaphore di `vlm.py`, jadi dua request bersamaan
  mengantre alih-alih bertabrakan jadi CUDA OOM.
- **Bobot tidak masuk image.** Rebuild kode karena itu murah, dan registry tidak
  menyimpan 4.4 GB berulang kali.
- **`NESTO_CORS_ORIGINS` dan `NESTO_API_KEY` wajib diisi** sebelum service dijangkau
  dari luar jaringan internal.
- Model diganti dengan mengganti isi folder yang di-mount lalu me-restart container;
  tidak perlu rebuild image.

## Kalau model diperbarui

Adapter baru **tidak** otomatis lebih baik. Verifikasi hasil merge sebelum di-deploy -
bobot merge yang salah tetap ter-load tanpa error, hanya keluarannya yang buruk:

```bash
uv run python "ai-services/evaluate.py" \
    --model-id "ai-services/outputs/qwen2vl-2b-nesto-lora/merged" \
    --no-adapter --limit 40 --no-downstream
```

Bandingkan angkanya dengan evaluasi adapter di `ai-services/README.md`. Selisih
besar berarti langkah merge-nya yang bermasalah, bukan modelnya.

