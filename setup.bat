@echo off
title Dany Soundboard Pro - Setup
color 0B

echo ===================================================
echo      SELAMAT DATANG DI SETUP DANY SOUNDBOARD
echo ===================================================
echo.
echo Pastikan Anda sudah menginstal Python dan VB-Audio Cable.
pause

echo.
echo [1/4] Membuat Virtual Environment (venv)...
if not exist "venv" (
    python -m venv venv
)

echo.
echo [2/4] Menginstal Library yang dibutuhkan...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo [3/4] Konfigurasi Perangkat Audio...
echo Menampilkan daftar perangkat audio di PC Anda:
echo ---------------------------------------------------
python cek_audio_devices.py
echo ---------------------------------------------------
echo.
echo CARI BARIS YANG BERTULISKAN: CABLE Input (VB-Audio Virtual Cable)
echo Pastikan memilih angka yang berakhiran MME atau DirectSound. Pastikan yang out nya lebih dari 0.
echo Jika Anda tidak melihat perangkat tersebut, pastikan VB-Audio Cable sudah terinstal dengan benar.
echo.
set /p user_id="Masukkan ANGKA ID perangkat tersebut: "
echo.
set /p user_folder="Masukkan lokasi folder suara Anda (contoh: D:\Musik\Soundboard): "

echo.
echo Menyimpan konfigurasi Anda ke dalam sistem...
:: Membuat script Python sementara untuk mengedit main.py secara otomatis
echo import re > setup_helper.py
echo import sys >> setup_helper.py
echo with open('main.py', 'r', encoding='utf-8') as f: code = f.read() >> setup_helper.py
echo code = re.sub(r'VB_CABLE_DEVICE_ID\s*=\s*\d+', f'VB_CABLE_DEVICE_ID = {sys.argv[1]}', code) >> setup_helper.py
echo code = re.sub(r'FOLDER_SUARA\s*=\s*r?[\x22\x27].*?[\x22\x27]', f'FOLDER_SUARA = r\x22{sys.argv[2]}\x22', code) >> setup_helper.py
echo with open('main.py', 'w', encoding='utf-8') as f: f.write(code) >> setup_helper.py

:: Menjalankan script pembantu dan menghapusnya
python setup_helper.py "%user_id%" "%user_folder%"
del setup_helper.py

echo.
echo [4/4] Membuat Shortcut di Desktop...
:: Memanfaatkan PowerShell untuk membuat shortcut dan memberinya hak Administrator (byte 0x15)
powershell -Command "$WShell = New-Object -ComObject WScript.Shell; $Shortcut = $WShell.CreateShortcut(\"$HOME\Desktop\Dany Soundboard.lnk\"); $Shortcut.TargetPath = \"$PWD\venv\Scripts\pythonw.exe\"; $Shortcut.Arguments = \"`\"$PWD\main.py`\"\"; $Shortcut.WorkingDirectory = \"$PWD\"; $Shortcut.Save(); $bytes = [System.IO.File]::ReadAllBytes(\"$HOME\Desktop\Dany Soundboard.lnk\"); $bytes[0x15] = $bytes[0x15] -bor 0x20; [System.IO.File]::WriteAllBytes(\"$HOME\Desktop\Dany Soundboard.lnk\", $bytes)"

echo.
echo ===================================================
echo SETUP SELESAI!
echo Silakan cek Desktop Anda untuk membuka aplikasinya.
echo ===================================================
pause