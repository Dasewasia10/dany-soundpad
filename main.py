import os
import time
import sounddevice as sd
import soundfile as sf
import customtkinter as ctk
import keyboard
import threading
import json
import pystray
from PIL import Image, ImageDraw
import socket
import sys
import requests
from bs4 import BeautifulSoup
import subprocess
import urllib.parse
import webbrowser

# --- SISTEM ANTI-GANDA & PEMANGGIL OTOMATIS ---
PORT_KUNCI = 54321

def dengarkan_bel_pintu(sock):
    """Berjalan di latar belakang untuk mendengar panggilan dari aplikasi kedua."""
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data.decode('utf-8') == "BANGUN":
                # Memanggil GUI ke depan menggunakan fungsi yang sudah ada
                app.after(0, bring_to_front)
        except Exception:
            pass

def cegah_ganda_atau_bangunkan():
    global lock_socket
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Mencoba menyewa port
        lock_socket.bind(('127.0.0.1', PORT_KUNCI))
        
        # Jika berhasil, ini adalah aplikasi PERTAMA. Mulai dengarkan bel pintu.
        threading.Thread(target=dengarkan_bel_pintu, args=(lock_socket,), daemon=True).start()
    except socket.error:
        # Jika gagal, ini adalah aplikasi KEDUA.
        # Jangan langsung mati, kirim pesan ke aplikasi pertama dulu!
        kirim_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        kirim_socket.sendto(b"BANGUN", ('127.0.0.1', PORT_KUNCI))
        kirim_socket.close()
        
        # Setelah pesan terkirim, aplikasi kedua bunuh diri dengan tenang
        sys.exit(0)

# --- KONFIGURASI UTAMA ---
VB_CABLE_DEVICE_ID = 7  
FOLDER_SUARA = "I:/Music/Soundboard"
KOLOM_MAKSIMAL = 2      
BATAS_KARAKTER = 32
CONFIG_FILE = "config.json" 

stop_event = threading.Event()
kategori_dict = {}
daftar_favorit = set()
tray_icon = None

# --- MANAJEMEN KONFIGURASI ---
def muat_konfigurasi():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("monitor", "off"), set(data.get("favorites", [])), data.get("volume", 0.8)
        except Exception:
            pass
    return "off", set(), 0.8

def simpan_konfigurasi(status_monitor, favs, vol):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"monitor": status_monitor, "favorites": list(favs), "volume": vol}, f)
    except Exception as e:
        print(f"Gagal menyimpan konfigurasi: {e}")

# --- LOGIKA AUDIO ---
def stream_audio(data, fs, device_id, volume):
    try:
        channels = data.shape[1] if len(data.shape) > 1 else 1
        chunk_size = int(fs * 0.05) 
        
        # Menerapkan volume slider (mengalikan array audio dengan persentase volume)
        data = data * volume

        with sd.OutputStream(samplerate=fs, device=device_id, channels=channels, dtype='float32') as stream:
            for i in range(0, len(data), chunk_size):
                if stop_event.is_set():
                    break  
                chunk = data[i:i+chunk_size]
                stream.write(chunk)
    except Exception:
        pass 

def _play_manager(file_path):
    stop_event.set()
    time.sleep(0.08) 
    stop_event.clear()

    try:
        data, fs = sf.read(file_path, dtype='float32')
        vol = slider_volume.get()
        
        threading.Thread(target=stream_audio, args=(data, fs, VB_CABLE_DEVICE_ID, vol), daemon=True).start()
        
        if toggle_var.get() == "on":
            threading.Thread(target=stream_audio, args=(data, fs, None, vol), daemon=True).start()
            
    except Exception as e:
        print(f"Gagal memutar audio: {e}")

def play_sound(file_path):
    threading.Thread(target=_play_manager, args=(file_path,), daemon=True).start()

def stop_all_sounds():
    stop_event.set()

# --- LOGIKA SYSTEM TRAY & JENDELA ---
def buat_ikon_tray():
    """Membuat gambar ikon sederhana untuk System Tray (Huruf DS)."""
    image = Image.new('RGB', (64, 64), color="#1976D2")
    d = ImageDraw.Draw(image)
    d.text((12, 12), "DS", fill="white", font=None, align="center")
    return image

def aksi_keluar_sepenuhnya(icon, item):
    """Menutup aplikasi sepenuhnya dari System Tray."""
    icon.stop()
    os._exit(0)  # Memaksa seluruh thread (termasuk hotkey) mati seketika

