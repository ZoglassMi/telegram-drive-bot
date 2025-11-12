import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from keep_alive import keep_alive

# Cargar .env local si existe (solo para desarrollo)
if os.path.exists("config.env"):
    load_dotenv("config.env")
else:
    load_dotenv()  # intenta cargar variables del entorno en Railway

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("❌ Falta BOT_TOKEN en las variables de entorno.")

# === COMANDOS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! El bot está activo en Railway 🚀")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Pong! Todo funciona correctamente 😎")

# === FUNCION PRINCIPAL ASINCRONA ===
async def start_bot():
    print("🚀 Iniciando bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    # Inicializar y arrancar sin usar run_polling (evita cerrar el loop)
    await app.initialize()
    await app.start()
    print("🤖 Bot iniciado correctamente y escuchando comandos...")

    # Si necesitas polling explícito (esto usa internamente a la app)
    # en PTB 20 la forma correcta es usar start() y luego esperar indefinidamente.
    # Mantener vivo:
    await asyncio.Event().wait()

# === ARRANQUE ===
if __name__ == "__main__":
    # 1) Levanta el servidor Flask en hilo daemon (mantiene contenedor “vivo”)
    keep_alive()

    # 2) Ejecuta el bot en el hilo principal con asyncio.run()
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente.")
