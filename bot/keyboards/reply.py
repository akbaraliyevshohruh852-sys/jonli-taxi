from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def phone_kb() -> ReplyKeyboardMarkup:
    """Telefon raqamini kontakt orqali so'rash"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def location_kb() -> ReplyKeyboardMarkup:
    """Lokatsiya yuborish + o'tkazib yuborish imkoniyati"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyamni yuborish", request_location=True)],
            [KeyboardButton(text="⏩ O'tkazib yuborish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def location_only_kb() -> ReplyKeyboardMarkup:
    """Faqat lokatsiya yuborish (majburiy)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyamni yuborish", request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def main_menu_passenger() -> ReplyKeyboardMarkup:
    """Yo'lovchi asosiy menyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚖 Jo'nab ketish")],
            [KeyboardButton(text="📦 Jo'natma yuborish")],
            [KeyboardButton(text="👥 VIP Xizmatlar")],
            [
                KeyboardButton(text="👤 Shaxsiy kabinet"),
                KeyboardButton(text="⬅️ Ortga qaytish")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Qayerga boramiz? 😊"
    )


def main_menu_driver() -> ReplyKeyboardMarkup:
    """Haydovchi asosiy menyusi (hozircha minimal)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Profilim")],
            [KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Kerakli bo'limni tanlang..."
    )


def main_menu_admin() -> ReplyKeyboardMarkup:
    """Admin paneli asosiy menyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🚗 Haydovchilar"),
                KeyboardButton(text="📊 Umumiy statistika")
            ],
            [
                KeyboardButton(text="📢 Xabar yuborish"),
                KeyboardButton(text="💰 Balans to'ldirish")
            ],
            [KeyboardButton(text="⬅️ Asosiy menyu")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Boshqaruv paneli..."
    )


# Qo'shimcha foydali funksiyalar (keyinroq ishlatishingiz mumkin)

def yes_no_kb() -> ReplyKeyboardMarkup:
    """Ha / Yo'q tugmalari"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ha"), KeyboardButton(text="❌ Yo'q")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def back_kb() -> ReplyKeyboardMarkup:
    """Faqat ortga tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def remove_keyboard() -> ReplyKeyboardMarkup:
    """Klaviaturani to'liq o'chirish"""
    return ReplyKeyboardRemove()
