import os
import asyncio
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from keep_alive import keep_alive

# Cargar variables de entorno (Railway o local)
if os.path.exists("config.env"):
    load_dotenv("config.env")
else:
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

# === BOT ASINCRÓNICO ===
async def run_bot():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    await app.initialize()
    await app.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")

    # Mantiene el bot activo indefinidamente
    await asyncio.Event().wait()

# === ARRANQUE GENERAL ===
def main():
    # 1️⃣ Iniciar Flask en hilo secundario (para mantener el contenedor activo)
    threading.Thread(target=keep_alive, daemon=True).start()

    # 2️⃣ Ejecutar el bot en el hilo principal con su propio event loop
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