def aksi_tampilkan_kembali(icon, item):
    """Memunculkan aplikasi dari System Tray."""
    icon.stop()
    app.after(0, bring_to_front)

def sembunyikan_ke_tray():
    """Fungsi yang dipanggil saat user menekan tombol 'X' merah (Close)."""
    app.withdraw()  # Sembunyikan jendela
    image = buat_ikon_tray()
    menu = pystray.Menu(
        pystray.MenuItem('Tampilkan', aksi_tampilkan_kembali, default=True),
        pystray.MenuItem('Keluar / Quit', aksi_keluar_sepenuhnya)
    )
    global tray_icon
    tray_icon = pystray.Icon("DanySoundboard", image, "Dany Soundboard Pro", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

def bring_to_front():
    app.deiconify()
    app.attributes('-topmost', True)
    app.attributes('-topmost', False)
    app.focus_force()

def trigger_summon():
    app.after(0, bring_to_front)

# --- LOGIKA TAMPILAN & FAVORIT ---
def format_teks_tombol(nama_file, is_fav=False):
    nama_bersih = os.path.splitext(nama_file)[0].replace("_", " ").title()
    if len(nama_bersih) > BATAS_KARAKTER:
        nama_bersih = nama_bersih[:BATAS_KARAKTER-3] + "..."
    ikon = "⭐" if is_fav else "🔊"
    return f"{ikon} {nama_bersih}"

def toggle_favorite(nama_file, path_lengkap, btn):
    if nama_file in daftar_favorit:
        daftar_favorit.remove(nama_file)
        is_fav = False
    else:
        daftar_favorit.add(nama_file)
        is_fav = True
    
    simpan_konfigurasi(toggle_var.get(), daftar_favorit, slider_volume.get())

    warna_fg = "#FBC02D" if is_fav else ["#3a7ebf", "#1f538d"] 
    warna_hover = "#F9A825" if is_fav else ["#325882", "#14375e"]
    warna_teks = "black" if is_fav else ["#DCE4EE", "#DCE4EE"]

    btn.configure(
        text=format_teks_tombol(nama_file, is_fav),
        fg_color=warna_fg, hover_color=warna_hover, text_color=warna_teks,
        font=("Arial", 12, "bold" if is_fav else "normal")
    )

    if "⭐ Favorit" not in kategori_dict:
        kategori_dict["⭐ Favorit"] = []

    if is_fav:
        if not any(f[0] == nama_file for f in kategori_dict["⭐ Favorit"]):
            kategori_dict["⭐ Favorit"].append((nama_file, path_lengkap))
    else:
        kategori_dict["⭐ Favorit"] = [f for f in kategori_dict["⭐ Favorit"] if f[0] != nama_file]
    
    if not kategori_dict["⭐ Favorit"]:
        kategori_dict.pop("⭐ Favorit", None)

    list_kategori = []
    if "⭐ Favorit" in kategori_dict: list_kategori.append("⭐ Favorit")
    list_kategori.append("Semua Suara")
    list_kategori.extend(sorted([k for k in kategori_dict.keys() if k not in ["⭐ Favorit", "Semua Suara"]]))
    
    dropdown_kategori.configure(values=list_kategori)

    if dropdown_kategori.get() == "⭐ Favorit" and not is_fav:
        btn.destroy()
        if not kategori_dict.get("⭐ Favorit"):
            dropdown_kategori.set("Semua Suara")
            ganti_kategori("Semua Suara")

def ganti_kategori(pilihan_kategori):
    for widget in frame_scroll.winfo_children():
        widget.destroy()

    daftar_file = kategori_dict.get(pilihan_kategori, [])
    daftar_file.sort(key=lambda x: x[0])

    baris, kolom = 0, 0
    for nama_file, path_lengkap in daftar_file:
        is_fav = nama_file in daftar_favorit
        kwargs = {
            "fg_color": "#FBC02D" if is_fav else None,
            "text_color": "black" if is_fav else None,
            "hover_color": "#F9A825" if is_fav else None
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        btn = ctk.CTkButton(
            frame_scroll, text=format_teks_tombol(nama_file, is_fav), 
            width=220, height=40, anchor="w",
            font=("Arial", 12, "bold" if is_fav else "normal"),
            command=lambda f=path_lengkap: play_sound(f), **kwargs
        )
        btn.grid(row=baris, column=kolom, padx=12, pady=7, sticky="ew")
        btn.bind("<Button-3>", lambda e, nf=nama_file, pl=path_lengkap, b=btn: toggle_favorite(nf, pl, b))
        
        kolom += 1
        if kolom >= KOLOM_MAKSIMAL:
            kolom, baris = 0, baris + 1

    app.after(10, lambda: frame_scroll._parent_canvas.yview_moveto(0))

def muat_ulang_suara():
    global kategori_dict
    stop_all_sounds() 

    kategori_saat_ini = dropdown_kategori.get() if 'dropdown_kategori' in globals() else "Semua Suara"
    kategori_dict.clear()
    semua_file, file_favorit = [], []

    if os.path.exists(FOLDER_SUARA):
        file_root = []
        for f in os.listdir(FOLDER_SUARA):
            path_lengkap = os.path.join(FOLDER_SUARA, f)
            if os.path.isfile(path_lengkap) and f.endswith(('.ogg', '.wav')):
                tup = (f, path_lengkap)
                file_root.append(tup); semua_file.append(tup)
                if f in daftar_favorit: file_favorit.append(tup)
        
        if file_root: kategori_dict["Utama"] = file_root

        for item in os.listdir(FOLDER_SUARA):
            path_item = os.path.join(FOLDER_SUARA, item)
            if os.path.isdir(path_item):
                file_sub = []
                for f in os.listdir(path_item):
                    path_lengkap = os.path.join(path_item, f)
                    if os.path.isfile(path_lengkap) and f.endswith(('.ogg', '.wav')):
                        tup = (f, path_lengkap)
                        file_sub.append(tup); semua_file.append(tup)
                        if f in daftar_favorit: file_favorit.append(tup)
                if file_sub: kategori_dict[item.title()] = file_sub

    kategori_dict["Semua Suara"] = semua_file
    if file_favorit: kategori_dict["⭐ Favorit"] = file_favorit

    if semua_file:
        list_kategori = []
        if "⭐ Favorit" in kategori_dict: list_kategori.append("⭐ Favorit")
        list_kategori.append("Semua Suara")
        list_kategori.extend(sorted([k for k in kategori_dict.keys() if k not in ["⭐ Favorit", "Semua Suara"]]))
        
        dropdown_kategori.configure(values=list_kategori)
        
        if kategori_saat_ini in list_kategori:
            dropdown_kategori.set(kategori_saat_ini)
            ganti_kategori(kategori_saat_ini)
        else:
            target = "⭐ Favorit" if "⭐ Favorit" in list_kategori else "Semua Suara"
            dropdown_kategori.set(target)
            ganti_kategori(target)
    else:
        dropdown_kategori.configure(values=["Kosong"])
        dropdown_kategori.set("Kosong")
        ganti_kategori("Kosong")

def buka_jendela_unduh():
    """Jendela pop-up pencarian dan pengunduhan MyInstants yang canggih."""
    jendela_unduh = ctk.CTkToplevel(app)
    jendela_unduh.title("Unduh dari MyInstants")
    jendela_unduh.geometry("500x650")

    # 1. Mengikat jendela ini ke jendela utama agar tidak tenggelam di belakangnya
    jendela_unduh.transient(app)

    # 2. Tarik paksa ke depan
    jendela_unduh.attributes('-topmost', True)
    jendela_unduh.focus_force()

    # 3. Lepaskan status "selalu di atas" setelah 100 milidetik (0.1 detik)
    # Dengan begini, jendela sudah ada di depan, tapi browser tetap bisa menimpanya nanti
    jendela_unduh.after(100, lambda: jendela_unduh.attributes('-topmost', False))

    # --- VARIABEL STATE PENCARIAN ---
    halaman_saat_ini = 1
    keyword_saat_ini = ""
    
    # --- PANEL ATAS (Pencarian & Kategori) ---
    panel_atas_unduh = ctk.CTkFrame(jendela_unduh)
    panel_atas_unduh.pack(pady=10, padx=15, fill="x")
    
    # Baris 1: Kotak Pencarian
    entry_pencarian = ctk.CTkEntry(panel_atas_unduh, width=300, placeholder_text="Ketik kata kunci, lalu tekan Enter...")
    entry_pencarian.grid(row=0, column=0, padx=10, pady=10)
    
    btn_cari = ctk.CTkButton(panel_atas_unduh, text="🔍 Cari", width=80, command=lambda: mulai_pencarian_baru())
    btn_cari.grid(row=0, column=1, padx=(0, 10), pady=10)
    
    # Memicu pencarian dengan menekan tombol Enter di keyboard
    entry_pencarian.bind("<Return>", lambda e: mulai_pencarian_baru())
    
    # Baris 2: Pemilihan Kategori (Folder)
    label_kat = ctk.CTkLabel(panel_atas_unduh, text="Simpan ke Folder:")
    label_kat.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="e")
    
    dropdown_kategori_unduh = ctk.CTkOptionMenu(panel_atas_unduh, dynamic_resizing=False, width=200)
    dropdown_kategori_unduh.grid(row=1, column=1, padx=(0, 10), pady=(0, 10), sticky="w")
    
    def perbarui_dropdown_kategori():
        """Memindai folder untuk mendapatkan daftar kategori terkini."""
        opsi = ["Utama"]
        if os.path.exists(FOLDER_SUARA):
            for item in os.listdir(FOLDER_SUARA):
                if os.path.isdir(os.path.join(FOLDER_SUARA, item)):
                    opsi.append(item.title())
        opsi.append("+ Buat Kategori Baru...")
        dropdown_kategori_unduh.configure(values=opsi)
        
    perbarui_dropdown_kategori()
    dropdown_kategori_unduh.set("Utama")
    
    def on_kategori_berubah(pilihan):
        """Membuat folder baru secara instan jika opsi pembuat dipilih."""
        if pilihan == "+ Buat Kategori Baru...":
            dialog = ctk.CTkInputDialog(text="Masukkan nama folder kategori baru:", title="Kategori Baru")
            nama_baru = dialog.get_input()
            if nama_baru and nama_baru.strip():
                nama_baru = nama_baru.strip().title()
                # Membuat folder fisik di File Explorer
                os.makedirs(os.path.join(FOLDER_SUARA, nama_baru), exist_ok=True)
                perbarui_dropdown_kategori()
                dropdown_kategori_unduh.set(nama_baru)
            else:
                dropdown_kategori_unduh.set("Utama") # Batal
                
    dropdown_kategori_unduh.configure(command=on_kategori_berubah)
    
    # --- PANEL HASIL PENCARIAN (Scrollable) ---
    frame_hasil = ctk.CTkScrollableFrame(jendela_unduh)
    frame_hasil.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    def mulai_pencarian_baru():
        nonlocal halaman_saat_ini, keyword_saat_ini
        keyword = entry_pencarian.get().strip()
        if not keyword: return
            
        keyword_saat_ini = keyword
        halaman_saat_ini = 1
        
        # Bersihkan hasil pencarian lama
        for widget in frame_hasil.winfo_children():
            widget.destroy()
            
        label_loading = ctk.CTkLabel(frame_hasil, text="Mencari...", text_color="yellow")
        label_loading.pack(pady=20)
        jendela_unduh.update() # Paksa GUI memuat teks loading
        
        # Lempar proses pencarian ke background agar aplikasi tidak freeze
        threading.Thread(target=ambil_data_pencarian, args=(keyword_saat_ini, halaman_saat_ini, label_loading), daemon=True).start()

    def load_more():
        nonlocal halaman_saat_ini
        halaman_saat_ini += 1
        
        # Cari dan hapus tombol "Load More" lama sebelum merender yang baru
        for widget in frame_hasil.winfo_children():
            if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "Tampilkan Lebih Banyak 🔄":
                widget.destroy()
                
        label_loading = ctk.CTkLabel(frame_hasil, text="Memuat halaman selanjutnya...", text_color="yellow")
        label_loading.pack(pady=10)
        
        threading.Thread(target=ambil_data_pencarian, args=(keyword_saat_ini, halaman_saat_ini, label_loading), daemon=True).start()

    def ambil_data_pencarian(keyword, halaman, label_loading):
        """Scraping data dari MyInstants secara tersembunyi."""
        try:
            # urllib.parse digunakan agar spasi dan simbol di keyword aman dikirim ke URL
            keyword_aman = urllib.parse.quote_plus(keyword)
            url = f"https://www.myinstants.com/en/search/?name={keyword_aman}&page={halaman}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = requests.get(url, headers=headers)
            soup = BeautifulSoup(req.text, 'html.parser')
            
            hasil = soup.find_all("div", class_="instant")
            
            app.after(0, label_loading.destroy)
            
            if not hasil and halaman == 1:
                app.after(0, lambda: ctk.CTkLabel(frame_hasil, text="Suara tidak ditemukan!", text_color="red").pack(pady=20))
                return
                
            for item in hasil:
                nama_asli = item.find("a", class_="instant-link").text.strip()
                
                # --- TAMBAHAN: Ambil link halaman untuk Preview ---
                link_halaman = item.find("a", class_="instant-link")["href"]
                url_halaman = "https://www.myinstants.com" + link_halaman
                # -------------------------------------------------

                teks_onclick = item.find("button", class_="small-button")["onclick"]
                link_mp3 = teks_onclick.split("play('")[1].split("')")[0]
                url_download = "https://www.myinstants.com" + link_mp3
                
                # Kirim url_halaman juga ke fungsi render
                app.after(0, render_baris_hasil, nama_asli, url_download, url_halaman)
                
            # Jika mendapatkan hasil, kita asumsikan ada halaman berikutnya
            if len(hasil) > 0: 
                app.after(0, lambda: ctk.CTkButton(
                    frame_hasil, text="Tampilkan Lebih Banyak 🔄", fg_color="transparent", 
                    border_width=1, command=load_more
                ).pack(pady=15))
                
        except Exception as e:
            app.after(0, lambda: label_loading.configure(text="Gagal mengambil data dari internet!", text_color="red"))
            print(f"Error scraping: {e}")

    def render_baris_hasil(nama_asli, url_download, url_halaman):
        """Menggambar setiap baris suara beserta tombol Download dan Preview."""
        baris = ctk.CTkFrame(frame_hasil, fg_color="transparent")
        baris.pack(fill="x", pady=2)
        
        nama_bersih = "".join(c for c in nama_asli if c.isalnum() or c in " -_").strip()
        teks_tampil = nama_bersih if len(nama_bersih) < 28 else nama_bersih[:25] + "..."
        
        lbl_nama = ctk.CTkLabel(baris, text=teks_tampil, font=("Arial", 12), anchor="w")
        lbl_nama.pack(side="left", padx=5)
        
        # Tombol Unduh (Kanan)
        btn_dl = ctk.CTkButton(baris, text="⬇️ Unduh", width=65, height=25, fg_color="#2E7D32", hover_color="#1B5E20")
        btn_dl.pack(side="right", padx=5)
        
        # Tombol Preview (Tengah)
        btn_preview = ctk.CTkButton(
            baris, text="🌐 Preview", width=70, height=25, 
            fg_color="#F57C00", hover_color="#EF6C00", 
            command=lambda: webbrowser.open(url_halaman) # Langsung buka ke browser
        )
        btn_preview.pack(side="right", padx=5)
        
        btn_dl.configure(command=lambda: threading.Thread(target=proses_unduh, args=(nama_bersih, url_download, btn_dl), daemon=True).start())

    def proses_unduh(nama_bersih, url_download, btn_dl):
        """Mengunduh MP3, mengonversi ke WAV, menghapus MP3, dan me-refresh aplikasi."""
        app.after(0, lambda: btn_dl.configure(text="⏳...", state="disabled", fg_color="gray"))
        try:
            # 1. Tentukan target folder sesuai pilihan pengguna
            kategori_terpilih = dropdown_kategori_unduh.get()
            if kategori_terpilih == "Utama" or kategori_terpilih == "+ Buat Kategori Baru...":
                folder_tujuan = FOLDER_SUARA
            else:
                folder_tujuan = os.path.join(FOLDER_SUARA, kategori_terpilih)
                
            path_mp3 = os.path.join(folder_tujuan, f"{nama_bersih}.mp3")
            path_wav = os.path.join(folder_tujuan, f"{nama_bersih}.wav")
            
            # 2. Unduh file mentah
            with open(path_mp3, 'wb') as f:
                f.write(requests.get(url_download).content)
                
            # 3. Konversi format menggunakan FFmpeg
            perintah_ffmpeg = f'ffmpeg -i "{path_mp3}" -c:a pcm_s16le "{path_wav}" -y'
            subprocess.run(perintah_ffmpeg, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 4. Hapus MP3
            os.remove(path_mp3)
            
            # Ubah tombol menjadi tanda selesai
            app.after(0, lambda: btn_dl.configure(text="✔️ Selesai", fg_color="#1976D2"))
            
            # PENTING: Minta aplikasi utama untuk merefresh layarnya agar suara baru langsung masuk!
            app.after(0, muat_ulang_suara)
            
        except Exception as e:
            app.after(0, lambda: btn_dl.configure(text="❌ Gagal", fg_color="#c62828"))
            print(f"Eror unduh {nama_bersih}: {e}")
            
# --- INISIALISASI GUI UTAMA ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()

# PANGGIL FUNGSINYA DI SINI, SETELAH `app` DIBUAT!
# (Agar aplikasi pertama tahu 'app' itu apa saat disuruh bangun)
cegah_ganda_atau_bangunkan()

app.title("Dany Soundboard Pro")
app.geometry("650x550") 

# MENGUNCI UKURAN JENDELA UNTUK MENGHILANGKAN LAG RESIZE
app.resizable(False, False)

# CEGAT TOMBOL CLOSE (X) UNTUK SYSTEM TRAY
app.protocol('WM_DELETE_WINDOW', sembunyikan_ke_tray)

keyboard.add_hotkey('ctrl+space', trigger_summon)

status_monitor, daftar_favorit, vol_terakhir = muat_konfigurasi()

# --- PANEL KONTROL ATAS ---
panel_atas = ctk.CTkFrame(app)
panel_atas.pack(pady=10, padx=15, fill="x")

btn_refresh = ctk.CTkButton(
    panel_atas, text="🔄 REFRESH", fg_color="#1976D2", hover_color="#1565C0",
    font=("Arial", 12, "bold"), width=90, command=muat_ulang_suara
)
btn_refresh.grid(row=0, column=0, padx=(15, 5), pady=10)

# Tambahkan ini di panel_atas, bersebelahan dengan tombol Refresh
btn_unduh = ctk.CTkButton(
    panel_atas, text="⬇️ UNDUH SUARA", fg_color="#2E7D32", hover_color="#1B5E20",
    font=("Arial", 12, "bold"), width=120, command=buka_jendela_unduh
)
# Pastikan menyesuaikan posisi grid agar sejajar dengan komponen lainnya
btn_unduh.grid(row=1, column=0, padx=10, pady=10)

toggle_var = ctk.StringVar(value=status_monitor)
switch_monitor = ctk.CTkSwitch(
    panel_atas, text="🎧 Monitor", variable=toggle_var, onvalue="on", offvalue="off",
    font=("Arial", 12, "bold"), command=lambda: simpan_konfigurasi(toggle_var.get(), daftar_favorit, slider_volume.get())
)
switch_monitor.grid(row=0, column=1, padx=10, pady=10)

# Slider Volume
slider_volume = ctk.CTkSlider(
    panel_atas, from_=0.0, to=1.0, width=120,
    command=lambda v: simpan_konfigurasi(toggle_var.get(), daftar_favorit, v)
)
slider_volume.set(vol_terakhir)
slider_volume.grid(row=0, column=2, padx=10, pady=10)

label_vol = ctk.CTkLabel(panel_atas, text="Volume", font=("Arial", 10))
label_vol.grid(row=1, column=2, pady=(0, 5))

# Konfigurasi grid agar tombol STOP rata kanan
panel_atas.grid_columnconfigure(3, weight=1)

btn_panic = ctk.CTkButton(
    panel_atas, text="🛑 STOP AUDIO", fg_color="#c62828", hover_color="#9e1c1c",
    font=("Arial", 12, "bold"), width=110, command=stop_all_sounds
)
btn_panic.grid(row=0, column=4, padx=15, pady=10, sticky="e")

# --- PANEL DROPDOWN KATEGORI ---
panel_kategori = ctk.CTkFrame(app, fg_color="transparent")
panel_kategori.pack(pady=(0, 5), padx=15, fill="x")

label_kategori = ctk.CTkLabel(panel_kategori, text="Kategori Folder:", font=("Arial", 14, "bold"))
label_kategori.pack(side="left", padx=(5, 10))

dropdown_kategori = ctk.CTkOptionMenu(panel_kategori, dynamic_resizing=False, width=250, command=ganti_kategori)
dropdown_kategori.pack(side="left")

label_bantuan = ctk.CTkLabel(panel_kategori, text="(Klik Kanan: ⭐ Favorit)", font=("Arial", 12, "italic"), text_color="gray")
label_bantuan.pack(side="right", padx=15)

# --- KANVAS SCROLL UTAMA ---
frame_scroll = ctk.CTkScrollableFrame(app, fg_color="transparent")
frame_scroll.pack(fill="both", expand=True, padx=10, pady=5)
frame_scroll.grid_columnconfigure((0, 1), weight=1)

muat_ulang_suara()

app.mainloop()