from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.config import ADMIN_CONTACT


def _normalize_telegram_url(url: str) -> str:
    """Telegram username yoki URL ni to'g'ri HTTPS formatga keltiradi."""
    url = url.strip()
    if not url:
        return "https://t.me/"
    if url.startswith("https://"):
        return url
    if url.startswith("http://"):
        return "https://" + url[7:]
    if url.startswith("t.me/"):
        return "https://" + url
    if url.startswith("@"):
        return f"https://t.me/{url[1:]}"  # ✅ Bo'shliqsiz!
    return f"https://t.me/{url}"  # ✅ Bo'shliqsiz!


def _build_admin_contact_url(contact: str) -> str:
    """
    Admin aloqa uchun to'g'ri URL yasaydi.
    Agar contact faqat raqamlardan iborat bo'lsa → tg://user?id=...
    Aks holda → https://t.me/... formatiga o'tkaziladi.
    """
    contact = contact.strip()
    if not contact:
        return "https://t.me/"
    if contact.isdigit():
        return f"tg://user?id={contact}"
    return _normalize_telegram_url(contact)


# === FOYDALANUVCHI KLAVIATURALARI ===

def role_kb():
    contact_url = _build_admin_contact_url(str(ADMIN_CONTACT))
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🙋‍♂️ Yo'lovchiman", callback_data="role_passenger"),
            InlineKeyboardButton(text="🚕 Haydovchiman", callback_data="role_driver")
        ],
        [
            InlineKeyboardButton(
                text="📂 JONLI TAXI — Barcha guruhlar (10 ta)",
                url="https://t.me/addlist/7N6UCOxaihcwM2M6"
            )
        ],
        [
            InlineKeyboardButton(text="ℹ️ Bot haqida", callback_data="bot_info"),
            InlineKeyboardButton(text="💬 Admin", url=contact_url)
        ],
    ])


def passenger_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚖 Jo'nab ketish", callback_data="p_taxi")],
        [InlineKeyboardButton(text="📦 Jo'natma yuborish", callback_data="p_delivery")],
        [InlineKeyboardButton(text="👥 VIP Xizmatlar", callback_data="p_vip")],
        [
            InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_role")
        ]
    ])


def driver_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Profilim", callback_data="d_profile")],
        [InlineKeyboardButton(text="💰 Balansni to'ldirish", callback_data="d_refill")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role")]
    ])

def locations_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Andijon", callback_data="loc_Andijon"),
            InlineKeyboardButton(text="Namangan", callback_data="loc_Namangan"),
            InlineKeyboardButton(text="Farg‘ona", callback_data="loc_Farg‘ona")
        ],
        [InlineKeyboardButton(text="Toshkent", callback_data="loc_Toshkent")],
        [InlineKeyboardButton(text="Qo‘shimcha manzil yozish...", callback_data="loc_custom")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role")]
    ])


def destinations_kb(from_loc):
    if from_loc in ["Andijon", "Namangan", "Farg‘ona"]:
        kb = [
            [
                InlineKeyboardButton(text="Toshkent", callback_data="dest_Toshkent"),
                InlineKeyboardButton(text="Chirchiq", callback_data="dest_Chirchiq"),
                InlineKeyboardButton(text="Angren", callback_data="dest_Angren")
            ],
            [InlineKeyboardButton(text="Boshqa...", callback_data="dest_custom")],
            [
                InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_from"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_role")
            ]
        ]
    else:
        kb = [
            [
                InlineKeyboardButton(text="Andijon", callback_data="dest_Andijon"),
                InlineKeyboardButton(text="Namangan", callback_data="dest_Namangan"),
                InlineKeyboardButton(text="Farg‘ona", callback_data="dest_Farg‘ona")
            ],
            [InlineKeyboardButton(text="Boshqa...", callback_data="dest_custom")],
            [
                InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_from"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_role")
            ]
        ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def time_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Bugun", callback_data="time_today"),
            InlineKeyboardButton(text="📅 Ertaga", callback_data="time_tomorrow")
        ],
        [InlineKeyboardButton(text="🕒 Aniq vaqt kiriting...", callback_data="time_custom")],
        [
            InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_dest"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_role")
        ]
    ])


def skip_kb(callback_data):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎤 Ovozli xabar yozish 🎧", callback_data="order_voice")],
        [InlineKeyboardButton(text="⏩ O'tkazib yuborish", callback_data="skip_details")],
        [
            InlineKeyboardButton(text="⬅️ Ortga", callback_data=callback_data),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_role")
        ]
    ])


def car_types_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Damas", callback_data="car_Damas"),
            InlineKeyboardButton(text="Gentra", callback_data="car_Gentra"),
            InlineKeyboardButton(text="Cobalt", callback_data="car_Cobalt")
        ],
        [
            InlineKeyboardButton(text="Nexia", callback_data="car_Nexia"),
            InlineKeyboardButton(text="Boshqa...", callback_data="car_custom")
        ],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role")]
    ])

def confirm_order_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buyurtmani yuborish", callback_data="confirm_order")],
        [InlineKeyboardButton(text="↩️ Barchasini qayta to‘ldirish", callback_data="back_to_role")]
    ])


def back_kb(callback_data):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data=callback_data)]
    ])


def skip_location_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏩ O'tkazib yuborish", callback_data="skip_location")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_dest")]
    ])


