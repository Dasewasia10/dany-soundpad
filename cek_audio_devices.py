import sounddevice as sd

print("=== DAFTAR PERANGKAT AUDIO ===")
print(sd.query_devices())
print("==============================")
print("\nPetunjuk:")
print("Cari baris yang bertuliskan 'CABLE Input' atau 'VB-Audio'.")
print("Angka yang berada di ujung paling kiri adalah ID perangkatmu.")