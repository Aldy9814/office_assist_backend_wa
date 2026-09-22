import pandas as pd
from firebase_admin import firestore
import os
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from xhtml2pdf import pisa
from datetime import datetime

from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment

def generate_report(intent, file_format, filter_val=None):
    try:
        db = firestore.client()
        print(f"Reading Data..")
        data_list=[]

        # Attendance
        if intent == 'tarik_absen':
            docs = db.collection('absen_dummy').stream()
            for doc in docs:
                doc_data = doc.to_dict()

                if 'tanggal' in doc_data:
                    date_str = doc_data['tanggal']
                    doc_month = date_str[:7]

                    if doc_month == filter_val:
                        data_list.append({
                            "Tanggal": date_str,
                            "ID_Karyawan": doc_data.get("id_karyawan", "-"),
                            "Nama": doc_data.get("nama", "-"),
                            "Departemen": doc_data.get("departemen", "-"),
                            "Status": doc_data.get("status", "-"),
                            "Jam_Masuk": doc_data.get("jam_masuk", "-"),
                            "Jam_Keluar": doc_data.get("jam_keluar", "-")
                        })
            filename_base = f"Laporan_Absen_{filter_val}"

        # Inventory
        elif intent == 'tarik_inventaris':
            docs = db.collection('inventaris_dummy').stream()
            for doc in docs:
                doc_data = doc.to_dict()

                cocok = True
                if filter_val and filter_val != "null":
                    keyword = filter_val.lower()

                    name = doc_data.get("nama_barang", "").lower()
                    category = doc_data.get("kategori", "").lower()

                    synonyms = {
                        "laptop": ["laptop", "macbook", "thinkpad"],
                        "komputer": ["laptop", "macbook", "monitor"],
                        "wifi": ["router", "mikrotik", "kabel"],
                        "internet": ["router", "mikrotik", "kabel"],
                        "mebel": ["meja", "kursi", "papan"],
                        "furniture": ["meja", "kursi", "papan"]
                    }
                
                    search_terms = synonyms.get(keyword, [keyword])

                    found = False
                    for term in search_terms:
                        if term in name or term in category:
                            found = True
                            break 

                    if not found:
                        cocok = False

                if cocok:
                    data_list.append({
                        "ID Barang": doc_data.get("id_barang", "-"),
                        "Nama Barang": doc_data.get("nama_barang", "-"),
                        "Kategori": doc_data.get("kategori", "-"),
                        "Jumlah": doc_data.get("jumlah", 0),
                        "Kondisi": doc_data.get("kondisi", "-"),
                        "Lokasi": doc_data.get("lokasi", "-"),
                        "Tgl Pengadaan": doc_data.get("tanggal_pengadaan", "-")
                    })

            suffix = f"_{filter_val}" if filter_val and filter_val != "null" else "_Semua"
            filename_base = f"Laporan_Inventaris{suffix}"

        print(f"📊 JUMLAH DATA DITEMUKAN: {len(data_list)}")
        if not data_list:
            return None

        df = pd.DataFrame(data_list)

        if file_format.lower() == "excel":
            file_path = f"{filename_base}.xlsx"

            writer = pd.ExcelWriter(file_path, engine='openpyxl')
            df.to_excel(writer, index=False, sheet_name='Laporan')

            workbook = writer.book
            worksheet = writer.sheets['Laporan']

            header_fill = PatternFill(start_color="203764", end_color="203764", fill_type="solid") 
            header_font = Font(color="FFFFFF", bold=True)
            border = Border(
                left=Side(style='thin', color='D4D4D4D4'),
                right=Side(style='thin', color='D4D4D4D4'),
                top=Side(style='thin', color='D4D4D4D4'),
                bottom=Side(style='thin', color='D4D4D4D4')
            )

            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = border

            for i, col_name in enumerate(df.columns, start=1):
                col_letter = get_column_letter(i)

                if "Nama" in str(col_name) or "Kategori" in str(col_name):
                    worksheet.column_dimensions[col_letter].width = 25
                else:
                    worksheet.column_dimensions[col_letter].width = 15

            for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=1, max_col=worksheet.max_column):
                for cell in row:
                    cell.border=border
                    cell.alignment = Alignment(horizontal='center', vertical='center')

            writer.close()
            print(f"Success! Excel is saved in: {os.path.abspath(file_path)}")
            return file_path

        elif file_format.lower() == "pdf":
            file_path = f"{filename_base}.pdf"

            html_table = df.to_html(index=False, border=1, justify="center")

            judul_laporan = "Laporan Kehadiran Karyawan" if intent == 'tarik_absen' else "Laporan Inventaris Aset"
            periode = filter_val if filter_val and filter_val != "null" else "Semua Data"

            html_content = f"""
            <html>
            <head>
                <style>
                    @page {{ 
                        size: A4 landscape; 
                        margin: 1cm; 
                    }}
                    body {{ 
                        font-family: Helvetica, Arial, sans-serif; 
                        font-size: 10pt;
                    }}
                    .header-title {{
                        text-align: center;
                        color: #203764;
                        font-size: 24pt;
                        font-weight: bold;
                        margin-bottom: 5px;
                    }}
                    .header-subtitle {{
                        text-align: center;
                        color: #555555;
                        font-size: 12pt;
                        margin-bottom: 20px;
                        border-bottom: 2px solid #203764;
                        padding-bottom: 10px;
                    }}
                    
                    table {{ 
                        width: 100%; 
                        border: 0.5px solid #000000;
                    }}
                    th {{ 
                        background-color: #203764; 
                        color: #ffffff; 
                        padding: 6px; 
                        text-align: center; 
                        font-weight: bold;
                        border: 0.5px solid #000000;
                    }}
                    td {{ 
                        padding: 5px; 
                        border: 0.5px solid #000000;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="header-title">{judul_laporan}</div>
                <div class="header-subtitle">Periode/Filter: {periode}</div>
                
                {html_table}
            </body>
            </html>
            """


            with open(file_path, "w+b") as result_file:
                pisa_status = pisa.CreatePDF(html_content, dest=result_file)

            if pisa_status.err:
                print("Error when converting HTML to PDF")
                return None

            else:
                print(f"Success! PDF is saved in: {os.path.abspath(file_path)}")
                return file_path
            
    except FileNotFoundError:
        print("Error: file {DATABASE_FILE} not found")
    


