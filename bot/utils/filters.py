from aiogram.filters import Filter
from aiogram import types
import core.database as db
from core.config import ADMIN_IDS

def norm(t):
    if not t: return ""
    return t.replace("‘", "'").replace("’", "'").strip()

class SettingBtn(Filter):
    """
    Buttons filtered by DB settings.
    """
    def __init__(self, key, defaults):
        self.key = key
        self.defaults = [norm(d) for d in defaults]
        
    async def __call__(self, message: types.Message) -> bool:
        if not message.text: return False
        
        m_text = norm(message.text)
        
        # Try DB setting first
        val = await db.get_setting(self.key)
        if val and m_text == norm(val):
            return True
        
        # Try defaults
        return m_text in self.defaults

class IsAdmin(Filter):
    async def __call__(self, event: types.TelegramObject) -> bool:
        from core.config import ADMIN_IDS
        # 1. Hardcoded adminlar
        if event.from_user.id in ADMIN_IDS:
            return True
            
        # 2. Bazadagi qo'shimcha adminlar
        add_admins = await db.get_setting('additional_admins', '')
        if add_admins:
            try:
                ids = [int(i.strip()) for i in add_admins.split(",") if i.strip()]
                return event.from_user.id in ids
            except: pass
            
        return False

class IsDriver(Filter):
    async def __call__(self, message: types.Message) -> bool:
        dr = await db.get_driver(message.from_user.id)
        # Barcha turdagi haydovchilarga ruxsat (active, offline, pending)
        # Faqat blocked foydalanuvchilar filtrdan o'tmaydi
        return dr is not None and dr['status'] != 'blocked'

class IsPassenger(Filter):
    async def __call__(self, message: types.Message) -> bool:
        p = await db.get_passenger(message.from_user.id)
        return p is not None
