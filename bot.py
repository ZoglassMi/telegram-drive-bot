import os
import random
import asyncio
from io import BytesIO
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
    "💫 No hay límites para quien sueña en grande.",
    "🌈 Cada fracaso te acerca más al éxito.",
    "🌻 Haz hoy algo por lo que tu yo del futuro te agradezca.",
    "🌟 A veces solo necesitas respirar y seguir.",
    "💭 Si puedes imaginarlo, puedes lograrlo.",
    "☀️ Empieza donde estás, usa lo que tienes, haz lo que puedas.",
    "🌊 La constancia es más poderosa que la motivación.",
    "🦋 El cambio es el comienzo de algo hermoso.",
    "🍃 La calma también es una forma de fuerza.",
    "🔥 Lo imposible solo tarda un poco más.",
    "🌄 El esfuerzo de hoy será tu orgullo mañana.",
    "💎 Sé la energía que quieres atraer.",
    "🌻 La disciplina supera al talento cuando el talento no se esfuerza.",
    "🌸 Agradece incluso los pequeños avances."
]

# === Estado global ===
auto_send_enabled = False
scheduler = None
send_interval = 1  # intervalo por defecto en minutos

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
        print(f"🖼️ Imagen seleccionada: {file['name']}")
        request = drive_service.files().get_media(fileId=file["id"])
        file_data = BytesIO(request.execute())
        file_data.name = file["name"]
        return file_data, file["name"]
    except Exception as e:
        print(f"⚠️ Error al obtener imagen: {e}")
        return None, None

# === Comandos del bot ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled
    auto_send_enabled = True
    await update.message.reply_text(f"✅ Autoenvío activado. Te enviaré fotos cada {send_interval} minuto(s) 🌅")
    print("▶️ Autoenvío activado por comando /start")

    # Enviar una imagen inicial
    file, _ = get_random_image_file()
    if file:
        phrase = random.choice(PHRASES)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=file, caption=phrase)
        print("📸 Imagen inicial enviada")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled
    auto_send_enabled = False
    await update.message.reply_text("🛑 Autoenvío detenido. Usa /start para reanudar.")
    print("⏸️ Autoenvío detenido por comando /stop")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! Todo funciona correctamente 😎")

async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Buscando una imagen aleatoria en tu Google Drive...")
    file, _ = get_random_image_file()
    if file:
        phrase = random.choice(PHRASES)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=file, caption=phrase)
        print("📤 Imagen enviada manualmente")
    else:
        await update.message.reply_text("⚠️ No se pudo obtener una imagen en este momento.")

async def settime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global send_interval, scheduler

    if not context.args:
        await update.message.reply_text("⏱️ Usa `/settime [5|15|30|1h]` para ajustar el intervalo de envío.", parse_mode="Markdown")
        return

    value = context.args[0].lower()
    new_interval = None

    if value == "5":
        new_interval = 5
    elif value == "15":
        new_interval = 15
    elif value == "30":
        new_interval = 30
    elif value == "1h":
        new_interval = 60

    if new_interval:
        send_interval = new_interval
        # Reiniciar tarea del scheduler
        for job in scheduler.get_jobs():
            job.remove()
        scheduler.add_job(send_random_image, "interval", minutes=send_interval, args=[context.application])
        await update.message.reply_text(f"✅ Intervalo actualizado: cada {value if value != '1h' else '1 hora'} ⏰")
        print(f"🔁 Intervalo de envío cambiado a {send_interval} minutos.")
    else:
        await update.message.reply_text("⚠️ Valor no válido. Usa `/settime [5|15|30|1h]`.", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **Comandos disponibles:**\n\n"
        "/start → Activa el envío automático de imágenes 📸\n"
        "/stop → Detiene el envío automático 🛑\n"
        "/foto → Envía una imagen aleatoria al instante 🌅\n"
        "/settime [5|15|30|1h] → Cambia el intervalo de envío ⏱️\n"
        "/ping → Verifica si el bot está activo ✅\n"
        "/help → Muestra esta lista de comandos ℹ️\n\n"
        "✨ Disfruta de tus fotos y frases inspiradoras ✨"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# === Envío automático ===
async def send_random_image(context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled
    if not auto_send_enabled:
        return

    file, _ = get_random_image_file()
    if file:
        try:
            phrase = random.choice(PHRASES)
            await context.bot.send_photo(chat_id=OWNER_ID, photo=file, caption=phrase)
            print("📤 Imagen automática enviada")
        except Exception as e:
            print(f"❌ Error al enviar imagen automática: {e}")

# === Bucle principal ===
async def start_bot():
    global scheduler
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("foto", foto))
    app.add_handler(CommandHandler("settime", settime))
    app.add_handler(CommandHandler("help", help_command))

    # Planificador de envío automático
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(send_random_image, "interval", minutes=send_interval, args=[app])
    scheduler.start()

    print("🤖 Bot conectado y escuchando comandos...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()  # Mantiene el bot activo

# === Ejecución principal ===
if __name__ == "__main__":
    keep_alive()  # Mantiene Railway activo
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
