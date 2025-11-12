import os
import asyncio
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from keep_alive import keep_alive

# Cargar .env local o variables del entorno en Railway
if os.path.exists("config.env"):
    load_dotenv("config.env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Falta BOT_TOKEN en las variables de entorno.")

# === Configurar credenciales de Google Drive ===
creds = Credentials.from_authorized_user_info({
    "client_id": GOOGLE_CLIENT_ID,
    "client_secret": GOOGLE_CLIENT_SECRET,
    "refresh_token": GOOGLE_REFRESH_TOKEN,
    "token_uri": "https://oauth2.googleapis.com/token"
})

drive_service = build("drive", "v3", credentials=creds)

# === Obtener imagen aleatoria del Drive ===
def get_random_image_url():
    try:
        results = drive_service.files().list(
            q="mimeType contains 'image/' and trashed = false",
            pageSize=100,
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])
        if not files:
            return None

        file = random.choice(files)
        return f"https://drive.google.com/uc?id={file['id']}"
    except Exception as e:
        print(f"⚠️ Error al obtener imagen: {e}")
        return None

# === Comando /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Bot activo! Usa /foto para recibir una imagen aleatoria.")

# === Comando /foto ===
async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = get_random_image_url()
    if url:
        await update.message.reply_photo(photo=url)
    else:
        await update.message.reply_text("⚠️ No encontré imágenes en tu Google Drive.")

# === Enviar imagen automática cada minuto ===
async def send_random_image(context: ContextTypes.DEFAULT_TYPE):
    url = get_random_image_url()
    if url:
        await context.bot.send_photo(chat_id=OWNER_ID, photo=url)
        print("📤 Imagen enviada automáticamente al propietario.")

# === Iniciar el bot ===
async def start_bot():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("foto", foto))

    # Programar envío automático
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_random_image, "interval", minutes=1, args=[app])
    scheduler.start()

    await app.initialize()
    await app.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")

    await asyncio.Event().wait()

# === Ejecutar ===
if __name__ == "__main__":
    keep_alive()
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
