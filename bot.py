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
INSPIRATIONAL_QUOTES = [
    "✨ Cree en ti mismo, y todo será posible.",
    "🌅 Cada día es una nueva oportunidad para empezar de nuevo.",
    "💫 Los sueños no funcionan a menos que tú trabajes por ellos.",
    "🌻 La vida es mejor cuando sonríes.",
    "🔥 Nunca te rindas, incluso cuando el camino sea difícil.",
    "🌈 Todo lo que necesitas ya está dentro de ti.",
    "☀️ A veces perder es solo el primer paso para ganar algo mejor.",
    "🌸 La felicidad no es un destino, es una forma de viajar.",
    "🦋 Con cada día creces un poco más, no lo olvides.",
    "🌙 No importa cuán oscuro sea el cielo, las estrellas siempre brillan."
]

# === Función para obtener imagen aleatoria ===
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

# === Scheduler ===
scheduler = AsyncIOScheduler(timezone="UTC")
job = None

async def send_random_image(context: ContextTypes.DEFAULT_TYPE, manual=False, chat_id=None):
    file, name = get_random_image_file()
    if file:
        try:
            quote = random.choice(INSPIRATIONAL_QUOTES)
            caption = f"🖼️ *{name}*\n\n_{quote}_\n\n🕐 {datetime.now().strftime('%H:%M:%S')} UTC"
            target_chat = chat_id if chat_id else OWNER_ID
            await context.bot.send_photo(
                chat_id=target_chat,
                photo=file,
                caption=caption,
                parse_mode="Markdown"
            )
            modo = "manual" if manual else "automático"
            print(f"📤 Imagen enviada ({modo}): {name}")
        except Exception as e:
            print(f"❌ Error al enviar imagen: {e}")

# === Comandos ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job
    chat_id = update.effective_chat.id
    if job and job.next_run_time:
        await update.message.reply_text("✅ El bot ya está enviando imágenes automáticamente.")
    else:
        job = scheduler.add_job(send_random_image, "interval", minutes=1, args=[context])
        await update.message.reply_text("🚀 Envío automático activado cada minuto.")
        print("🟢 Envío automático iniciado.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job
    if job:
        job.remove()
        job = None
        await update.message.reply_text("🛑 Envío automático detenido.")
        print("🔴 Envío automático detenido.")
    else:
        await update.message.reply_text("⚠️ No hay envío automático activo.")

async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("📸 Buscando una imagen inspiradora para ti...")
    await send_random_image(context, manual=True, chat_id=chat_id)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! Todo funciona correctamente 😎")

# === Inicializar bot ===
async def start_bot():
    print("🚀 Iniciando bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("foto", foto))
    app.add_handler(CommandHandler("ping", ping))

    scheduler.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")

    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()  # Mantiene el bot vivo

# === MAIN seguro para Railway ===
if __name__ == "__main__":
    keep_alive()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            print("⚠️ Loop ya en ejecución, creando nueva tarea asincrónica...")
            loop.create_task(start_bot())
        else:
            loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
