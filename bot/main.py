import asyncio
import logging
import sys
import os
from datetime import datetime

# --- MUHIM TUZATISH (Python 3.14+ va Pyrogram uchun) ---
import nest_asyncio
nest_asyncio.apply()
# -----------------------------------------------------

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
# Pydantic warning suppression
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from core.config import TOKEN, ADMIN_IDS
from core.database import init_db, db

from bot.handlers import (
    common,
    registration,
    driver,
    passenger,
    admin,
    bridge,
    avto_xabar_add,
    avto_xabar_manage,
    chat_member
)
from bot.utils.avto_xabar_scheduler import start_all_ads
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.middlewares.maintenance import MaintenanceMiddleware

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_new.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def subscription_scheduler(bot: Bot):
    while True:
        try:
            expired = await db.get_expired_drivers()
            for driver_data in expired:
                await db.update_driver_status(driver_data['telegram_id'], 'expired')
                try:
                    await bot.send_message(
                        driver_data['telegram_id'],
                        "🔴 <b>Obuna muddati tugadi!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "Sizning haydovchilik obunangiz muddati tugadi.\n"
                        "Yangi buyurtmalarni qabul qilish uchun obunani yangilang.",
                        parse_mode="HTML"
                    )
                except:
                    pass
                for aid in ADMIN_IDS:
                    try:
                        await bot.send_message(
                            aid,
                            "⚠️ <b>HAYDOVCHI OBUNASI TUGADI</b>\n"
                            "━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"👤 Ism: {driver_data['full_name']}\n"
                            f"📞 Tel: +{driver_data['phone']}\n"
                            f"🆔 ID: <code>{driver_data['telegram_id']}</code>",
                            parse_mode="HTML"
                        )
                    except:
                        pass
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Subscription scheduler error: {e}", exc_info=True)
            await asyncio.sleep(60)

async def backup_scheduler(bot: Bot):
    from aiogram.types import FSInputFile
    from core.config import DB_PATH

    while True:
        try:
            await asyncio.sleep(86400)
            if not os.path.exists(DB_PATH):
                logger.warning("DB file not found for backup")
                continue
            filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
            db_file = FSInputFile(DB_PATH, filename=filename)
            for aid in ADMIN_IDS:
                try:
                    await bot.send_document(
                        aid,
                        document=db_file,
                        caption=f"🔄 <b>AVTOMATIK ZAXIRA</b>\n"
                                f"📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(f"Backup send failed to {aid}: {e}")
        except Exception as e:
            logger.error(f"Backup scheduler error: {e}", exc_info=True)
            await asyncio.sleep(60)

# Global Instances
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def setup_dispatcher():
    # Middleware
    dp.message.middleware(MaintenanceMiddleware())
    dp.callback_query.middleware(MaintenanceMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Routers
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(driver.router)
    dp.include_router(passenger.router)
    dp.include_router(bridge.router)
    dp.include_router(chat_member.router)
    # Avto Xabar routerlarini ham yoqib qo'yamiz (requirements.txt to'g'rilandi)
    dp.include_router(avto_xabar_manage.router)
    dp.include_router(avto_xabar_add.router)
    dp.include_router(common.router)

async def on_startup(bot: Bot):
    await init_db()
    logger.info("Database initialized successfully")
    
    os.makedirs('sessions', exist_ok=True)
    
    asyncio.create_task(subscription_scheduler(bot))
    asyncio.create_task(backup_scheduler(bot))
    asyncio.create_task(start_all_ads(bot))

    await bot.set_my_commands([
        BotCommand(command="/start", description="Botni ishga tushirish"),
        BotCommand(command="/help", description="Yordam va qo'llanma")
    ])

async def main():
    setup_dispatcher()
    await on_startup(bot)

    logger.info(f"🚀 JONLI TAXI BOT starting...")
    print(f"🚀 JONLI TAXI BOT starting...")

    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Polling failed: {e}", exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
