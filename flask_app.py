import asyncio
import logging
import sys
import threading
from flask import Flask, request
from aiogram.types import Update
from bot.main import bot, dp, setup_dispatcher
from core.database import init_db

# Logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Setup Dispatcher (Routers/Middleware)
setup_dispatcher()

# Webhook URL (PythonAnywhere domeningiz)
WEBHOOK_HOST = "https://shohruh2006.pythonanywhere.com"
WEBHOOK_PATH = f"/webhook/{bot.token}"
WEBHOOK_URL  = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# ---------------------------------------------------------------------
bg_loop = asyncio.new_event_loop()

def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()

t = threading.Thread(target=start_background_loop, args=(bg_loop,), daemon=True)
t.start()

def run_async(coro):
    future = asyncio.run_coroutine_threadsafe(coro, bg_loop)
    return future.result()

# DB ni sozlash
try:
    run_async(init_db())
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database Init Failed: {e}")

# Webhook o'rnatish
async def setup_webhook():
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook set: {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"Webhook setup failed: {e}")

try:
    run_async(setup_webhook())
except Exception as e:
    logger.error(f"Webhook auto-setup error: {e}")


@app.route('/')
def home():
    return "<h1>Jonli Taxi Bot</h1><p>Bot ishlayapti ✅</p><a href='/setup'>Webhookni sozlash</a>"


@app.route('/setup')
def setup():
    """Brauzer orqali webhookni sozlash"""
    try:
        run_async(setup_webhook())
        return f"<h2>✅ Webhook muvaffaqiyatli o'rnatildi!</h2><p>{WEBHOOK_URL}</p>"
    except Exception as e:
        return f"<h2>❌ Xato:</h2><pre>{e}</pre>", 500


@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook_handler():
    if request.method == 'POST':
        try:
            update = Update.model_validate(request.json)
            run_async(dp.feed_update(bot, update))
            return "ok"
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return "error", 500
    return "forbidden", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
