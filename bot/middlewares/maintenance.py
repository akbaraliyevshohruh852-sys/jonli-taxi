from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, types
from aiogram.types import Message, CallbackQuery
from core.database import db
from core.config import ADMIN_IDS

class MaintenanceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Check if maintenance mode is ON
        maint_mode = await db.get_setting('maintenance_mode', 'off')
        
        if maint_mode == 'on':
            # Check if user is NOT admin
            user = data.get('event_from_user')
            if user and user.id not in ADMIN_IDS:
                msg_text = (
                    "⚠️ **TEXNIK ISHLAR OLIB BORILMOQDA**\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Botda hozirda texnik ishlar ketmoqda. Iltimos, birozdan so'ng qayta urinib ko'ring.\n\n"
                    "Keltirilgan noqulayliklar uchun uzr so'raymiz."
                )
                if isinstance(event, Message):
                    await event.answer(msg_text, parse_mode="Markdown")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⚠️ Texnik ishlar ketmoqda...", show_alert=True)
                return  # Stop execution
                
        return await handler(event, data)
