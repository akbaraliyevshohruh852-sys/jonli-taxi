import logging
import pytz
import apscheduler.util
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes, Defaults

# --- LOGGING & MONKEYPATCH (Sizniki kabi) ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Holatlar
CHOOSE_ROLE, DRIVER_REG_NAME, DRIVER_REG_PHONE, DRIVER_REG_CAR, DRIVER_REG_NUMBER = range(5)
PASSENGER_REG_NAME, PASSENGER_REG_PHONE = range(5, 7)

# Ma'lumotlar bazasi (Simulatsiya)
users = {}  # {user_id: {role, name, phone, reg_date, is_vip}}
ADMIN_IDS = [5200168486]

# --- START FUNKSIYASI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in ADMIN_IDS:
        await admin_menu(update, context)
        return ConversationHandler.END

    if user_id in users:
        if users[user_id]['role'] == 'driver':
            await driver_menu(update, context)
        else:
            await passenger_menu(update, context)
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("🚗 Haydovchi", callback_data='role_driver')],
        [InlineKeyboardButton("👤 Yo'lovchi", callback_data='role_passenger')]
    ]
    await update.message.reply_text(
        "Assalomu alaykum! Taksi botiga xush kelibsiz. Kim bo'lib foydalanmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSE_ROLE

# --- ADMIN PANEL LOGIKASI (YANGI) ---
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['📊 Statistika', '👥 Foydalanuvchilar'], ['📢 Xabar yuborish']]
    await update.message.reply_text("👨‍💼 ADMIN PANEL", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def admin_user_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Bu funksiya "Foydalanuvchilar" tugmasi bosilganda filtr menyusini chiqaradi
    keyboard = [
        [InlineKeyboardButton("🚗 Haydovchilar", callback_data='adm_drivers')],
        [InlineKeyboardButton("🚶 Yo'lovchilar", callback_data='adm_passengers')],
        [InlineKeyboardButton("💎 VIP Haydovchilar", callback_data='adm_vip')],
        [InlineKeyboardButton("👥 Barcha foydalanuvchilar", callback_data='adm_all')]
    ]
    await update.message.reply_text("Qaysi toifani ko'rmoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard))

async def process_admin_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    filter_type = query.data.split('_')[1]
    
    found_users = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Filtrlash mantiqi
    for uid, data in users.items():
        if filter_type == 'drivers' and data['role'] == 'driver':
            found_users.append((uid, data))
        elif filter_type == 'passengers' and data['role'] == 'passenger':
            found_users.append((uid, data))
        elif filter_type == 'vip' and data.get('is_vip') and data['role'] == 'driver':
            found_users.append((uid, data))
        elif filter_type == 'all':
            found_users.append((uid, data))

    if not found_users:
        await query.message.reply_text("Hozircha bunday foydalanuvchilar yo'q.")
        return

    await query.message.reply_text(f"🔍 Natija: {len(found_users)} ta foydalanuvchi topildi.")

    for uid, data in found_users:
        # Har bir foydalanuvchi uchun alohida karta va profil tugmasi
        role_emoji = "🚗" if data['role'] == 'driver' else "🚶"
        vip_status = "✅ VIP" if data.get('is_vip') else "❌ Oddiy"
        
        text = (
            f"{role_emoji} **{data['name']}**\n"
            f"📞 Tel: {data['phone']}\n"
            f"🆔 ID: `{uid}`\n"
            f"📅 Ro'yxatdan o'tdi: {data.get('reg_date', now)}\n"
            f"💎 Status: {vip_status}"
        )
        
        # Telegram profiliga o'tish linki
        profile_btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 Profilga o'tish", url=f"tg://user?id={uid}")
        ]])
        
        await query.message.reply_text(text, reply_markup=profile_btn, parse_mode="Markdown")

# --- RO'YXATDAN O'TISH (SAQLASH QISMI YANGILANDI) ---
async def driver_reg_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users[user_id] = {
        'role': 'driver', 
        'name': context.user_data['name'], 
        'phone': context.user_data['phone'],
        'reg_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'is_vip': False # Default holatda VIP emas
    }
    await update.message.reply_text("✅ Haydovchi sifatida ro'yxatdan o'tdingiz!")
    await driver_menu(update, context)
    return ConversationHandler.END

async def passenger_reg_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users[user_id] = {
        'role': 'passenger', 
        'name': context.user_data['name'], 
        'phone': update.message.text,
        'reg_date': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    await update.message.reply_text("✅ Yo'lovchi sifatida ro'yxatdan o'tdingiz!")
    await passenger_menu(update, context)
    return ConversationHandler.END

# --- MENYULAR ---
async def driver_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("🚗 Haydovchi paneli:", reply_markup=ReplyKeyboardMarkup([['📊 Statistika']], resize_keyboard=True))

async def passenger_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("👤 Yo'lovchi paneli:", reply_markup=ReplyKeyboardMarkup([['🚖 Taksi chaqirish']], resize_keyboard=True))

# --- MAIN ---
def main():
    application = Application.builder().token("8288534129:AAFYH9lCpXVSsiLpqZ5IfRcBotrgLRuT558").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_ROLE: [CallbackQueryHandler(lambda u, c: choose_role(u, c))], # choose_role funksiyasini saqlab qolasiz
            DRIVER_REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_reg_name)],
            DRIVER_REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_reg_phone)],
            DRIVER_REG_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_reg_car)],
            DRIVER_REG_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, driver_reg_complete)],
            PASSENGER_REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, passenger_reg_name)],
            PASSENGER_REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, passenger_reg_complete)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    # Handlerlar
    application.add_handler(conv_handler)
    # Admin tugmalari uchun handlerlar
    application.add_handler(MessageHandler(filters.Text("👥 Foydalanuvchilar"), admin_user_filters))
    application.add_handler(CallbackQueryHandler(process_admin_query, pattern="^adm_"))
    
    application.run_polling()

if __name__ == '__main__':
    main()
