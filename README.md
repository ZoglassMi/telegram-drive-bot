# 🤖 Telegram Drive Bot

Bot de Telegram en Python que responde comandos y está preparado para integrarse con Google Drive y otras APIs.

## Tecnologías
- Python 3.11
- python-telegram-bot 20.6
- Flask
- APScheduler
- Google API Client

## Variables de entorno necesarias en Railway
| Key                   | Value                          |
|-----------------------|--------------------------------|
| BOT_TOKEN             | tu_token_de_telegram           |
| OWNER_ID              | tu_id_de_usuario               |
| GOOGLE_CLIENT_ID      | tu_client_id                   |
| GOOGLE_CLIENT_SECRET  | tu_secret                      |
| GOOGLE_REFRESH_TOKEN  | tu_refresh_token               |

## Deploy en Railway
1. Crear proyecto vacío en Railway.
2. Conectar tu repo de GitHub.
3. Configurar las variables de entorno.
4. Deploy y revisar logs para confirmar que el bot inicia.
