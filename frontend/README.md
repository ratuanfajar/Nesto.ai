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
atau `hostname -I` (Linux). Pastikan port 8000 diizinkan di firewall laptop untuk
profil jaringan yang sedang aktif.

**HP fisik via USB**, tanpa perlu satu WiFi:
```dotenv
WIFI_ADDRESS=127.0.0.1
```
Buka terowongannya setiap kali HP tersambung:
```bash
adb reverse tcp:8000 tcp:8000
```
Terowongan ini hilang tiap kabel dicabut atau HP reboot, jadi perintahnya perlu
diulang setelah menyambung lagi; cek dengan `adb reverse --list`. Gunakan
`127.0.0.1`, bukan `localhost` — `localhost` bisa resolve ke `::1` lebih dulu
sementara `adb reverse` hanya mendengarkan di IPv4.

> IP LAN dari router bersifat dinamis dan bisa berubah tiap laptop reconnect
> WiFi — kalau berubah, update `.env` dan build ulang.

## Menjalankan

Backend harus jalan lebih dulu — lihat [`../be/README.md`](../be/README.md).
Bentuk response yang diharapkan ada di
[`../be/examples/analyze_response.json`](../be/examples/analyze_response.json).

Buka folder ini di Android Studio, sync Gradle (supaya `BuildConfig` ter-generate
dari `.env`), lalu Run. Atau dari terminal:

```bash
./gradlew :app:installDebug
```

> Setiap kali `.env` diubah, wajib sync Gradle ulang (`Sync Now` di Android
> Studio, atau `./gradlew --stop` lalu build ulang dari terminal) supaya nilai
> baru ter-refresh ke `BuildConfig`.

Untuk build APK debug tanpa Android Studio (mis. dari CI atau mesin lain
tanpa Android SDK terpasang), lihat build lewat Docker di bawah.

## Build lewat Docker

Cara ini tidak butuh Android SDK terpasang di laptop — semua proses compile
terjadi di dalam container. Dijalankan dari **root repo**, tempat
`docker-compose.yml` berada.

```bash
docker compose up -d nesto-api
docker compose --profile build-fe up --build nesto-fe-builder
```

`--profile build-fe` wajib karena service ini tidak ikut jalan lewat
`docker compose up` biasa: sifatnya build sekali lalu selesai, bukan service yang
nyala terus seperti backend.

Setelah build selesai, APK muncul di:

```
frontend/build-output/app-debug.apk
```

### Build Docker membaca `.env` root, bukan `frontend/.env`

`frontend/.env` hanya berlaku untuk build Gradle lokal (Android Studio atau
`./gradlew`). Untuk build lewat Docker, nilainya diambil dari `.env` di **root
repo**, karena dua sebab:

- [`.dockerignore`](.dockerignore) mengecualikan `.env`, jadi file itu tidak
  pernah ikut masuk ke build context.
- `Dockerfile` menerima `WIFI_ADDRESS` dan `NESTO_API_KEY` sebagai `ARG` lalu
  menyetelnya jadi `ENV`, dan `envVar()` di `app/build.gradle.kts` memeriksa
  `System.getenv` lebih dulu sebelum melirik `.env`.

Compose mengisi `ARG` itu dari `.env` di direktori tempat perintahnya
dijalankan. Jadi untuk build Docker, isi `.env` root:

```dotenv
WIFI_ADDRESS=10.0.2.2
NESTO_API_KEY=
```

Kalau memakai keduanya, jaga agar `.env` root dan `frontend/.env` bernilai sama
supaya APK hasil Android Studio dan hasil Docker tidak berbeda alamat backend.

### Memastikan APK yang terpasang sudah yang terbaru

`API_BASE_URL` dan `NESTO_API_KEY` ditanam saat kompilasi lewat `BuildConfig`,
bukan dibaca saat runtime. Setiap perubahan `.env` atau kode klien menuntut build
ulang; APK lama akan tetap memakai nilai lamanya. Bandingkan waktu tulis file APK
dengan waktu perubahan terakhir agar tidak salah menduga:

```bash
ls -l build-output/app-debug.apk
```

Kalau build gagal dan perlu debug lebih dalam:

```bash
docker compose --profile build-fe run --rm nesto-fe-builder sh
```

Ini masuk ke shell container tanpa langsung menjalankan `gradlew`, sehingga bisa
dicek manual file yang ter-copy dan environment variable yang diteruskan.
