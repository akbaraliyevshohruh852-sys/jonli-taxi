from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def subscription_plans_kb():
    buttons = [
        [InlineKeyboardButton(text="💳 Sotib olish", callback_data="buy_pro_stars")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def request_contact_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )

def main_control_kb():
    buttons = [
        [InlineKeyboardButton(text="📝 E'lon matni", callback_data="ad_manage_text"), 
         InlineKeyboardButton(text="📊 Statistika", callback_data="ad_manage_stat")],
        [InlineKeyboardButton(text="⏱ Interval", callback_data="ad_manage_interval"), 
         InlineKeyboardButton(text="📋 Guruhlar", callback_data="ad_manage_groups")],
        [InlineKeyboardButton(text="👤 Profillar", callback_data="ad_manage_profiles")],
        [InlineKeyboardButton(text="▶️ Ishga tushirish", callback_data="ad_manage_start"), 
         InlineKeyboardButton(text="🛑 To'xtatish", callback_data="ad_manage_stop")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="ad_manage_home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profiles_kb(accounts: list):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if not accounts:
        kb.inline_keyboard.append([InlineKeyboardButton(text="➕ Profil qo'shish", callback_data="add_profile")])
    else:
        for acc in accounts:
            icon = "✅" if acc['status'] == "active" else "❌"
            kb.inline_keyboard.append([InlineKeyboardButton(text=f"{icon} {acc['phone']} {acc['name']}", callback_data=f"sel_acc_{acc['id']}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="➕ Yangi profil qo'shish", callback_data="add_profile")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_main")])
    return kb

def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ /cancel — bekor qilish")]],
        resize_keyboard=True
    )

def code_not_received_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❗ Kod kelmadi", callback_data="resend_code")]
    ])

def message_settings_kb():
    buttons = [
        [InlineKeyboardButton(text="📝 Matn", callback_data="msg_type_text")],
        [InlineKeyboardButton(text="🖼 Rasm+matn", callback_data="msg_type_photo")],
        [InlineKeyboardButton(text="📩 Forward 🔒", callback_data="msg_type_forward")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def interval_kb(current_interval=5):
    buttons = []
    row = []
    # Intervals: 1, 2, 3, 5, 10, 15, 20... 60
    intervals = [1, 2, 3, 5] + list(range(10, 65, 5))
    
    for i in intervals:
        text = f"✅ {i}m" if i == current_interval else f"{i}m"
        row.append(InlineKeyboardButton(text=text, callback_data=f"set_int_{i}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="Interval nima", callback_data="what_is_interval")])
    buttons.append([InlineKeyboardButton(text="Orqaga", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def subscription_buy_kb():
    buttons = [
        [InlineKeyboardButton(text="💳 Sotib olish", callback_data="buy_ad_sub")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
