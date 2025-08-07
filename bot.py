import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import re

# Konfigurasi log
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = "8474313899:AAE7X4gvp-kzsnXPOGmL08rBryleJkeFku4"
GOOGLE_SHEETS_JSON_PATH = "noizbot-451214-639184b6b3f7.json"
SHEET_NAME = "Arsip UMKM Desa Langkai" # Nama spreadsheet
WORKSHEET_NAME = "Sheet1" # Nama worksheet 

# Fungsi untuk mengotentikasi dan mendapatkan koneksi Google Sheets
def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_JSON_PATH, scope)
    client = gspread.authorize(creds)
    return client

# Fungsi untuk menyimpan data ke Google Sheets
def save_to_sheets(data):
    try:
        client = get_gspread_client()
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        # Tambahkan header jika sheet kosong
        if not sheet.get_all_values():
            headers = ["Timestamp", "Nama UMKM", "Jenis Usaha", "Nama Pemilik", "Alamat Lengkap", "Nomor Telepon", "Deskripsi Singkat"]
            sheet.append_row(headers)
        
        sheet.append_row(data)
        logger.info(f"Data saved to Google Sheets: {data}")
    except Exception as e:
        logger.error(f"Error saving to Google Sheets: {e}")
        return False
    return True

# Handler untuk perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Halo! Silakan kirim data UMKM Anda dalam satu pesan dengan format berikut:\n\n"
        "Nama UMKM: (isi)\n"
        "Jenis Usaha: (isi)\n"
        "Nama Pemilik: (isi)\n"
        "Alamat Lengkap: (isi)\n"
        "Nomor Telepon: (isi)\n"
        "Deskripsi Singkat: (isi)\n\n"
        "Pastikan setiap baris diawali dengan nama kolom yang benar."
    )

# Handler untuk menerima dan mem-parsing pesan teks
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    
    # Mem-parsing teks berdasarkan format yang diberikan
    data = {}
    lines = text.strip().split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            data[key] = value

    # Validasi data yang diparsing
    required_keys = ["Nama UMKM", "Jenis Usaha", "Nama Pemilik", "Alamat Lengkap", "Nomor Telepon", "Deskripsi Singkat"]
    if all(key in data for key in required_keys):
        # Kumpulkan semua data dan timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data_to_save = [
            timestamp,
            data.get("Nama UMKM"),
            data.get("Jenis Usaha"),
            data.get("Nama Pemilik"),
            data.get("Alamat Lengkap"),
            data.get("Nomor Telepon"),
            data.get("Deskripsi Singkat")
        ]

        if save_to_sheets(data_to_save):
            await update.message.reply_text("🎉 Data UMKM berhasil disimpan ke Google Sheets! Terima kasih.")
        else:
            await update.message.reply_text("Maaf, terjadi kesalahan saat menyimpan data. Silakan coba lagi.")
    else:
        await update.message.reply_text(
            "Format data yang Anda kirimkan tidak lengkap atau salah. "
            "Mohon gunakan format berikut:\n\n"
            "Nama UMKM: (isi)\n"
            "Jenis Usaha: (isi)\n"
            "Nama Pemilik: (isi)\n"
            "Alamat Lengkap: (isi)\n"
            "Nomor Telepon: (isi)\n"
            "Deskripsi Singkat: (isi)"
        )

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Handler untuk perintah /start
    application.add_handler(CommandHandler("start", start))
    
    # Handler untuk semua pesan teks non-perintah
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()