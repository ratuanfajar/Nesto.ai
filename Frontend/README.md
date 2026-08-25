# Nesto App (Android)

Klien Android untuk Nesto AI: tukang memotret sketsa teknis, aplikasi mengirimnya
ke endpoint `/v1/analyze`, lalu menampilkan spesifikasi, part list, dan layout
potong di lembaran triplek.

Jetpack Compose, Hilt, Retrofit. Arsitektur berlapis:

```
presentation/   layar Compose + widget, dipisah per fitur
domain/         entity dan kontrak repository
data/           implementasi repository, Retrofit service, remote data source
global/         DI, navigasi, konstanta jaringan
utils/          ekspor PDF, data dummy
```

## Setup

Base URL dan API key tidak di-hardcode, tapi diambil dari file `.env` saat build
(dibaca di `app/build.gradle.kts`, diteruskan ke `BuildConfig`, lalu dipakai oleh
[`global/di/NetworkModule.kt`](app/src/main/java/com/example/nesto_app/global/di/NetworkModule.kt)
dan `NetworkConstants.kt`). Setiap orang yang clone repo ini perlu isi `.env`
miliknya sendiri — nilainya beda-beda tergantung jaringan dan konfigurasi
backend masing-masing.

```bash
cp .env.example .env
```

Isi dua variable berikut di `.env`:

```dotenv
WIFI_ADDRESS=10.0.2.2
NESTO_API_KEY=
```

| Variable | Fungsi | Wajib diisi? |
|---|---|---|
| `WIFI_ADDRESS` | Alamat backend yang diakses aplikasi | Ya, sesuaikan dengan cara testing (lihat di bawah) |
| `NESTO_API_KEY` | Dikirim sebagai header `X-API-Key` ke backend | Hanya kalau backend mewajibkan — harus sama persis dengan `NESTO_API_KEY` di `.env` backend |

### Menentukan `WIFI_ADDRESS`

**Emulator Android**, backend Docker jalan di laptop yang sama:
```dotenv
WIFI_ADDRESS=10.0.2.2
```
Alamat khusus bawaan emulator untuk menembus `localhost` milik host. Dari
emulator, host **tidak** bisa diakses lewat `localhost` — wajib `10.0.2.2`.
Nilai default `.env.example` sudah pakai ini, tidak perlu diubah kalau testing
dengan emulator.

**HP fisik**, satu jaringan WiFi dengan laptop:
```dotenv
WIFI_ADDRESS=192.168.x.x
```
Cari IP laptop dengan `ipconfig` (Windows), `ipconfig getifaddr en0` (macOS),
atau `hostname -I` (Linux).

**HP fisik via USB**, tanpa perlu satu WiFi:
```bash
adb reverse tcp:8000 tcp:8000
```
lalu `.env`:
```dotenv
WIFI_ADDRESS=localhost
```

> IP LAN dari router bersifat dinamis dan bisa berubah tiap laptop reconnect
> WiFi — kalau berubah, update `.env` dan build ulang.

## Menjalankan

Backend harus jalan lebih dulu — lihat [`../deploy/README.md`](../deploy/README.md).
Bentuk response yang diharapkan ada di
[`../deploy/examples/analyze_response.json`](../deploy/examples/analyze_response.json).

Buka folder ini di Android Studio, sync Gradle (supaya `BuildConfig` ter-generate
dari `.env`), lalu Run. Atau dari terminal:

```bash
./gradlew :app:installDebug
```

> Setiap kali `.env` diubah, wajib sync Gradle ulang (`Sync Now` di Android
> Studio, atau `./gradlew --stop` lalu build ulang dari terminal) supaya nilai
> baru ter-refresh ke `BuildConfig`.

Untuk build APK release tanpa Android Studio (mis. dari CI atau mesin lain
tanpa Android SDK terpasang), lihat build lewat Docker di bawah.

## Build lewat Docker

Cara ini tidak butuh Android SDK terpasang di laptop — semua proses compile
terjadi di dalam container. Backend perlu dijalankan lebih dulu sebelum build
FE, supaya APK yang dihasilkan bisa langsung dites.

```bash
cd deploy
cp .env.example .env          # sekali saja, isi NESTO_API_KEY kalau perlu
docker compose up -d nesto-api
docker compose --profile build-fe run --rm nesto-fe-builder
```

Penjelasan tiap baris:

1. `cd deploy` — masuk ke folder tempat `docker-compose.yml` berada.
2. `cp .env.example .env` — hanya perlu sekali di awal. Isi `NESTO_API_KEY` di
   file `.env` ini kalau backend memang mewajibkan API key, kosongkan kalau
   tidak.
3. menjalankan backend di background. Liat di deploy/README.MD, .
   Tunggu sampai statusnya `healthy` (`docker compose ps`) sebelum lanjut ke
   langkah berikutnya.
4. `docker compose --profile build-fe run --rm nesto-fe-builder` — build APK.
   Perintah ini pakai `--profile build-fe` karena service ini **tidak** ikut
   jalan otomatis lewat `docker compose up` biasa — sifatnya build sekali lalu
   selesai (`--rm` otomatis membersihkan container setelah selesai), bukan
   service yang nyala terus seperti backend.

Setelah build selesai, APK muncul di:

```
Frontend/build-output/app-release.apk
```

`WIFI_ADDRESS` dan `NESTO_API_KEY` yang dipakai saat build ini diambil dari
`Frontend/.env` (lihat bagian Setup di atas) — pastikan sudah diisi sebelum
menjalankan perintah build di atas.

Kalau build gagal dan perlu debug lebih dalam:

```bash
docker compose --profile build-fe run --rm nesto-fe-builder sh
```

Ini masuk ke shell container tanpa langsung menjalankan `gradlew`, sehingga
bisa dicek manual file yang ter-copy dan environment variable yang diteruskan.