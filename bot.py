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

# === Frases inspiradoras ===
PHRASES = [
    "🌟 Cada día es una nueva oportunidad para brillar.",
    "💪 Cree en ti, incluso cuando nadie más lo haga.",
    "🌱 Las pequeñas acciones diarias crean grandes resultados.",
    "🔥 Tu esfuerzo de hoy será tu orgullo de mañana.",
    "🚀 No busques el momento perfecto, haz que el momento sea perfecto.",
    "🌈 La vida es como una cámara: enfócate en lo positivo.",
    "💫 A veces perderse es la mejor forma de encontrarse."
]

# === Configuración Google Drive ===
creds = Credentials(
    None,
    refresh_token=GOOGLE_REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
)
drive_service = build("drive", "v3", credentials=creds)

# === Cache de archivos (para evitar pedir Drive cada vez) ===
IMAGE_CACHE = []
CACHE_TTL_MINUTES = 10

def refresh_file_cache():
    """Actualiza la lista de imágenes disponibles en Drive."""
    global IMAGE_CACHE
    try:
        results = drive_service.files().list(
            q="mimeType contains 'image/' and trashed = false",
            pageSize=200,
            fields="files(id, name)"
        ).execute()
        IMAGE_CACHE = results.get("files", [])
        print(f"🗂️ Caché actualizada con {len(IMAGE_CACHE)} imágenes.")
    except Exception as e:
        print(f"⚠️ Error al actualizar caché: {e}")

def get_random_image_file_from_cache():
    """Obtiene una imagen aleatoria de la caché o de Drive si está vacía."""
    global IMAGE_CACHE
    if not IMAGE_CACHE:
        refresh_file_cache()
    if not IMAGE_CACHE:
        return None, None

    file = random.choice(IMAGE_CACHE)
    try:
        request = drive_service.files().get_media(fileId=file["id"])
        file_data = BytesIO(request.execute())
        file_data.name = file["name"]
        return file_data, file["name"]
    except Exception as e:
        print(f"⚠️ Error al descargar imagen: {e}")
        return None, None

# === Función general de envío de imagen ===
async def send_random_image(bot_or_context, manual=False, chat_id=None):
    """Envía una imagen aleatoria desde Drive, con frase inspiradora."""
    if hasattr(bot_or_context, "bot"):
        bot = bot_or_context.bot
    else:
        bot = bot_or_context

    file, name = get_random_image_file_from_cache()
    if not file:
        print("⚠️ No se encontró imagen para enviar.")
        return

    try:
        phrase = random.choice(PHRASES)
        caption = f"{phrase}\n\n🖼️ *{name}*\n🕐 {datetime.utcnow().strftime('%H:%M:%S')} UTC"
        target = chat_id if chat_id else OWNER_ID
        await bot.send_photo(chat_id=target, photo=file, caption=caption, parse_mode="Markdown")

        modo = "manual" if manual else "automático"
        print(f"📤 Imagen enviada ({modo}): {name}")
    except Exception as e:
        print(f"❌ Error al enviar imagen: {e}")

# === Inicializar scheduler global ===
scheduler = AsyncIOScheduler(timezone="UTC")
job = None

# === Comandos del bot ===
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job
    if job:
        await update.message.reply_text("✅ El envío automático ya está activo.")
        return

    bot = context.bot
    job = scheduler.add_job(
        lambda: asyncio.create_task(send_random_image(bot)),
        "interval",
        minutes=1
    )

    await update.message.reply_text("🚀 Envío automático ACTIVADO (cada 1 minuto).")
    print("🟢 Envío automático iniciado.")

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job
    if job:
        job.remove()
        job = None
        await update.message.reply_text("🛑 Envío automático DETENIDO.")
        print("🔴 Envío automático detenido.")
    else:
        await update.message.reply_text("⚠️ No hay tareas automáticas en ejecución.")

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! El bot está funcionando correctamente 😎")

async def foto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Buscando una imagen aleatoria...")
    await send_random_image(context, manual=True, chat_id=update.effective_chat.id)

# === Función principal ===
async def start_bot():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("foto", foto_cmd))

    scheduler.start()
    scheduler.add_job(refresh_file_cache, "interval", minutes=CACHE_TTL_MINUTES)
    refresh_file_cache()  # precarga inicial

    await app.initialize()
    await app.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")

    await asyncio.Event().wait()  # Mantiene el bot activo

# === Ejecución principal ===
if __name__ == "__main__":
    keep_alive()
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
