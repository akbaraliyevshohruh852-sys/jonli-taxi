# core/config.py
import os

from dotenv import load_dotenv

# dotenv
load_dotenv()

# Telegram Bot Token
TOKEN = os.getenv("BOT_TOKEN", "8135159824:AAHfVvSrjKQ5ita9hFzyqlQWDw1ihq_WHzM")

# Pyrogram API Config
API_ID = int(os.getenv("API_ID", "32197686"))
API_HASH = os.getenv("API_HASH", "e61663d4254b75515d950f913d7d5f10")

# Adminlar ID ro'yxati
admin_ids_str = os.getenv("ADMIN_IDS", "5200168486,7937744235,193146757")
ADMIN_IDS = [int(i.strip()) for i in admin_ids_str.split(",") if i.strip()]

# Guruhlar IDlari
DRIVER_GROUP_ID = int(os.getenv("DRIVER_GROUP_ID", "-1003344171936"))
VIP_GROUP_ID = int(os.getenv("VIP_GROUP_ID", "-1003344171936"))

# Majburiy obuna bo'lish kerak bo'lgan kanallar
MANDATORY_CHANNELS = [
    {
        "chat_id": -1003623161520,
        "url": os.getenv("PUBLIC_GROUP_URL", "https://t.me/jonlitaxivodiy"),
        "name": "Jonli Taxi Vodiy"
    }
]

# Admin bilan bog'lanish
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT", "7937744235")

# Ommaviy guruh (Yo'lovchilar uchun)
PUBLIC_GROUP_URL = os.getenv("PUBLIC_GROUP_URL", "https://t.me/jonlitaxivodiy")
PUBLIC_GROUP_CHAT_ID = int(os.getenv("PUBLIC_GROUP_CHAT_ID", "-1003623161520"))

# Grabber (Xabar yig'uvchi) uchun manba guruhlar IDlari
GRABBER_SOURCES = [
    PUBLIC_GROUP_CHAT_ID,
    -1003560973274    # Yangi guruh
]

# To'lov ma'lumotlari
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "9860 3501 4062 9212")
PAYMENT_CARD_OWNER = os.getenv("PAYMENT_CARD_OWNER", "Usmonov Samandar")
PAYMENT_AMOUNT = os.getenv("PAYMENT_AMOUNT", "20000")

# Ma'lumotlar bazasi sozlamalari
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
default_db_path = os.path.join(BASE_DIR, "vodiy_express.db")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")
DB_PATH = default_db_path

# Eskiz SMS API
ESKIZ_EMAIL = os.getenv("ESKIZ_EMAIL", "")
ESKIZ_PASSWORD = os.getenv("ESKIZ_PASSWORD", "")
ESKIZ_TOKEN = os.getenv("ESKIZ_TOKEN", "")
