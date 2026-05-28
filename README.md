# Dany Soundboard Pro 🔊

Aplikasi soundboard ringan yang dibuat menggunakan Python. Berfungsi untuk menyalurkan suara langsung ke Discord/Game tanpa lag, mendukung Global Hotkeys, dan sistem Folder Kategori otomatis!

## Tahap 1: Persiapan (Wajib)
Sebelum menjalankan aplikasi ini, komputermu membutuhkan dua hal:
1. **Python:** Unduh dan instal Python dari [python.org](https://www.python.org/downloads/). *(PENTING: Saat instalasi, centang kotak "Add Python to PATH" di bagian bawah).*
2. **VB-Audio Virtual Cable:** Unduh dan instal dari [vb-audio.com](https://vb-audio.com/Cable/). Ini berfungsi sebagai kabel tak kasat mata untuk menyambungkan aplikasi ini ke Discord. Scroll ke bawah kalau ingin versi yang "gratis" (Donationware).

## Tahap 2: Pengaturan Windows & Discord
Agar suaramu (dari mikrofon asli) dan suara dari Soundboard bisa terdengar bersamaan:
1. Buka **Sound Control Panel** di Windows.
2. Ke tab **Recording** -> Klik kanan Microphone aslimu -> **Properties** -> Tab **Listen**.
3. Centang **"Listen to this device"**, lalu ubah *Playback through this device* ke **CABLE Input (VB-Audio Virtual Cable)**. Klik OK.
4. Buka Discord -> Settings -> Voice & Video.
5. Ubah **Input Device** menjadi **CABLE Output**.

## Tahap 3: Instalasi Sekali Klik!
1. Klik ganda file `setup.bat` di dalam folder ini.
2. Biarkan ia menginstal library yang dibutuhkan.
3. Saat diminta, masukkan **ID VB-Cable** yang muncul di layar hitam tersebut.
4. Masukkan **lokasi folder** tempat kamu menyimpan file suaramu (`.wav` atau `.ogg`).
5. Selesai! Akan muncul *shortcut* baru di Desktop-mu.

## Cara Penggunaan
* Klik ganda shortcut **Dany Soundboard** di Desktop.
* Aplikasi akan masuk ke pojok kanan bawah (System Tray) jika kamu tekan tombol X (Close).
* **Hotkeys:** Tekan `Ctrl + Space` kapan saja saat main game atau buka Discord untuk memanggil aplikasi ke depan layar!
* **Favorit:** Klik kanan pada tombol suara untuk menjadikannya favorit (⭐).