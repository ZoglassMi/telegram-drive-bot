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
    "🌅 Cada día es una nueva oportunidad.",
    "💪 No te rindas, lo mejor está por venir.",
    "🚀 Cree en ti mismo y da el siguiente paso.",
    "🌻 Sonríe, hoy puede ser un gran día.",
    "🔥 El éxito empieza cuando decides intentarlo.",
    "🌙 Incluso las noches más oscuras terminan con el amanecer.",
    "💫 No hay límites para quien sueña en grande.",
    "🌈 Tu actitud determina tu dirección.",
    "🌺 Haz algo hoy por lo que tu futuro te agradezca.",
    "🌞 Agradece lo que tienes, trabaja por lo que sueñas.",
    "🌟 Cada error te acerca más a tu meta.",
    "🦋 Cambia tus pensamientos y cambiarás tu mundo."
]

# === Zona horaria de Perú ===
PERU_TZ = pytz.timezone("America/Lima")

# === Variables globales ===
auto_send_enabled = True
daily_mode = False
daily_hour = 8
daily_minute = 0
current_interval = 1  # minutos

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

# === Comandos de Telegram ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled, daily_mode
    auto_send_enabled = True
    daily_mode = False
    await update.message.reply_text("✅ Autoenvío de imágenes activado. Enviaré fotos automáticamente cada cierto tiempo. Usa /settime para cambiar el intervalo.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled, daily_mode
    auto_send_enabled = False
    daily_mode = False
    await update.message.reply_text("🛑 Autoenvío de imágenes detenido. Usa /start para reanudar o /daily_on para modo diario.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📘 **Comandos disponibles:**\n\n"
        "➡️ /start - Activa el envío automático.\n"
        "➡️ /stop - Detiene el envío automático.\n"
        "➡️ /foto - Envía una imagen aleatoria.\n"
        "➡️ /settime [5|15|30|60] - Cambia el intervalo (en minutos u horas).\n"
        "➡️ /daily_on - Activa modo diario (una imagen al día a las 8:00 a.m. 🇵🇪).\n"
        "➡️ /daily_off - Desactiva el modo diario.\n"
        "➡️ /setdailytime HH:MM - Cambia la hora del envío diario.\n"
        "➡️ /ping - Verifica que el bot esté activo.\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! Todo funciona correctamente 😎")

async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Buscando una imagen aleatoria en tu Google Drive...")
    file, _ = get_random_image_file()
    if file:
        phrase = random.choice(PHRASES)
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=file,
            caption=phrase,
            parse_mode="Markdown"
        )
        print("📤 Imagen enviada manualmente con /foto.")
    else:
        await update.message.reply_text("⚠️ No se pudo obtener una imagen en este momento.")

async def settime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_interval, daily_mode
    if daily_mode:
        await update.message.reply_text("⚠️ Estás en modo diario. Usa /daily_off antes de cambiar el intervalo.")
        return

    try:
        value = int(context.args[0])
        if value not in [5, 15, 30, 60]:
            raise ValueError
        current_interval = value
        await update.message.reply_text(f"⏱️ Intervalo cambiado a {value} minutos.")
    except:
        await update.message.reply_text("⚠️ Usa el comando así: /settime 15 (valores: 5, 15, 30, 60)")

async def daily_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global daily_mode, auto_send_enabled
    daily_mode = True
    auto_send_enabled = False
    await update.message.reply_text(f"📅 Modo diario activado. Enviaré una imagen todos los días a las {daily_hour:02d}:{daily_minute:02d} 🇵🇪.")

async def daily_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global daily_mode, auto_send_enabled
    daily_mode = False
    auto_send_enabled = True
    await update.message.reply_text("📆 Modo diario desactivado. Volviendo al modo automático.")

async def setdailytime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global daily_hour, daily_minute
    try:
        time_str = context.args[0]
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError
        daily_hour = hour
        daily_minute = minute
        await update.message.reply_text(f"🕗 Hora diaria actualizada a {daily_hour:02d}:{daily_minute:02d} 🇵🇪.")
    except:
        await update.message.reply_text("⚠️ Usa el formato correcto: /setdailytime 08:00")

# === Envío automático ===
async def send_random_image(app):
    global auto_send_enabled
    if not auto_send_enabled:
        return

    file, _ = get_random_image_file()
    if file:
        phrase = random.choice(PHRASES)
        await app.bot.send_photo(chat_id=OWNER_ID, photo=file, caption=phrase, parse_mode="Markdown")
        print(f"📤 Imagen enviada automáticamente ({datetime.now(PERU_TZ)})")

# === Envío diario ===
async def send_daily_image(app):
    global daily_mode
    if not daily_mode:
        return

    file, _ = get_random_image_file()
    if file:
        phrase = random.choice(PHRASES)
        await app.bot.send_photo(chat_id=OWNER_ID, photo=file, caption=phrase, parse_mode="Markdown")
        print(f"📅 Imagen diaria enviada a las {datetime.now(PERU_TZ)}")

# === Función principal ===
async def start_bot():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("foto", foto))
    app.add_handler(CommandHandler("settime", settime))
    app.add_handler(CommandHandler("daily_on", daily_on))
    app.add_handler(CommandHandler("daily_off", daily_off))
    app.add_handler(CommandHandler("setdailytime", setdailytime))
    app.add_handler(CommandHandler("help", help_command))

    # Scheduler
    scheduler = AsyncIOScheduler(timezone=PERU_TZ)
    scheduler.add_job(send_random_image, "interval", minutes=current_interval, args=[app])
    scheduler.add_job(send_daily_image, "cron", hour=daily_hour, minute=daily_minute, args=[app])
    scheduler.start()

    await app.initialize()
    await app.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")

    await asyncio.Event().wait()

# === Ejecución principal ===
if __name__ == "__main__":
    keep_alive()
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
