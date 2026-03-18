from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from bot.utils.checks import check_user_sub
from bot.keyboards.inline import check_sub_kb
from core.config import PUBLIC_GROUP_URL, ADMIN_IDS
import logging

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event: Update,
        data: dict
    ):
        # Extract user and chat type
        user = None
        is_private = False
        
        if isinstance(event, Message):
            user = event.from_user
            is_private = event.chat.type == "private"
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            is_private = event.message.chat.type == "private" if event.message else True
        
        if not user or not is_private:
            return await handler(event, data)

        # Skip admins
        if user.id in ADMIN_IDS:
            return await handler(event, data)

        # Allow specific callbacks (like checking subscription)
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)
        # Allow specific commands if needed (like /start sometimes needs to run to show welcome, but we want to block even start if not subbed)
        # Actually, /start is handled in common.py which shows the sub prompt.
        # But if we use middleware, it will block /start too. 
        # So we should intercept /start and other updates.
        
        # Bot instance from data
        bot = data['bot']
        
        # Check subscription
        is_sub = await check_user_sub(bot, user.id)
        
        if not is_sub:
            # If not subscribed, stop everything and show prompt
            text = (
                "⚠️ <b>DIQQAT!</b>\n\n"
                "Botdan foydalanish uchun rasmiy guruhimizga a'zo bo'lishingiz shart.\n"
                "Afsuski, siz guruhdan chiqib ketgansiz yoki a'zo emassiz.\n\n"
                f"📢 <b>Guruh:</b> <a href='{PUBLIC_GROUP_URL}'>Jonli Taxi | Rasmiy Guruh</a>\n\n"
                "👇 <i>A'zo bo'lib, '✅ Tasdiqlash' tugmasini bosing:</i>"
            )
            
            # Answer callback to stop loading animation
            if isinstance(event, CallbackQuery):
                await event.answer("Guruhga a'zo bo'ling!", show_alert=True)
                try:
                    await event.message.delete()
                except:
                    pass
                await event.message.answer(text, reply_markup=check_sub_kb(PUBLIC_GROUP_URL), parse_mode="HTML", disable_web_page_preview=True)
            elif isinstance(event, Message):
                await event.answer(text, reply_markup=check_sub_kb(PUBLIC_GROUP_URL), parse_mode="HTML", disable_web_page_preview=True)
            
            # Stop propagation
            return

        return await handler(event, data)
