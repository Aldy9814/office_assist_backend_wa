from sqlalchemy import create_engine
import pandas as pd
import random
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

print("Memulai pembuatan data Relasional (Tanpa Absensi)...")

# 1. GENERATE TABEL MASTER KARYAWAN
first_name = ["Budi", "Siti", "Andi", "Rina", "Joko", "Ayu", "Dimas", "Eka", "Fajar", "Gita", "Hendra", "Indah"]
last_name = ["Santoso", "Aminah", "Wijaya", "Marlina", "Susilo", "Pratama", "Sari", "Kusuma", "Nugroho", "Rahayu"]
divisi_list = ["IT Support", "Operasional", "HRD", "Keuangan", "Marketing", "Gudang"]

karyawan_data = []
for i in range(1, 101):
    nama = f"{random.choice(first_name)} {random.choice(last_name)}"
    karyawan_data.append({
        "id_karyawan": f"EMP-{i:03d}",
        "nama_lengkap": nama,
        "nomor_wa": f"628{random.randint(100000000, 999999999)}",
        "divisi": random.choice(divisi_list),
        "role": "admin" if i <= 3 else "user"
    })

df_karyawan = pd.DataFrame(karyawan_data)
df_karyawan.to_sql('karyawan', engine, if_exists='replace', index=False)
print(f"✅ Tabel Karyawan terbuat ({len(df_karyawan)} baris).")

# 2. GENERATE TABEL INVENTARIS
item_category = {
    "Elektronik": ["Laptop Thinkpad T14", "Monitor Dell 24 Inch", "Mini PC Intel NUC"],
    "Furniture": ["Meja Kerja Ergonomis", "Kursi Jaring Hidrolik", "Lemari Arsip Besi"],
    "Aksesoris": ["Mouse Wireless Logitech", "Keyboard Mechanical Keychron"]
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
        "id_karyawan": random.choice(karyawan_data)["id_karyawan"] # FK
    })

df_inventory = pd.DataFrame(inventory_data)
df_inventory.to_sql('inventaris', engine, if_exists='replace', index=False)
print(f"✅ Tabel Inventaris terbuat ({len(df_inventory)} baris).")

print("🎉 Selesai! Database siap digunakan.")