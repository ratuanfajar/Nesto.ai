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

## Menjalankan

Buka folder ini di Android Studio, lalu Run. Atau dari terminal:

```bash
./gradlew :app:installDebug
```

Base URL masih placeholder `https://example.com` di
[`global/di/NetworkModule.kt`](app/src/main/java/com/example/nesto_app/global/di/NetworkModule.kt)
dan `NetworkConstants.kt` masih kosong - keduanya perlu diisi sebelum aplikasi bisa
menjangkau service. Dari emulator, host diakses lewat `10.0.2.2`, bukan `localhost`.

Backend harus jalan lebih dulu - lihat [`../deploy/README.md`](../deploy/README.md).
Bentuk response yang diharapkan ada di
[`../deploy/examples/analyze_response.json`](../deploy/examples/analyze_response.json).
