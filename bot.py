import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Cargar variables de entorno
load_dotenv("config.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ✅ Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy tu bot de Google Drive, listo para ayudarte.")

# ✅ Comando /ping (prueba de conexión)
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot activo y funcionando correctamente.")

# ✅ Comando /info (solo para ti)
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("📊 Estado: Online\nVersión: v1.0\nServidor: Render")
    else:
        await update.message.reply_text("🚫 No tienes permiso para usar este comando.")

# ✅ Mantener el bot activo (útil para Render)
async def keep_alive():
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "Bot activo 🟢"

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# ✅ Iniciar aplicación
async def main():
    print("Iniciando bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("info", info))

    await app.run_polling()

if __name__ == "__main__":
    # Ejecutar Flask en paralelo al bot (Render necesita un puerto HTTP activo)
    import threading
    threading.Thread(target=keep_alive).start()
    asyncio.run(main())
