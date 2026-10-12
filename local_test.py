from generator_v2 import generate_report

print("=== MEMULAI TEST LOKAL ===")

# Attendance September pdf
print("\n[Test 1] Menarik Data Absen (2026-09) -> PDF")
hasil_1 = generate_report(intent='tarik_absen', file_format='pdf', keyword='2026-09')
print(f"File disimpan di: {hasil_1}")

# All Inventory excel
print("\n[Test 2] Menarik Seluruh Data Inventaris -> Excel")
hasil_2 = generate_report(intent='tarik_inventaris', file_format='excel', keyword='null')
print(f"File disimpan di: {hasil_2}")

# Inventory laptop pdf
print("\n[Test 3] Menarik Data Inventaris (Keyword: Laptop) -> PDF")
hasil_3 = generate_report(intent='tarik_inventaris', file_format='pdf', keyword='Laptop')
print(f"File disimpan di: {hasil_3}")