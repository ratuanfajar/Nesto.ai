# Nesto AI Services

Pipeline dari **foto sketsa teknis** menjadi **rencana potong triplek**.

```
gambar sketsa
   |
   |  Tahap 1  finetune_qlora.ipynb      Qwen2-VL-2B + QLoRA
   v
JSON terstruktur  (schema.py)
   |
   |  Tahap 2  evaluate.ipynb            schema validity, MAE, error count
   v
   |  Tahap 3  bom_engine.ipynb          dekomposisi -> part list (mm)
   v
part list
   |
   |  Tahap 4  nesting_engine.ipynb      guillotine nesting -> lembar + waste %
   v
koordinat potong + kebutuhan bahan
```

## Isi folder

| File | Isi |
|---|---|
| `dataset_generator/generate_dataset.py` | generator 1500 sketsa sintetis + label JSON |
| `download_model.ipynb` | unduh bobot base model |
| `finetune_qlora.ipynb` | **Tahap 1** - fine-tune QLoRA, hasilnya `outputs/qwen2vl-2b-nesto-lora/adapter/` |
| `schema.py` | kontrak JSON (Pydantic) + `parse_model_output()` yang tahan pagar ```` ```json ```` |
| `evaluate.py` / `evaluate.ipynb` | **Tahap 2** - inference batch + seluruh metrik evaluasi |
| `bom_engine.py` / `bom_engine.ipynb` | **Tahap 3** - rule engine dimensi global -> part list |
| `nesting_engine.py` / `nesting_engine.ipynb` | **Tahap 4** - 2D cutting optimizer + visualisasi SVG |

| `merge_adapter.py` | adapter + base model -> bobot penuh siap deploy |

Logika ada di file `.py` (bisa di-import layanan lain), notebook `.ipynb` menjalankan
dan memvisualkannya langkah demi langkah. Notebook di-run dengan working directory
folder `ai-services` ini. `be/` mengimpor `schema.py`, `bom_engine.py`,
`nesting_engine.py`, dan `evaluate.py` sebagai paket `nesto_core` - keempatnya tidak
boleh dipindah tanpa menyesuaikan `be/Dockerfile`.

## Isi folder outputs

Folder `outputs/` tidak masuk git. Isinya berbeda-beda sifatnya:

| Isi | Ukuran | Sifat |
|---|---|---|
| `adapter/` | 152 MB | hasil training, tidak tergantikan - inilah yang didistribusikan |
| `merged/` | 4.2 GB | turunan, dibuat ulang oleh `merge_adapter.py` |
| `checkpoint-*/` | 213 MB | state resume training; bobot adapternya sama dengan `adapter/` |
| `eval_report.json` | 10 KB | laporan evaluasi, satu-satunya yang ikut ke git |
| `val_predictions.jsonl` | 164 KB | prediksi mentah, untuk skor ulang tanpa GPU |

## Distribusi adapter

Adapter berisi seluruh perubahan bobot hasil fine-tuning: 392 tensor LoRA pada
`q/k/v/o_proj` dan `gate/up/down_proj` di 28 layer bahasa. Vision encoder tidak ikut
dilatih (`exclude_modules: ".*visual.*"`), dan tidak ada token baru yang ditambahkan,
jadi tidak ada bobot yang tertinggal di luar folder ini.

Bobot base tidak pernah disentuh; yang disimpan hanya `(alpha/r) x B @ A`. Karena itu
141 MB cukup untuk mewakili perubahan pada model 2 miliar parameter, dan hanya folder
inilah yang perlu berpindah tangan:

```bash
huggingface-cli upload <user>/qwen2vl-2b-nesto-lora \
    outputs/qwen2vl-2b-nesto-lora/adapter . --private
```

Penerima menjalankan `python merge_adapter.py` - base model diunduh otomatis dari
HuggingFace, dan `nesto_merge_info.json` mencatat sidik jari adapter yang menyatu
supaya versi yang dipakai bisa dipastikan, bukan ditebak dari nama folder.

## Menjalankan lewat CLI

```bash
# Tahap 2 - evaluasi 100 sampel validasi (butuh GPU)
python evaluate.py --limit 100 --nest \
    --save-predictions outputs/val_predictions.jsonl \
    --report-json outputs/eval_report.json

# skor ulang tanpa GPU dari prediksi yang sudah tersimpan
python evaluate.py --predictions outputs/val_predictions.jsonl

# Tahap 3 - part list dari satu file JSON
python bom_engine.py dataset_generator/synthetic_furniture_dataset/ground_truth/synth_0001.json

