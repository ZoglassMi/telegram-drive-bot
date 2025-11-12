import os
import random
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from keep_alive import keep_alive

# --- CONFIGURACIÓN ---
TOKEN = os.getenv("BOT_TOKEN")  # tu token del bot
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))  # tu ID de Telegram

# Lista de imágenes (pueden ser URLs públicas de Drive o Imgur)
IMAGE_URLS = [
    "https://picsum.photos/600/400?random=1",
    "https://picsum.photos/600/400?random=2",
    "https://picsum.photos/600/400?random=3"
]

# Frases inspiradoras
PHRASES = [
    "🌅 Cada día es una nueva oportunidad.",
    "💪 No te rindas, lo mejor está por venir.",
    "🚀 Cree en ti mismo y da el siguiente paso.",
    "🌻 Sonríe, hoy puede ser un gran día.",
    "🔥 El éxito empieza cuando decides intentarlo."
]

# Estado del bot (para pausar o reanudar)
auto_send_enabled = True

# --- LOGGING ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- FUNCIONES DE BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled
    auto_send_enabled = True
    await update.message.reply_text("✅ Bot iniciado. Te enviaré fotos automáticamente cada minuto.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_send_enabled
    auto_send_enabled = False
    await update.message.reply_text("🛑 Autoenvío de fotos detenido. Usa /start para reanudar.")

async def send_random_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando manual para enviar una foto"""
    url = random.choice(IMAGE_URLS)
    phrase = random.choice(PHRASES)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=url, caption=phrase)

async def send_random_image(app):
    """Tarea automática que se ejecuta cada cierto tiempo"""
    global auto_send_enabled
    if not auto_send_enabled:
        return

    try:
        url = random.choice(IMAGE_URLS)
        phrase = random.choice(PHRASES)
        await app.bot.send_photo(chat_id=OWNER_ID, photo=url, caption=phrase)
    except Exception as e:
        logging.error(f"Error enviando imagen automática: {e}")

# --- CONFIGURAR BOT ---
async def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("foto", send_random_photo))

    # Programador de tareas automáticas
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: asyncio.run(send_random_image(app)), "interval", minutes=1)
    scheduler.start()

    logging.info("🤖 Bot iniciado correctamente y escuchando comandos...")
    await app.run_polling()

# --- MAIN ---
if __name__ == "__main__":
    keep_alive()  # Mantiene Flask activo
    asyncio.get_event_loop().run_until_complete(run_bot())
