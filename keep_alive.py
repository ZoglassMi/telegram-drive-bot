from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot activo y escuchando comandos en Railway."

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def keep_alive():
    thread = Thread(target=run)
    thread.daemon = True
    thread.start()
