import os
import threading
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from keep_alive import keep_alive

# Cargar variables de entorno
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("❌ Falta BOT_TOKEN en las variables de entorno.")

# === COMANDOS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! El bot está activo en Railway 🚀")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! Todo funciona correctamente 😎")

# === FUNCIÓN PRINCIPAL ===
async def start_bot():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    await app.initialize()
    await app.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")

    # Mantiene el bot corriendo
    await app.updater.start_polling()
    await asyncio.Event().wait()  # Espera infinita sin cerrar loop

# === ARRANQUE SEGURO PARA RAILWAY ===
def run_bot():
    asyncio.run(start_bot())

if __name__ == "__main__":
    # Inicia el servidor Flask (para mantener el contenedor vivo)
    keep_alive()

    # Inicia el bot en un hilo separado
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
