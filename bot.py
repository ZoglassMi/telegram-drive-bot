import os
import random
import asyncio
from io import BytesIO
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from keep_alive import keep_alive
import pytz

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
    "🌅 Cada día es una nueva oportunidad para brillar.",
    "💪 No te rindas, lo mejor aún está por venir.",
    "🚀 Cree en ti y haz que las cosas pasen.",
    "🌻 Sonríe, el mundo necesita más luz como la tuya.",
    "🔥 El éxito comienza cuando das el primer paso.",
    "🌙 Incluso la noche más oscura termina con un amanecer.",
    "💫 No hay límites para quien sueña en grande.",
    "☀️ Haz de hoy un día tan increíble que mañana te dé envidia.",
    "🌈 Siempre hay algo bueno en cada día, solo hay que buscarlo.",
    "✨ Eres más fuerte de lo que imaginas y más capaz de lo que crees."
]

# === Estado ===
auto_send_enabled = True
auto_send_mode = "normal"  # "normal" o "diario"
send_interval = 1  # minutos (por defecto)
scheduler = AsyncIOScheduler(timezone=pytz.timezone("America/Lima"))

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

# === Envío de imagen ===
async def send_random_image(app, chat_id):
    file, name = get_random_image_file()
    if file:
        try:
            phrase = random.choice(PHRASES)
            await app.bot.send_photo(
                chat_id=chat_id,
                photo=file,
                caption=phrase,
                parse_mode="Markdown"
            )
            print(f"📤 Imagen enviada: {name} ({datetime.now()})")
        except Exception as e:
            print(f"❌ Error al enviar imagen: {e}")

# === Comandos ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled
    auto_send_enabled = True
    await update.message.reply_text("✅ Autoenvío de imágenes activado.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled
    auto_send_enabled = False
    await update.message.reply_text("🛑 Autoenvío detenido. Usa /start para reanudar.")

async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Buscando una imagen aleatoria...")
    await send_random_image(context.application, update.effective_chat.id)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! El bot está activo 😎")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Comandos disponibles:*\n\n"
        "/start - Activa el autoenvío de imágenes\n"
        "/stop - Detiene el autoenvío\n"
        "/foto - Envía una imagen aleatoria\n"
        "/ping - Comprueba si el bot está activo\n"
        "/settime [5|15|30|60] - Cambia el intervalo (minutos / 1h)\n"
        "/setmode [normal|diario] - Cambia entre modo automático o diario\n"
        "/help - Muestra este mensaje de ayuda"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def settime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global send_interval, scheduler, auto_send_mode

    if auto_send_mode == "diario":
        await update.message.reply_text("⚠️ Estás en modo diario. Usa /setmode normal para cambiar el intervalo.")
        return

    if not context.args:
        await update.message.reply_text("⏱️ Usa: /settime [5|15|30|60]")
        return

    value = context.args[0]
    if value not in ["5", "15", "30", "60"]:
        await update.message.reply_text("⚠️ Valor no válido. Usa: 5, 15, 30 o 60.")
        return

    send_interval = int(value if value != "60" else 60)
    restart_jobs(context.application)
    await update.message.reply_text(f"✅ Intervalo actualizado a cada {value} minutos.")

async def setmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_mode
    if not context.args:
        await update.message.reply_text("📅 Usa: /setmode [normal|diario]")
        return

    mode = context.args[0].lower()
    if mode not in ["normal", "diario"]:
        await update.message.reply_text("⚠️ Modo no válido. Usa: normal o diario.")
        return

    auto_send_mode = mode
    restart_jobs(context.application)

    if mode == "diario":
        await update.message.reply_text("🌞 Modo diario activado. Recibirás una imagen cada día a las 9:00 AM 🇵🇪")
    else:
        await update.message.reply_text(f"🔁 Modo normal activado. Intervalo actual: cada {send_interval} minutos.")

# === Reiniciar tareas del scheduler ===
def restart_jobs(app):
    scheduler.remove_all_jobs()
    if auto_send_mode == "diario":
        # Enviar todos los días a las 9:00 AM hora Perú
        scheduler.add_job(send_random_image, CronTrigger(hour=9, minute=0, timezone=pytz.timezone("America/Lima")), args=[app, OWNER_ID])
    else:
        # Intervalo regular
        scheduler.add_job(send_random_image, "interval", minutes=send_interval, args=[app, OWNER_ID])
    scheduler.start()
    print(f"🔁 Tareas reiniciadas en modo {auto_send_mode}")

# === Ejecución principal ===
async def start_bot():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("foto", foto))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("settime", settime))
    app.add_handler(CommandHandler("setmode", setmode))

    restart_jobs(app)

    await app.initialize()
    await app.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    keep_alive()
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
