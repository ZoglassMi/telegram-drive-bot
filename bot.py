import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from keep_alive import keep_alive
import datetime

# 🔹 Token de tu bot desde BotFather
BOT_TOKEN = os.getenv("8541894748:AAEcqOFbkqP_bFEkMpJYmagXG42Tvfo6iZs")

# 🔹 ID personal (usa /start y mira el chat.id en consola para enviarte mensajes a ti)
OWNER_ID = int(os.getenv("5722722923", "0"))

# --- FUNCIONES PRINCIPALES ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Hola {user.first_name}! 🤖\nEl bot de Google Drive está activo.")
    print(f"[+] {user.first_name} inició el bot.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🧭 *Comandos disponibles:*\n\n"
        "/start - Iniciar bot\n"
        "/help - Mostrar este menú\n"
        "/time - Ver hora actual\n"
        "/ping - Prueba de conexión"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    await update.message.reply_text(f"🕒 Hora actual: {now}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 ¡Pong! El bot está activo.")

# --- MENSAJE AUTOMÁTICO CADA 15 MIN ---
async def auto_message(application):
    if OWNER_ID != 0:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        await application.bot.send_message(
            chat_id=OWNER_ID,
            text=f"⏰ Recordatorio automático: el bot sigue activo ({now})"
        )
        print("[+] Mensaje automático enviado.")
    else:
        print("[!] OWNER_ID no configurado.")

# --- MAIN ---
def main():
    print("Iniciando bot...")
    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("time", time_command))
    app.add_handler(CommandHandler("ping", ping))

    # 🔁 Tarea automática cada 15 minutos
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: app.create_task(auto_message(app)), 'interval', minutes=15)
    scheduler.start()

    app.run_polling()

if __name__ == '__main__':
    main()
