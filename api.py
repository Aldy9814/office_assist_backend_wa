from fastapi import FastAPI, HTTPException, Header, Request, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import json
import requests
from dotenv import load_dotenv
from generator import generate_report
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

load_dotenv()

my_api_key = os.getenv("GEMINI_API_KEY")
if not my_api_key:
    raise ValueError("API key not found")
client = genai.Client(api_key=my_api_key)

cred = credentials.Certificate("firebase-credentials.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

app = FastAPI(title="Office Assist WhatsApp API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WA_VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN")
WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID") 
WA_ACCESS_TOKEN = os.getenv("WA_ACCESS_TOKEN")

def send_wa_text(to_number: str, text: str):
    url = f"https://graph.facebook.com/v17.0/{WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization" : f"Bearer {WA_ACCESS_TOKEN}",
        "Content-Type" : "application/json"
    }
    payload = {
        "messaging_product" : "whatsapp",
        "to" : to_number,
        "type" : "text",
        "text" : {"body" : text}
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"Meta Send Text Response: {response.text}")

def send_wa_document(to_number: str, file_path: str, caption: str):

    upload_url = f"https://graph.facebook.com/v17.0/{WA_PHONE_NUMBER_ID}/media"
    headers = {"Authorization" : f"Bearer {WA_ACCESS_TOKEN}"}

    mime_type = "application/pdf" if file_path.endswith('.pdf') else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, mime_type)}
        data = {"messaging_product": "whatsapp"}

        upload_res = requests.post(upload_url, headers=headers, data=data, files=files)
        print(f"Meta Upload Response: {upload_res.text}")

    upload_data = upload_res.json()
    media_id = upload_data.get("id")

    if not media_id:
        send_wa_text(to_number, "Maaf, terjadi kesalahan saat mengunggah dokumen ke WhatsApp.")
        return

    send_url = f"https://graph.facebook.com/v17.0/{WA_PHONE_NUMBER_ID}/messages"
    headers_send = {
        "Authorization": f"Bearer {WA_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "document",
        "document": {
            "id": media_id,
            "caption": caption,
            "filename": os.path.basename(file_path)
        }
    }
    response = requests.post(send_url, headers=headers_send, json=payload)
    print(f"Meta Send Doc Response: {response.text}")

def process_wa_message(sender_phone: str, message_text: str):
    time_now = datetime.now().strftime("%d %B %Y")

    prompt_instruction = f"""
    Kamu adalah asisten AI HR bernama OfficeAssist.
    Kamu sedang melayani karyawan dengan nomor WhatsApp: {sender_phone}.
    
    Tugasmu adalah menganalisis pesan user dan mengekstrak niatnya (intent) untuk menarik laporan kantor.
    Baca pesan user ini: "{message_text}"
    
    Tugasmu adalah mengeluarkan output HANYA dalam format JSON dengan struktur ini, tanpa teks tambahan apa pun:
    {{
        "intent": "tarik_absen" atau "tarik_inventaris" atau "tarik_pengadaan" atau "tarik_jadwal" atau "lainnya",
        "bulan": "YYYY-MM" (contoh: untuk september 2026 menjadi "2026-09", isi null jika tidak relevan),
        "format": "excel" atau "pdf",
        "kata_kunci": "kata kunci spesifik jika ada (misal: 'laptop' untuk inventaris), isi null jika tidak ada"
    }}
    
    Catatan:
    - Jika user tidak menyebut format, asumsikan "excel".
    - Jika pesan user hanya sapaan atau tidak meminta laporan spesifik, isi "intent" dengan "lainnya".
    - WAKTU SAAT INI ADALAH: {time_now}. Gunakan informasi ini jika user meminta data "bulan ini", "bulan lalu", atau "kemarin".
    - Sistem kami hanya bisa mencetak 1 laporan untuk 1 bulan atau 1 kategori spesifik.
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt_instruction
        )

        raw_json = response.text.strip().replace("```json", "").replace("```", "")
        extraction_result = json.loads(raw_json)
        print(f"Gemini extraction result: {extraction_result}")

        intent = extraction_result.get("intent")
        file_format = extraction_result.get("format", "excel")
        bulan = extraction_result.get("bulan")
        keyword = extraction_result.get("kata_kunci")

        if intent == 'tarik_absen':
            if not bulan or bulan == "null" or bulan == "":
                send_wa_text(sender_phone, "Data bulan apa yang diinginkan? Tolong sebutkan bulannya ya")
                return

            send_wa_text(sender_phone, f"Tungu sebentar, menyiapkan laporan absen untuk bulan {bulan}...")
            file_path = generate_report(intent, file_format, bulan)

            if file_path and os.path.exists(file_path):
                caption = f"Siap, laporan untuk bulan {bulan} dengan format {file_format.upper()} sudah saya siapkan"
                send_wa_document(sender_phone, file_path, caption)
            else:
                send_wa_text(sender_phone, "Maaf, sepertinya belum ada data yang masuk pada bulan tersebut")

        elif intent == 'tarik_inventaris':
            send_wa_text(sender_phone, "Tunggu sebentar, sedang menarik data inventaris")
            file_path = generate_report(intent, file_format, keyword)

            if file_path and os.path.exists(file_path):
                messages = f"Siap, laporan inventaris dengan format {file_format.upper()} sudah disiapkan"
                if keyword and keyword != "null":
                    messages = f"siap, laporan inventaris untuk '{keyword}' dengan format {file_format.upper()} sudah disiapkan"
                send_wa_document(sender_phone, file_path, messages)
            else:
                send_wa_text(sender_phone, "Maaf, data inventaris yang dicari tidak tersedia")

        else: 
            send_wa_text(sender_phone, "Maaf, saat ini saya hanya dapat melayani penarikan absen dan data inventaris")

    except Exception as e:
        print(f"Error Gemini: {e}")
        send_wa_text(sender_phone, "Sistem sedang mengalami gangguan. Coba lagi nanti")


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WA_VERIFY_TOKEN:
            print("Webhook is verified by Meta")
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    return "Office Assist Bot Running!"

@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()

        print("LOG WEBHOOK META:", json.dumps(body, indent=2))

        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        msg = value["messages"][0]
                        sender_phone = msg["from"]

                        if msg["type"] == "text":
                            message_text = msg["text"]["body"]
                            background_tasks.add_task(process_wa_message, sender_phone, message_text)
        return {"status": "ok"}
    except Exception as e:
        print(f"Error webhook: {e}")
        return {"status": "error"}

@app.get("/download/{filename}")
async def download_file(filename: str):
    save_filename = os.path.basename(filename)
    if os.path.exists(save_filename):
        return FileResponse(path=save_filename, filename=save_filename)
    raise HTTPException(status_code=404, detail="File not found")


