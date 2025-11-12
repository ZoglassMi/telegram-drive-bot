import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Cargar variables de entorno
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# --- Comandos del bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot de Telegram funcionando correctamente en Render 🚀")

# --- Ejecución principal ---
async def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN no está configurado en las variables de entorno")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("🤖 Bot iniciado. Esperando mensajes...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
