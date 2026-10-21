from sqlalchemy import create_engine
import pandas as pd
import random
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

print("Memulai pembuatan data Relasional (Tanpa Absensi)...")

# 1. GENERATE EMPLOYEE DATA

first_name = ["Budi", "Siti", "Andi", "Rina", "Joko", "Ayu", "Dimas", "Eka", "Fajar", "Gita", "Hendra", "Indah"]
last_name = ["Santoso", "Aminah", "Wijaya", "Marlina", "Susilo", "Pratama", "Sari", "Kusuma", "Nugroho", "Rahayu"]
division_list = ["IT Support", "Operasional", "HRD", "Keuangan", "Marketing", "Gudang"]

employee_data = []
for i in range(1, 101):
    full_name = f"{random.choice(first_name)} {random.choice(last_name)}"
    employee_data.append({
        "employee_id": f"EMP-{i:03d}",
        "full_name": full_name,
        "whatsapp_number": f"628{random.randint(100000000, 999999999)}",
        "division": random.choice(division_list),
        "role": "admin" if i <= 3 else "user"
    })

df_employees = pd.DataFrame(employee_data)
df_employees.to_sql('employees', engine, if_exists='append', index=False)
print(f"✅ Tabel Karyawan terbuat ({len(df_employees)} baris).")

# 2. GENERATE INVENTORY
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
        "item_code": f"INV-{prefix}-{i:04d}",
        "item_name": item_name,
        "category": category,
        "condition_status": random.choice(condition_list),
        "employee_id": random.choice(employee_data)["employee_id"] 
    })

df_inventory = pd.DataFrame(inventory_data)
df_inventory.to_sql('inventory', engine, if_exists='append', index=False)
print(f"✅ Tabel Inventaris terbuat ({len(df_inventory)} baris).")

print("🎉 Selesai! Database siap digunakan.")