import os
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from keep_alive import keep_alive

# === Cargar variables de entorno ===
if os.path.exists("config.env"):
    load_dotenv("config.env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("❌ Falta BOT_TOKEN en las variables de entorno.")

# === Comandos ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! El bot está activo en Railway 🚀")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! Todo funciona correctamente 😎")

# === Iniciar bot ===
def run_bot():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    # Este método maneja el ciclo de vida completo del bot
    print("🤖 Bot en modo polling. Esperando comandos...")
    app.run_polling()

# === Main ===
def main():
    # Mantiene vivo el contenedor
    threading.Thread(target=keep_alive, daemon=True).start()
    run_bot()

if __name__ == "__main__":
    main()