def accept_order_kb(order_id, user_id, phone):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Profil", url=f"tg://user?id={user_id}")],
        [InlineKeyboardButton(text="✅ Buyurtmani qabul qilish", callback_data=f"accept_{order_id}")]
    ])


def check_sub_kb(channel_url):
    url = _normalize_telegram_url(channel_url)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Guruhga qo'shiling", url=url)],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role")]
    ])


# === ADMIN PANEL KLAVIATURALARI ===

def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Dashboard & Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="🚗 Haydovchilar Markazi", callback_data="admin_drivers_menu")
        ],
        [
            InlineKeyboardButton(text="📦 Buyurtmalar (Barcha)", callback_data="admin_orders"),
            InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users_menu")
        ],
        [
            InlineKeyboardButton(text="💰 To'lovlar & Moliya", callback_data="admin_payments_menu"),
            InlineKeyboardButton(text="📢 Reklama Yuborish", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="👥 Guruhlar", callback_data="admin_groups"),
            InlineKeyboardButton(text="🛡 Adminlar", callback_data="admin_manage_admins")
        ],
        [
            InlineKeyboardButton(text="⚙️ Tizim Sozlamalari", callback_data="admin_settings"),
            InlineKeyboardButton(text="🤖 Avto Xabar", callback_data="admin_avto_xabar")
        ],
        [
            InlineKeyboardButton(text="🦅 Grabber", callback_data="admin_grabber"),
            InlineKeyboardButton(text="🚫 Qora Ro'yxat", callback_data="admin_blacklist")
        ],
        [
            InlineKeyboardButton(text="📁 Baza Backup", callback_data="admin_download_db"),
            InlineKeyboardButton(text="📝 Tizim Jurnali", callback_data="admin_view_logs")
        ],
        [InlineKeyboardButton(text="🏥 Tizim Monitori (Health)", callback_data="admin_health")]
    ])

def admin_drivers_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Faol Haydovchilar", callback_data="show_active_drivers"),
            InlineKeyboardButton(text="⏳ Kutilayotganlar", callback_data="show_pending_drivers")
        ],
        [
            InlineKeyboardButton(text="💎 VIP Haydovchilar", callback_data="show_vip_drivers"),
            InlineKeyboardButton(text="🔴 Rad etilganlar", callback_data="show_rejected_drivers")
        ],
        [InlineKeyboardButton(text="🔎 Haydovchi Qidirish", callback_data="admin_search_user")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])




def admin_users_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚗 Haydovchilar", callback_data="show_all_drivers"),
            InlineKeyboardButton(text="🚶 Yo'lovchilar", callback_data="show_all_passengers")
        ],
        [
            InlineKeyboardButton(text="💎 VIP Haydovchilar", callback_data="show_vip_drivers"),
            InlineKeyboardButton(text="🚫 Blacklist", callback_data="admin_blacklist")
        ],
        [
            InlineKeyboardButton(text="🌐 Barcha foydalanuvchilar", callback_data="show_all_users_combined"),
            InlineKeyboardButton(text="🔎 Qidiruv", callback_data="admin_search_user")
        ],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])


def admin_driver_manage_kb(tid, current_status='active'):
    # Granular management for driver
    rows = [
        [InlineKeyboardButton(text="💰 Balansni To'ldirish", callback_data=f"refill_one_{tid}")],
        [InlineKeyboardButton(text="✉️ Shaxsiy Xabar Yuborish", callback_data=f"message_user_{tid}")],
        [InlineKeyboardButton(text="🗓 Obunani Uzaytirish (30 kun)", callback_data=f"extend_sub_{tid}")],
        [InlineKeyboardButton(text="👤 Profil (Telegram)", url=f"tg://user?id={tid}")]
    ]
    
    # Status toggles
    status_row = []
    if current_status != 'active':
        status_row.append(InlineKeyboardButton(text="✅ Aktiv", callback_data=f"set_status_active_{tid}"))
    if current_status != 'rejected':
        status_row.append(InlineKeyboardButton(text="❌ Rad Etish", callback_data=f"set_status_rejected_{tid}"))
    if status_row:
        rows.append(status_row)
        
    rows.append([InlineKeyboardButton(text="🚫 Qora Ro'yxat (Blok)", callback_data=f"block_user_{tid}")])
    rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_drivers_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_order_manage_kb(oid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Buyurtmani o'chirish", callback_data=f"delete_order_{oid}")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_orders")]
    ])


def admin_payments_menu_kb(pending_count=0):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📂 Kutilayotgan To'lovlar ({pending_count})", callback_data="admin_payments_pending")],
        [InlineKeyboardButton(text="📜 Barcha To'lovlar Tarixi", callback_data="admin_payments_history")],
        [InlineKeyboardButton(text="💳 Karta Ma'lumotlarini Sozlash", callback_data="admin_edit_card")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])


def admin_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Admin Menyu", callback_data="admin_main_menu")]
    ])


def back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="back_to_role")]
    ])
def admin_avto_xabar_kb(pending_count=0):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 To'lovlar ({pending_count})", callback_data="admin_avto_payments")],
        [InlineKeyboardButton(text="✏️ Narxni o'zgartirish", callback_data="edit_avto_fee")],
        [InlineKeyboardButton(text="📋 Guruhlar ro'yxati", callback_data="edit_avto_groups")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])


def admin_avto_pay_manage_kb(pid, uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"avtopay_ok_{pid}_{uid}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"avtopay_no_{pid}_{uid}")
        ],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_avto_payments")]
    ])
