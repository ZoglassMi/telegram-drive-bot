import os
import random
import asyncio
from io import BytesIO
from datetime import datetime, timedelta
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

# === Scheduler y estado global ===
scheduler = AsyncIOScheduler(timezone="UTC")
job = None  # referencia al job automático
file_cache = []           # lista de dicts {id, name}
cache_last_refreshed = None
CACHE_TTL_MINUTES = 10    # cada cuánto refrescar la lista de archivos

# === UTIL: refrescar cache de archivos (solo metadata, no descarga) ===
def refresh_file_cache():
    global file_cache, cache_last_refreshed
    try:
        print("🔄 Refrescando cache de archivos de Drive...")
        results = drive_service.files().list(
            q="mimeType contains 'image/' and trashed = false",
            pageSize=1000,  # obtener hasta 1000 ids (ajusta si nece.)
            fields="files(id, name)"
        ).execute()
        files = results.get("files", [])
        file_cache = [{"id": f["id"], "name": f["name"]} for f in files]
        cache_last_refreshed = datetime.utcnow()
        print(f"✅ Cache actualizada: {len(file_cache)} imágenes encontradas.")
    except Exception as e:
        print(f"⚠️ Error al refrescar cache de Drive: {e}")

# === Obtener archivo aleatorio usando cache (descarga el binario) ===
def get_random_image_file_from_cache():
    # si cache vacía o vieja, refrescar
    global cache_last_refreshed
    if not file_cache or (cache_last_refreshed and datetime.utcnow() - cache_last_refreshed > timedelta(minutes=CACHE_TTL_MINUTES)):
        refresh_file_cache()

    if not file_cache:
        print("⚠️ Cache vacía: no hay imágenes para elegir.")
        return None, None

    file_meta = random.choice(file_cache)
    try:
        request = drive_service.files().get_media(fileId=file_meta["id"])
        data = BytesIO(request.execute())
        data.name = file_meta["name"]
        return data, file_meta["name"]
    except Exception as e:
        print(f"⚠️ Error descargando archivo {file_meta['id']}: {e}")
        # si falla, eliminamos esa entrada de cache para evitar repetir errores
        try:
            file_cache.remove(file_meta)
        except Exception:
            pass
        return None, None

# === Lógica de envío ===
async def send_random_image(context_or_app, manual=False, chat_id=None):
    # context_or_app: si es Context (jobs de APScheduler pasan Context), si es app (cuando se lanza manual con app arg)
    # manejamos ambos casos comprobando atributos
    if hasattr(context_or_app, "bot"):
        bot = context_or_app.bot
    else:
        bot = context_or_app.bot  # si le pasamos la app, también tiene .bot

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

# === Comandos ===
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job
    if job:
        await update.message.reply_text("✅ El envío automático ya está activo.")
        return

    # Añadimos job que ejecuta send_random_image, pasándole 'context' cada vez
    job = scheduler.add_job(lambda: asyncio.create_task(send_random_image(context)), "interval", minutes=1)
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
        await update.message.reply_text("⚠️ No había envío automático activo.")

async def foto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Buscando una imagen inspiradora...")
    # pasar el context para que send_random_image use context.bot
    await send_random_image(context, manual=True, chat_id=update.effective_chat.id)

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! Todo funciona correctamente 😎")

# === Función principal ===
async def start_bot():
    print("🚀 Iniciando bot...")

    # refrescar cache al arrancar
    refresh_file_cache()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # registrar comandos
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("foto", foto_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))

    # iniciar scheduler (usa mismo loop asyncio)
    scheduler.start()

    # también activar job de refresco de cache cada X minutos
    scheduler.add_job(refresh_file_cache, "interval", minutes=CACHE_TTL_MINUTES)

    # iniciar bot (initialize + start)
    await app.initialize()
    await app.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")

    # iniciar polling (no cerrar loop al terminar)
    await app.updater.start_polling()
    await asyncio.Event().wait()  # bloqueo infinito para mantener el servicio

# === ENTRYPOINT ===
if __name__ == "__main__":
    keep_alive()  # levantar servidor flask en hilo daemon

    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
