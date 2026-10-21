from generator_v2 import generate_report

print("=== MEMULAI TES LOKAL MYSQL & GENERATOR ===")

print("\n[Tes 2] Menarik Laporan Inventaris 'Monitor Dell' pdf...")
inventory_file = generate_report(intent="tarik_inventaris", file_format="pdf", keyword="Monitor Dell")
if inventory_file:
    print(f"✅ Tes 2 Berhasil! File tersimpan di: {inventory_file}")
else:
    print("❌ Tes 2 Gagal: Data tidak ditemukan atau error.")

print("\n[Tes 3] Menarik Laporan Inventaris 'keyboard' Excel...")
inventory_file = generate_report(intent="tarik_inventaris", file_format="excel", keyword="keyboard")
if inventory_file:
    print(f"✅ Tes 3 Berhasil! File tersimpan di: {inventory_file}")
else:
    print("❌ Tes 3 Gagal: Data tidak ditemukan atau error.")

print("\n=== TES SELESAI ===")