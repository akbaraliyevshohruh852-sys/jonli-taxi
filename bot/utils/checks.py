from aiogram import Bot
from core.config import PUBLIC_GROUP_CHAT_ID, ADMIN_IDS
import time
import logging
from core import database as db

logger = logging.getLogger(__name__)

# Cache: {user_id: (is_subscribed: bool, timestamp: float)}
_sub_cache = {}


async def check_user_sub(bot: Bot, user_id: int, bypass_cache: bool = False) -> bool:
    """
    Foydalanuvchining majburiy kanallarga obuna bo'lganligini tekshiradi.
    100% ishonchli bo'lish uchun: xatolarni batafsil log qiladi, cache ni to'g'ri boshqaradi va bot huquqlarini hisobga oladi.
    """
    # 1. Majburiy obuna sozlamasi o'chirilgan bo'lsa – o'tkazib yuboramiz
    is_enabled = await db.get_setting('mandatory_sub', 'on')
    if is_enabled != 'on':
        logger.info(f"Mandatory sub off for user {user_id}")
        return True

    # 2. Adminlarni tekshirmaymiz
    if user_id in ADMIN_IDS:
        logger.info(f"Admin skip for user {user_id}")
        return True

    # 3. Cache dan tekshirish (bypass bo'lsa yoki cache yo'q bo'lsa yangidan tekshiradi)
    now = time.time()
    if not bypass_cache and user_id in _sub_cache:
        status, ts = _sub_cache[user_id]
        ttl = 300 if status else 60  # Muvaffaqiyatli: 5 daqiqa, muvaffaqiyatsiz: 1 daqiqa
        if now - ts < ttl:
            logger.info(f"Cache hit for user {user_id}: {status}")
            return status

    # 4. Majburiy kanallarni bazadan olish
    channels_str = await db.get_setting('mandatory_channels', str(PUBLIC_GROUP_CHAT_ID))
    channels_str = channels_str.strip() if channels_str else ""
    if not channels_str:
        logger.warning("No mandatory channels set")
        return True

    channels_list = [c.strip() for c in channels_str.split(",") if c.strip()]
    if not channels_list:
        logger.warning("Channels list empty after parsing")
        return True

    # 5. Har bir kanalni tekshirish (xatolarda aniq log)
    final_status = True
    for channel in channels_list:
        try:
            # Chat ID ni to'g'ri int ga aylantirish va tekshirish
            if not (channel.isdigit() or (channel.startswith('-') and channel[1:].isdigit())):
                logger.error(f"Invalid channel format: {channel} (must be int like -1234567890)")
                continue

            chat_id = int(channel)

            # Botning o'zi kanal a'zosi ekanligini oldin tekshirish (muammo bo'lsa)
            try:
                bot_member = await bot.get_chat_member(chat_id, bot.id)
                if bot_member.status not in ("member", "administrator", "creator"):
                    logger.error(f"Bot not member in channel {channel}. Status: {bot_member.status}")
                    continue
            except Exception as bot_e:
                logger.error(f"Bot membership check failed for {channel}: {bot_e}")
                continue

            # Foydalanuvchini tekshirish
            member = await bot.get_chat_member(chat_id, user_id)
            is_sub = member.status in ("member", "administrator", "creator")  # restricted olib tashlandi, chunki ko'pincha muammo

            if not is_sub:
                logger.info(f"User {user_id} not subscribed to {channel}. Status: {member.status}")
                final_status = False
                break  # Birinchisidagi muammo yetarli

            logger.debug(f"User {user_id} subscribed to {channel}")

        except Exception as e:
            logger.error(f"Subscription check error for channel {channel} user {user_id}: {type(e).__name__} - {str(e)}")
            # Xato bo'lsa (masalan bot huquqi yetmasa) – False deb hisoblaymiz (xavfsizroq)
            final_status = False
            break

    # 6. Natijani cache ga saqlash
    _sub_cache[user_id] = (final_status, now)
    logger.info(f"Final sub status for user {user_id}: {final_status}")

    return final_status
