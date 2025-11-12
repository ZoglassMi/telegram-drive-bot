from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
import logging
import os
from dotenv import load_dotenv
import asyncio

# Cargar variables del entorno
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Configuración del log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Comandos del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! El bot está funcionando correctamente.")

async def main():
    # Crear la aplicación
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Agregar comandos
    app.add_handler(CommandHandler("start", start))

    # Iniciar el bot
    print("🤖 Bot en ejecución...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
