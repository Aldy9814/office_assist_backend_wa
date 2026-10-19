from generator_v2 import generate_report

print("=== MEMULAI TES LOKAL MYSQL & GENERATOR ===")

# # Simulasi 1: Skenario Tarik Absensi (Anggap saja Gemini sudah menghasilkan JSON ini)
# print("\n[Tes 1] Menarik Laporan Absensi PDF untuk 2026-09...")
# file_absen = generate_report(intent="tarik_absen", file_format="pdf", keyword="2026-09")
# if file_absen:
#     print(f"✅ Tes 1 Berhasil! File tersimpan di: {file_absen}")
# else:
#     print("❌ Tes 1 Gagal: Data tidak ditemukan atau error.")

# Simulasi 2: Skenario Tarik Inventaris Spesifik (Format Excel)
print("\n[Tes 2] Menarik Laporan Inventaris 'Monitor Dell' pdf...")
file_inventaris = generate_report(intent="tarik_inventaris", file_format="pdf", keyword="Monitor Dell")
if file_inventaris:
    print(f"✅ Tes 2 Berhasil! File tersimpan di: {file_inventaris}")
else:
    print("❌ Tes 2 Gagal: Data tidak ditemukan atau error.")

print("\n[Tes 3] Menarik Laporan Inventaris 'Monitor Dell' Excel...")
file_inventaris = generate_report(intent="tarik_inventaris", file_format="excel", keyword="keyboard")
if file_inventaris:
    print(f"✅ Tes 3 Berhasil! File tersimpan di: {file_inventaris}")
else:
    print("❌ Tes 3 Gagal: Data tidak ditemukan atau error.")

print("\n=== TES SELESAI ===")