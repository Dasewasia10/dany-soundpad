import os
import subprocess
import shutil

FOLDER_SUARA = "."

def konversi_dan_naikkan_file():
    if not os.path.exists(FOLDER_SUARA):
        print(f"Folder '{FOLDER_SUARA}' tidak ditemukan.")
        return

    print("1. Memeriksa dan mengonversi file MP3 di dalam folder...")
    file_terkonversi = 0

    # Tahap 1: Konversi semua MP3 ke WAV terlebih dahulu di dalam folder
    for nama_file in os.listdir(FOLDER_SUARA):
        if nama_file.endswith(".mp3"):
            path_mp3 = os.path.join(FOLDER_SUARA, nama_file)
            nama_file_wav = os.path.splitext(nama_file)[0] + ".wav"
            path_wav = os.path.join(FOLDER_SUARA, nama_file_wav)

            perintah = f'ffmpeg -i "{path_mp3}" -c:a libvorbis -q:a 4 "{path_wav}" -y'

            try:
                subprocess.run(perintah, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  ✅ Berhasil Konversi: {nama_file} -> {nama_file_wav}")
                os.remove(path_mp3)  # Hapus MP3 setelah sukses jadi WAV
                file_terkonversi += 1
            except subprocess.CalledProcessError:
                print(f"  ❌ Gagal mengonversi: {nama_file}. Pastikan FFmpeg terinstal.")
            except Exception as e:
                print(f"  ⚠️ Gagal menghapus file MP3 asli {nama_file}: {e}")

    print(f"\n=== RINGKASAN ===")
    print(f"Total MP3 dikonversi : {file_terkonversi}")
    print("==================")

if __name__ == "__main__":
    konversi_dan_naikkan_file()