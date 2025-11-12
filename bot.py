import os
import random
import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# =========================
# CONFIGURACIÓN INICIAL
# =========================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

# =========================
# COMANDO /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy tu bot personal. Enviaré mensajes cada 15 minutos.\n"
        "Usa /photo para recibir una foto aleatoria 📸"
    )

# =========================
# COMANDO /photo
# =========================
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fotos = [
        "https://picsum.photos/600/400?random=1",
        "https://picsum.photos/600/400?random=2",
        "https://picsum.photos/600/400?random=3",
        "https://picsum.photos/600/400?random=4",
        "https://picsum.photos/600/400?random=5"
    ]
    url = random.choice(fotos)
    await update.message.reply_photo(url, caption="📸 Foto aleatoria para ti!")

# =========================
# MENSAJE AUTOMÁTICO (cada 15 min)
# =========================
async def enviar_mensaje_programado():
    try:
        await bot.send_message(
            chat_id=OWNER_ID,
            text=f"⏰ Recordatorio automático — {datetime.now().strftime('%H:%M:%S')}\n¡Sigue creando cosas geniales!"
        )
        logger.info("Mensaje automático enviado correctamente.")
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")

# =========================
# FUNCIÓN PRINCIPAL
# =========================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("photo", photo))

    # Tarea automática cada 15 minutos
    scheduler.add_job(enviar_mensaje_programado, "interval", minutes=15)
    scheduler.start()

    logger.info("🤖 Bot iniciado y ejecutándose...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
