import os
import random
import asyncio
from io import BytesIO
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from keep_alive import keep_alive

# === Cargar variables de entorno ===
if os.path.exists("config.env"):
    load_dotenv("config.env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

if not all([BOT_TOKEN, OWNER_ID, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN]):
    raise ValueError("❌ Faltan variables de entorno necesarias para el bot o Google Drive")

# === Conexión con Google Drive ===
creds = Credentials(
    None,
    refresh_token=GOOGLE_REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
)
drive_service = build("drive", "v3", credentials=creds)

# === Frases inspiradoras ===
PHRASES = [
    "🌅 Cada día es una nueva oportunidad.",
    "💪 No te rindas, lo mejor está por venir.",
    "🚀 Cree en ti mismo y da el siguiente paso.",
    "🌻 Sonríe, hoy puede ser un gran día.",
    "🔥 El éxito empieza cuando decides intentarlo.",
    "🌙 Incluso las noches más oscuras terminan con el amanecer.",
    "💫 No hay límites para quien sueña en grande."
]

# === Estado del autoenvío ===
auto_send_enabled = True

# === Función para obtener imagen aleatoria de Google Drive ===
def get_random_image_file():
    try:
        results = drive_service.files().list(
            q="mimeType contains 'image/' and trashed = false",
            pageSize=100,
            fields="files(id, name)"
        ).execute()
        files = results.get("files", [])
        if not files:
            print("⚠️ No se encontraron imágenes en Google Drive.")
            return None, None
        file = random.choice(files)
        print(f"🖼️ Imagen seleccionada: {file['name']} ({file['id']})")

        request = drive_service.files().get_media(fileId=file["id"])
        file_data = BytesIO(request.execute())
        file_data.name = file["name"]
        return file_data, file["name"]
    except Exception as e:
        print(f"⚠️ Error al obtener imagen: {e}")
        return None, None

# === Comandos de Telegram ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled
    auto_send_enabled = True
    await update.message.reply_text("✅ Autoenvío de imágenes activado. Te enviaré fotos automáticamente cada minuto.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled
    auto_send_enabled = False
    await update.message.reply_text("🛑 Autoenvío de imágenes detenido. Usa /start para reanudar.")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! Todo funciona correctamente 😎")

async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Buscando una imagen aleatoria en tu Google Drive...")
    file, name = get_random_image_file()
    if file:
        phrase = random.choice(PHRASES)
        caption = f"{phrase}\n\n🖼️ **{name}**\n🕐 {datetime.now().strftime('%H:%M:%S')} UTC"
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=file,
            caption=caption,
            parse_mode="Markdown"
        )
        print(f"📤 Imagen enviada manualmente: {name}")
    else:
        await update.message.reply_text("⚠️ No se pudo obtener una imagen en este momento.")

# === Envío automático cada minuto ===
async def send_random_image(app):
    global auto_send_enabled
    if not auto_send_enabled:
        return

    file, name = get_random_image_file()
    if file:
        try:
            phrase = random.choice(PHRASES)
            caption = f"{phrase}\n\n🌅 Imagen automática desde tu Google Drive\n🖼️ **{name}**\n🕐 {datetime.now().strftime('%H:%M:%S')} UTC"
            await app.bot.send_photo(
                chat_id=OWNER_ID,
                photo=file,
                caption=caption,
                parse_mode="Markdown"
            )
            print(f"📤 Imagen enviada automáticamente: {name} ({datetime.now()})")
        except Exception as e:
            print(f"❌ Error al enviar imagen automática: {e}")

# === Función principal ===
async def start_bot():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("foto", foto))

    # Tarea programada cada 1 minuto
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(send_random_image, "interval", minutes=1, args=[app])
    scheduler.start()

    # Iniciar bot
    await app.initialize()
    await app.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")

    await asyncio.Event().wait()  # Mantiene el bot activo

# === Ejecución principal ===
if __name__ == "__main__":
    keep_alive()  # Mantiene activo Railway

    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
