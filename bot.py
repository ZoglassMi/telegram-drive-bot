import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from keep_alive import keep_alive

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# --- Verificación básica ---
if not BOT_TOKEN:
    raise ValueError("❌ Falta la variable BOT_TOKEN en Railway")

# --- Comandos del bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Bot en Railway activo y funcionando 🚀")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! El bot está vivo 😎")

# --- Arranque principal ---
async def main():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    # Ejecutar el bot (polling)
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

# --- Mantener vivo el contenedor ---
keep_alive()

# --- Iniciar bot ---
if __name__ == "__main__":
    try:
        # Crear una nueva tarea sin cerrar el event loop
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