# Tahap 4 - rencana potong + gambar layout
python nesting_engine.py dataset_generator/synthetic_furniture_dataset/ground_truth/synth_0001.json \
    --kerf 3 --algo guillotine --svg outputs/nesting.svg
```

## Metrik Tahap 2

- **Schema Validity Rate** (target > 98 %) beserta jumlah error dipecah per jenis:
  `json_decode`, `schema` (field hilang / tipe salah), `empty`.
- **MAE / MedAE / RMSE / max / bias** per field numerik, plus jumlah sampel yang
  meleset di luar toleransi ±0.5 cm dan ±1.0 cm.
- **Exact match & distribusi off-by-N** untuk jumlah ambalan / pintu / laci.
- **Akurasi kategorikal** + pasangan salah tebak yang paling sering.
- **Precision / recall drop pocket** (TP / FP / FN / TN).
- **Breakdown** per `furniture_type` dan per layout gambar.
- **Dampak hilir**: part list hasil prediksi dibandingkan part list ground truth -
  selisih jumlah keping, ukuran potong (mm), dan jumlah lembar triplek.

## Dataset v2 - perbaikan field ber-error tinggi

Evaluasi v1 menunjukkan empat field dengan error jauh di atas yang lain:
`plinth.height_cm`, `plinth.offset_cm`, `drop_pocket.depth_cm`, `drop_pocket.height_cm`.
Penyebabnya bukan model, tapi gambar: keempat angka itu **tidak pernah diberi garis
dimensi** sehingga model cuma bisa menebak prior (mis. selalu menjawab `8.0` untuk
tinggi plinth). Bukti pembandingnya `drop_pocket.length_cm` - satu-satunya field
pocket yang punya label - akurasinya 100 %.

Perubahan di `dataset_generator/generate_dataset.py`:

- **Isometrik**: dimensi tinggi plinth (kiri-depan) + setback plinth (depan-bawah);
  dimensi panjang & kedalaman drop pocket pada bidang atas; leader-note
  `POCKET DALAM <h> cm` untuk kedalaman turun pocket.
- **Multi-view**: tampak depan menggambar toe-kick sebagai *recess* ber-setback
  lengkap dengan dimensi tinggi & setback; tampak samping menampilkan pocket
  sebagai cekungan terbuka dengan dimensi tinggi & kedalaman; tampak atas
  mendapat dimensi kedalaman pocket.
- **Sampling**: tinggi/setback plinth tidak lagi konstan per `furniture_type`
  (dulu bookshelf selalu 8.0/2.0 - hafalan, bukan pembacaan), dan frekuensi
  drop pocket naik 0.5 -> 0.7 supaya sampelnya cukup untuk dilatih & diukur.
- `has_plinth=False` sekarang memaksa `height_cm = offset_cm = 0.0`; sebelumnya
  angka acak yang tak punya jejak visual apa pun ikut jadi target latih.

Dataset baru ada di `dataset_generator/synthetic_furniture_dataset_v2/`
(folder v1 sengaja tidak ditimpa). `finetune_qlora.ipynb` dan default
`evaluate.py` sudah menunjuk ke sana - **model perlu di-fine-tune ulang** karena
adapter lama dilatih pada gambar tanpa label-label ini.

## Asumsi konstruksi (Tahap 3)

Carcass "top & bottom menjepit dinding samping", plinth di bawah:

```
tinggi dinding samping = tinggi total - tebal top - tebal bottom - tinggi plinth
lebar ambalan          = panjang total - 2 x tebal samping
ukuran potong          = ukuran jadi - tebal edging per sisi yang di-edging
```

`eb = [top, right, bottom, left]`; sisi top/bottom sepanjang `length_mm`, sisi
left/right sepanjang `width_mm`. Semua aturan bengkel lain (tebal panel belakang,
setback ambalan, celah pintu, clearance rel laci) ada di `BOMConfig`.

## Asumsi nesting (Tahap 4)

- Lembaran standar 2440 x 1220 mm, kerf 3 mm, trim tepi opsional.
- `respect_grain=True` (default) mematikan rotasi demi arah serat seragam.
- Satu lembar tidak pernah mencampur material atau tebal berbeda.
- Guillotine BSSF-SAS dipakai sebagai default karena panel saw hanya bisa memotong
  lurus ujung-ke-ujung; MaxRects tersedia lewat `--algo maxrects`.
- Waste per unit furnitur wajar terlihat besar (panel belakang 4 mm memakai satu
  lembar penuh). Optimasi sesungguhnya terjadi saat part beberapa unit dipack bersama.
