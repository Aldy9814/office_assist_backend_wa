import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('office_data.db')

first_name = ["Budi", "Siti", "Andi", "Rina", "Joko", "Ayu", "Dimas", "Eka", "Fajar", "Gita", "Hendra", "Indah", "Kevin", "Lestari", "Muhammad", "Nadia", "Oka", "Putri", "Rizky", "Tari"]
last_name = ["Santoso", "Aminah", "Wijaya", "Marlina", "Susilo", "Pratama", "Sari", "Kusuma", "Nugroho", "Rahayu", "Saputra", "Wulandari", "Setiawan", "Larasati", "Hidayat", "Permata", "Syahputra"]

employee = list(set([f"{random.choice(first_name)} {random.choice(last_name)}" for _ in range(150)]))[:100]

status_list = ["Hadir"] * 80 + ["Terlambat"] * 10 + ["Sakit"] * 5 + ["Izin"] * 5
attendance_data = []

start_date = datetime(2026, 1, 1)
end_date = datetime(2026, 9, 30)
delta = end_date - start_date

print("Creating Attendance and Inventory Table...")

for i in range(delta.days + 1):
    current_date = start_date + timedelta(days=i)
    if current_date.weekday() >= 5:
        continue

    date_str = current_date.strftime("%Y-%m-%d")
    for nama in employee:
        status = random.choice(status_list)

        if status == "Hadir":
            clock_in = f"0{random.randint(7,8)}:{random.randint(10, 59):02d}"
        elif status == "Terlambat":
            clock_in = f"09:{random.randint(10,59):02d}"
        else:
            clock_in = "-"

        desc = "Lengkap"
        if status == "Sakit": desc = "Surat Dokter"
        elif status == "Terlambat": desc = "Keperluan Pribadi"

        attendance_data.append({
            "tanggal": date_str,
            "nama_karyawan": nama,
            "status": status,
            "waktu_masuk": clock_in,
            "keterangan": desc
        })

df_attendance = pd.DataFrame(attendance_data)
df_attendance.to_sql('attendance', conn, if_exists='replace', index=False)
print(f"Sukses! {len(df_attendance):,} baris data absen telah dimasukkan")

# INVENTORY DATA
print("Membuat 500 data inventaris kantor")
item_category = {
    "Elektronik": ["Laptop Thinkpad T14", "Laptop Macbook Air", "Monitor Dell 24 Inch", "Mini PC Intel NUC", "iPad Pro 11"],
    "Furniture": ["Meja Kerja Ergonomis", "Kursi Jaring Hidrolik", "Lemari Arsip Besi", "Papan Tulis Kaca"],
    "Aksesoris": ["Mouse Wireless Logitech", "Keyboard Mechanical Keychron", "Headset Jabra", "Webcam Logitech C920"]
}

condition_list = ["Baik"] * 85 + ["Rusak Ringan"] * 10 + ["Dalam Perbaikan"] * 5
inventory_data = []

for i in range(1, 501):
    category = random.choice(list(item_category.keys()))
    item_name = random.choice(item_category[category])
    prefix = category[:3].upper()

    inventory_data.append({
        "kode_barang": f"INV-{prefix}-{i:04d}",
        "nama_barang": item_name,
        "kategori": category,
        "kondisi": random.choice(condition_list),
        "pemegang": random.choice(employee + ["IT Support", "Ruang Meeting A", "Gudang"])
    })

df_inventory = pd.DataFrame(inventory_data)
df_inventory.to_sql('inventaris', conn, if_exists='replace', index=False)
print(f"Sukses! {len(df_inventory)} baris data inventaris telah dimasukkan.")

conn.close()
print("Selesai! office_data.db siap untuk stress test.")

