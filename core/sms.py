import aiohttp
import logging
from core.config import ESKIZ_EMAIL, ESKIZ_PASSWORD

logger = logging.getLogger(__name__)

class EskizSMS:
    BASE_URL = "https://notify.eskiz.uz/api"

    def __init__(self, email=ESKIZ_EMAIL, password=ESKIZ_PASSWORD):
        self.email = email
        self.password = password
        self.token = None

    async def get_token(self):
        """Eskiz API dan token olish yoki yangilash."""
        if self.token:
            return self.token

        url = f"{self.BASE_URL}/auth/login"
        data = {
            "email": self.email,
            "password": self.password
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        self.token = res_json.get('data', {}).get('token')
                        logger.info("Eskiz SMS API tokeni muvaffaqiyatli olindi.")
                        return self.token
                    else:
                        error_text = await response.text()
                        logger.error(f"Eskiz SMS API token olishda xatolik: {response.status} - {error_text}")
                        return None
            except Exception as e:
                logger.error(f"Eskiz SMS API ulanishda xatolik: {e}")
                return None

    async def send_sms(self, phone: str, message: str, from_name: str = "4546"):
        """SMS yuborish."""
        token = await self.get_token()
        if not token:
            logger.error("Token bo'lmagani uchun SMS yuborib bo'lmadi.")
            return False

        url = f"{self.BASE_URL}/message/sms/send"
        
        # Telefon raqam faqat raqamlardan iborat bo'lishi kerak va + siz
        phone = ''.join(filter(str.isdigit, str(phone)))
        if phone.startswith('8'): # 890... -> 99890...
            phone = '998' + phone[1:]
        elif not phone.startswith('998'):
            phone = '998' + phone

        headers = {
            "Authorization": f"Bearer {token}"
        }
        data = {
            "mobile_phone": phone,
            "message": message,
            "from": from_name,
            "callback_url": ""
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=data) as response:
                    res_json = await response.json()
                    if response.status == 200:
                        logger.info(f"SMS yuborildi ({phone}): {res_json}")
                        return True
                    elif response.status == 401: # Token eskirgan bo'lishi mumkin
                        self.token = None
                        logger.warning("Eskiz tokeni eskirgan, yangilanmoqda...")
                        return await self.send_sms(phone, message, from_name)
                    else:
                        logger.error(f"SMS yuborishda xatolik: {response.status} - {res_json}")
                        return False
            except Exception as e:
                logger.error(f"SMS yuborishda ulanish xatosi: {e}")
                return False

# Global instance
sms_client = EskizSMS()
