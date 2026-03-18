from aiogram import Router, types, F, Bot
from aiogram.types import FSInputFile
from aiogram.filters import Command, StateFilter 
from aiogram.fsm.context import FSMContext
from bot.keyboards.inline import role_kb, check_sub_kb, passenger_main_kb, driver_main_kb
from bot.keyboards.reply import main_menu_admin, main_menu_driver, main_menu_passenger
from core.config import ADMIN_IDS, PUBLIC_GROUP_URL
from core import database as db
from bot.utils.checks import check_user_sub
import logging

logger = logging.getLogger(__name__)
router = Router()

# Creative Welcome Photo path
START_PHOTO_PATH = r"C:\Users\woxa\.gemini\antigravity\brain\01dd178d-3ba8-48ba-abcb-daf40e430a69\uploaded_image_1768107843948.png"

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    args = message.text.split() if message.text else []
    uid = message.from_user.id
    
    # 0. Blacklist Check
    if await db.is_blacklisted(uid):
        await message.answer("🚫 **SIZ BOTDAN BUTUNLAY BLOKLANGANSIZ!**\n\nSababi: Qoidalarni buzish yoki dezinformatsiya. Admin bilan bog'laning.", parse_mode="Markdown")
        return

    # 1. Referral handling
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1].replace("ref_", ""))
        # Faqat yangi foydalanuvchi bo'lsa
        if not await db.get_passenger(uid) and not await db.get_driver(uid):
            await db.add_driver_invite(referrer_id)
            # Check if reached 20
            ref_driver = await db.get_driver(referrer_id)
            if ref_driver and ref_driver['invite_count'] >= 20 and ref_driver['status'] != 'active':
                # Update status and set subscription for 30 days
                from datetime import datetime, timedelta
                sub_end = datetime.now() + timedelta(days=30)
                await db.update_driver_subscription(referrer_id, sub_end)
                try: 
                    await bot.send_message(referrer_id, "🎁 **MUBORAK BO'LSIN!**\n\nSiz 20 ta do'stingizni taklif qildingiz va 1 oylik **BEPUL VIP** maqomiga ega bo'ldingiz! 🚀\n\nSizning VIP maqomingiz 30 kun davomida faol bo'ladi.", parse_mode="Markdown")
                except: pass

    await state.clear()
    
    # 2. Mandatory Subscription Check
    is_sub = await check_user_sub(bot, uid)
    if not is_sub:
        text = (
            "🏦 <b>JONLI TAXI | RASMIY BOT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "👋 <b>Xush kelibsiz!</b>\n\n"
            "Botimiz xizmatlaridan to'liq foydalanish uchun rasmiy guruhimizga a'zo bo'lishingiz zarur:\n\n"
            f"📢 <b>Guruhimiz:</b> <a href='{PUBLIC_GROUP_URL}'>Jonli Taxi | Rasmiy Guruh</a>\n\n"
            "✨ <i>A'zo bo'lgach, '✅ Tasdiqlash' tugmasini bosing.</i>"
        )
        await message.answer(text, reply_markup=check_sub_kb(PUBLIC_GROUP_URL), parse_mode="HTML", disable_web_page_preview=True)
        return

    # User existence
    driver = await db.get_driver(uid)
    passenger = await db.get_passenger(uid)

    welcome_text = (
        "✨ <b>ASOSIY MENYU</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Xizmat turini tanlang yoki kabinetingizga o'ting: ↙️"
    )

    # Har doim asosiy rol tanlash menyusini ko'rsatish (User Request)
    await message.answer(welcome_text, reply_markup=role_kb(), parse_mode="HTML")

@router.callback_query(F.data == "check_subscription")
async def handle_check_sub(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    is_sub = await check_user_sub(bot, callback.from_user.id, bypass_cache=True)
    if is_sub:
        await callback.answer("✅ Rahmat! Obuna tasdiqlandi.", show_alert=True)
        await cmd_start(callback.message, state, bot)
    else:
        await callback.answer("❌ Siz hali guruhga a'zo bo'lmadingiz!", show_alert=True)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "❓ **BOTDAN FOYDALANISH YO'RIQNOMASI**\n\n"
        "🔹 **Yo'lovchi:** Taksi yoki yetkazib berish xizmati uchun buyurtma bering.\n"
        "🔹 **Haydovchi:** Ro'yxatdan o'ting, to'lov qiling va buyurtmalarni oling.\n\n"
        "📞 Savollar bo'lsa: @yordamchiguruh01"
    )
    await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "bot_info", StateFilter("*"))
async def handle_bot_info(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "ℹ️ <b>JONLI TAXI BOTI HAQIDA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 <b>Bu qanday bot?</b>\n"
        "Bu bot Vodiy (Andijon, Namangan, Farg'ona) va Toshkent shaharlari o'rtasida "
        "taksi xizmati hamda yuk tashish (dastavka) jarayonini osonlashtirish uchun yaratilgan.\n\n"
        "🚩 <b>Botning maqsadi:</b>\n"
        "Yo'lovchilar uchun tezkor mashina topish, haydovchilar uchun esa doimiy mijozlar bazasini shakllantirishdir.\n\n"
        "🛠 <b>Bot qanday ishlaydi?</b>\n"
        "1. Yo'lovchi buyurtma qoldiradi.\n"
        "2. Buyurtma haydovchilar guruhiga yuboriladi.\n"
        "3. Haydovchi buyurtmani qabul qiladi va yo'lovchi bilan bog'lanadi.\n\n"
        "✨ <b>Afzalliklari:</b>\n"
        "✅ Tezkorlik (24/7)\n"
        "✅ Ishonchlilik (Adminlar nazorati)\n"
        "✅ Shaffoflik (Narxlar va kelishuvlar)"
    )
    from bot.keyboards.inline import back_to_main_kb
    await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="HTML")

@router.callback_query(F.data == "avto_xabar", StateFilter("*"))
async def handle_avto_xabar(callback: types.CallbackQuery):
    await callback.answer("⏳ Ushbu xizmat tez kunda ishga tushiriladi!", show_alert=True)

@router.callback_query(F.data == "back_to_role", StateFilter("*"))
async def back_to_role(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    await state.clear()
    await cmd_start(callback.message, state, bot)
@router.callback_query(StateFilter("*"))
async def catch_all_callbacks(callback: types.CallbackQuery):
    """Barcha javob berilmagan tugmalarga javob qaytarish (spinnerni to'xtatish)"""
    try:
        await callback.answer()
    except:
        pass
