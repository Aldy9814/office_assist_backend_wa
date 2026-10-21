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
from generator_v2 import generate_report
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from sqlalchemy import create_engine, text

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("API key not found")
client = genai.Client(api_key=api_key)

DB_URL = os.getenv("DATABASE_URL")
db_engine = create_engine(DB_URL)

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

GREEN_API_URL = os.getenv("GREEN_API_URL")
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")

def format_phone_number(phone: str) -> str:
    if not phone.endswith("@c.us"):
        return f"{phone}@c.us"
    return phone

def send_wa_text(to_number: str, text: str):
    chat_id = format_phone_number(to_number)
    url = f"{GREEN_API_URL}/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
    
    payload = {
        "chatId": chat_id,
        "message": text
    }
    response = requests.post(url, json=payload)
    print(f"Green API Text Response: {response.text}")

def send_wa_document(to_number: str, file_path: str, caption: str):
    chat_id = format_phone_number(to_number)
    url = f"{GREEN_API_URL}/waInstance{GREEN_API_ID}/sendFileByUpload/{GREEN_API_TOKEN}"

    payload = {
        "chatId": chat_id,
        "caption": caption
    }

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        upload_res = requests.post(url, data=payload, files=files)
        print(f"Green API Doc Response: {upload_res.text}")
    
def process_wa_message(sender_phone: str, message_text: str):
    prompt_instruction = f"""
        Kamu adalah asisten AI HR bernama OfficeAssist.
        Kamu sedang melayani karyawan dengan nomor WhatsApp: {sender_phone}.

        Tugasmu adalah menganalisis pesan user dan mengekstrak niat (intent) serta detail filter untuk menarik laporan kantor.
        Baca pesan user ini: "{message_text}"

        Keluarkan output HANYA dalam format JSON dengan struktur yang persis seperti ini, tanpa markdown ```json atau teks awalan/akhiran apa pun:
        {{
            "intent": "tarik_inventaris" | "tarik_pengadaan" | "tarik_jadwal" | "lainnya",
            "format": "excel" | "pdf",
            "keyword": "string" | null
        }}

        ATURAN PENTING:
        1. FORMAT LAPORAN: Jika user tidak menyebut format secara eksplisit, selalu asumsikan "excel".
        2. EKSTRAKSI KATA KUNCI (KRITIKAL): 
        - Untuk inventaris: Jika user menyebut merek, tipe spesifik (misal: "Monitor Dell", "PC Intel NUC"), atau nama/divisi pemegang aset, tangkap frasa tersebut utuh sebagai "keyword".
        - Jika tidak ada filter yang diminta, isi null.
        3. INTENT LAINNYA: Jika pesan hanya sapaan atau tidak meminta laporan, isi intent "lainnya".
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
        keyword = extraction_result.get("keyword")
        
        response_status = "success"

        if intent == 'tarik_inventaris':
            send_wa_text(sender_phone, "Tunggu sebentar, sedang menarik data inventaris")
            file_path = generate_report(intent, file_format, keyword)

            if file_path and os.path.exists(file_path):
                messages = f"Siap, laporan inventaris dengan format {file_format.upper()} sudah disiapkan."
                if keyword and keyword != "null":
                    messages = f"Siap, laporan inventaris untuk '{keyword}' dengan format {file_format.upper()} sudah disiapkan."
                send_wa_document(sender_phone, file_path, messages)
            else:
                send_wa_text(sender_phone, "Maaf, data inventaris yang dicari tidak tersedia.")
                response_status = "data_not_found"

        elif intent == 'lainnya':
            guide_message = (
               "Maaf, OfficeAssist belum mengenali perintah tersebut. 🤖\n\n"
                "Saat ini, Anda bisa meminta saya untuk:\n"
                "1. *Tarik Laporan Inventaris*\n"
                "   Contoh: 'Cetak data aset Monitor Dell excel'\n"
                "   Contoh: 'Minta laporan inventaris lengkap pdf'\n\n"
                "Ketik pesan Anda dengan jelas, dan saya akan menyiapkan laporannya!"
            )
            send_wa_text(sender_phone, guide_message)
            response_status = "bot_guide_sent"

        else: 
            send_wa_text(sender_phone, "Maaf, saat ini saya hanya dapat melayani penarikan data inventaris.")
            response_status = "unrecognized_intent"

        with db_engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO audit_logs (whatsapp_number, incoming_message, detected_intent, response_status)
                VALUES (:wa, :msg, :intent, :status)
            """), {
                "wa": sender_phone,
                "msg": message_text,
                "intent": intent,
                "status": response_status
            })

    except Exception as e:
        print(f"Error Gemini / Processing: {e}")
        send_wa_text(sender_phone, "Sistem sedang mengalami gangguan. Coba lagi nanti.")
        
        with db_engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO audit_logs (whatsapp_number, incoming_message, detected_intent, response_status)
                VALUES (:wa, :msg, :intent, :status)
            """), {
                "wa": sender_phone,
                "msg": message_text,
                "intent": "error",
                "status": "system_error"
            })

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == GREEN_API_TOKEN:
            print("Webhook is verified by Meta")
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    return "Office Assist Bot Running!"

@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        print("=== LOG PAYLOAD GREEN API ===")
        print(json.dumps(body, indent=4))
        print("=============================")

        type_webhook = body.get("typeWebhook")

        if type_webhook in ["incomingMessageReveived", "outgoingMessageReceived"]:
            sender_phone = body["senderData"]["sender"]
            message_data = body.get("messageData", {})
            type_message = message_data.get("typeMessage")

            message_text = ""

            if type_message == "textMessage":
                message_text = message_data["textMessageData"]["textMessage"]
            elif type_message == "extendedTextMessage":
                message_text = message_data["extendedTextMessage"]["text"]

            if message_text:
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