import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from keep_alive import keep_alive
import asyncio

# === CARGA DE VARIABLES ===
if os.path.exists("config.env"):
    from dotenv import load_dotenv
    load_dotenv("config.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

# === VALIDACIONES ===
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN no encontrado.")
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REFRESH_TOKEN:
    raise ValueError("❌ Variables de Google no configuradas correctamente.")

# === COMANDOS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy tu bot de Google Drive conectado y activo 🚀")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Estoy vivo y funcionando correctamente en Railway.")

# === CREAR APLICACIÓN ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ping", ping))

# === MANTENER BOT ACTIVO ===
keep_alive()

# === EJECUTAR POLLING ===
if __name__ == "__main__":
    t
