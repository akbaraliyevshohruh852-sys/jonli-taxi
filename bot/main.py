import asyncio
import logging
import sys
import os
import threading
from datetime import datetime
from flask import Flask

# --- PYTHON 3.14+ VA PYROGRAM UCHUN MUHIM ---
import nest_asyncio
nest_asyncio.apply()
# --------------------------------------------

# Render Bepul rejasi uchun Web Server (Port binding xatosini oldini oladi)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

def run_flask():
    # Render avtomatik taqdim etadigan portni ishlatadi (odatda 10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Project root-ni sys.path-ga qo'shish
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Windowsda UTF-8 muammosini hal qilish
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from core.config import TOKEN, ADMIN_IDS
from core.database import init_db, db

from bot.handlers import (
    common, registration, driver, passenger, 
    admin, bridge, avto_xabar_add, avto_xabar_manage, chat_member
)
from bot.utils.avto_xabar_scheduler import start_all_ads
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.middlewares.maintenance import MaintenanceMiddleware

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def subscription_scheduler(bot: Bot):
    while True:
        try:
            expired = await db.get_expired_drivers()
            for dr_data in expired:
                await db.update_driver_status(dr_data['telegram_id'], 'expired')
                try:
                    await bot.send_message(
                        dr_data['telegram_id'],
                        "🔴 <b>Obuna muddati tugadi!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "Yangi buyurtmalarni qabul qilish uchun obunani yangilang.",
                        parse_mode="HTML"
                    )
                except Exception: pass
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            await asyncio.sleep(60)

# Global Instances
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def on_startup(bot: Bot):
    await init_db()
    logger.info("Database initialized")
    
    os.makedirs('sessions', exist_ok=True)
    
    # Schedulerlarni ishga tushirish
    asyncio.create_task(subscription_scheduler(bot))
    asyncio.create_task(start_all_ads(bot))

    await bot.set_my_commands([
        BotCommand(command="/start", description="Botni ishga tushirish"),
        BotCommand(command="/help", description="Yordam")
    ])

async def main():
    # Middleware
    dp.message.middleware(MaintenanceMiddleware())
    dp.message.middleware(SubscriptionMiddleware())

    # Routers
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(driver.router)
    dp.include_router(passenger.router)
    dp.include_router(bridge.router)
    dp.include_router(avto_xabar_manage.router)
    dp.include_router(avto_xabar_add.router)
    dp.include_router(chat_member.router)
    dp.include_router(common.router)

    await on_startup(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("🚀 JONLI TAXI BOT ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # 1. Flask serverni alohida oqimda ishga tushiramiz (Render uchun)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Python 3.14+ uchun xavfsiz Event Loop yaratish
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # main() ni task sifatida yurgizamiz
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    finally:
        loop.close()
