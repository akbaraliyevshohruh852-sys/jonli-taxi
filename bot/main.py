import asyncio
import logging
import sys
import os
import threading
import warnings
from datetime import datetime
from flask import Flask

# --- KRITIK TUZATISH (Event Loop va Pydantic uchun) ---
import nest_asyncio
nest_asyncio.apply()
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
# -----------------------------------------------------

# Render uchun Web Server (Port binding)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running perfectly!", 200

def run_flask():
    # Render PORT muhit o'zgaruvchisini avtomatik beradi
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

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

from core.config import TOKEN, ADMIN_IDS
from core.database import init_db, db

# Handlerlarni import qilish
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
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def subscription_scheduler(bot: Bot):
    """Obunasi tugagan haydovchilarni tekshirish"""
    while True:
        try:
            expired = await db.get_expired_drivers()
            if expired:
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
                    except Exception as e:
                        logger.warning(f"Message to {dr_data['telegram_id']} failed: {e}")
            await asyncio.sleep(3600) # Har soatda bir marta
        except Exception as e:
            logger.error(f"Subscription scheduler error: {e}")
            await asyncio.sleep(60)

# Global Bot va Dispatcher obyektlari
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher(storage=MemoryStorage())

async def on_startup(bot: Bot):
    # Ma'lumotlar bazasini yaratish
    await init_db()
    logger.info("✅ Database initialized")
    
    # Sessions papkasini yaratish
    os.makedirs('sessions', exist_ok=True)
    
    # Avtomatik vazifalarni orqa fonda boshlash
    asyncio.create_task(subscription_scheduler(bot))
    asyncio.create_task(start_all_ads(bot))

    # Bot menyusini sozlash
    await bot.set_my_commands([
        BotCommand(command="/start", description="Botni ishga tushirish"),
        BotCommand(command="/help", description="Yordam va qo'llanma")
    ])

async def main():
    # Middleware-larni ro'yxatdan o'tkazish
    dp.message.middleware(MaintenanceMiddleware())
    dp.callback_query.middleware(MaintenanceMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Router-larni (handlerlar) ulash
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(driver.router)
    dp.include_router(passenger.router)
    dp.include_router(bridge.router)
    dp.include_router(avto_xabar_manage.router)
    dp.include_router(avto_xabar_add.router)
    dp.include_router(chat_member.router)
    dp.include_router(common.router)

    # Botni ishga tushirish qismi
    await on_startup(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("🚀 JONLI TAXI BOT is running on Render!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # 1. Render talab qiladigan Web Serverni alohida oqimda ishga tushiramiz
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Python 3.11/3.14 uchun barqaror Event Loop
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually")
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
