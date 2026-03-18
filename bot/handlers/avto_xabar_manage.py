from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from core.config import ADMIN_IDS
from core import database as db
from bot.keyboards.avto_xabar import main_control_kb, interval_kb, subscription_buy_kb, profiles_kb
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from bot.keyboards.inline import back_to_main_kb
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = Router()

class AdCreate(StatesGroup):
    waiting_for_text = State()
    waiting_for_payment_photo = State()

async def check_sub(message: types.Message, user_id: int):
    is_active = await db.is_ad_sub_active(user_id)
    if not is_active:
        fee = await db.get_setting("avto_xabar_fee", "25000")
        card = await db.get_setting("payment_card", "9860 3501 4062 9212")
        owner = await db.get_setting("payment_card_owner", "Usmonov Samandar")
        
        text = (
            "🚀 <b>Avto Xabar xizmati faol emas!</b>\n\n"
            "Ushbu xizmat orqali e'loningizni 24/7 rejimida guruhlarga avtomatik tarqatishingiz mumkin.\n\n"
            f"💰 <b>Xizmat narxi:</b> {fee} so'm / 30 kun\n"
            f"💳 <b>Karta:</b> <code>{card}</code>\n"
            f"👤 <b>Ega:</b> {owner}\n\n"
            "To'lovni amalga oshirgach, chekni (rasmni) yuboring."
        )
        if isinstance(message, types.CallbackQuery):
            await message.message.edit_text(text, reply_markup=subscription_buy_kb(), parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=subscription_buy_kb(), parse_mode="HTML")
        return False
    return True


@router.callback_query(F.data == "buy_ad_sub")
async def buy_ad_sub_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("📸 To'lov chekini (rasmini) yuboring:")
    await state.set_state(AdCreate.waiting_for_payment_photo)


@router.message(AdCreate.waiting_for_payment_photo, F.photo)
async def process_ad_payment(message: types.Message, state: FSMContext, bot: Bot):
    fee = await db.get_setting("avto_xabar_fee", "25000")
    photo_id = message.photo[-1].file_id
    pid = await db.add_payment(message.from_user.id, int(fee), photo_id)
    
    await message.answer(
        "✅ <b>To'lov qabul qilindi!</b>\n\nAdmin tasdiqlashi bilan xizmat ishga tushadi.",
        reply_markup=main_control_kb(),
        parse_mode="HTML"
    )
    await state.clear()
    
    from core.config import ADMIN_IDS
    from bot.keyboards.inline import admin_avto_pay_manage_kb
    
    alert_text = (
        f"🤖 <b>AVTO XABAR TO'LOVI #{pid}</b>\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"💵 Summa: {fee} so'm"
    )
    
    for aid in ADMIN_IDS:
        try:
            await bot.send_photo(
                aid,
                photo=photo_id,
                caption=alert_text,
                reply_markup=admin_avto_pay_manage_kb(pid, message.from_user.id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {aid} for avto pay: {e}")


@router.callback_query(F.data == "ad_manage_text")
async def handle_elon_matni(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    logger.info(f"handle_elon_matni triggered for user {callback.from_user.id}")
    await state.clear()
    if not await check_sub(callback, callback.from_user.id):
        return
    
    ad = await db.get_ad_message(callback.from_user.id)
    text = "📝 <b>E'lon boshqaruvi</b>\n\n"
    
    if ad and ad['text']:
        text += f"<b>Joriy matn:</b>\n<i>{ad['text']}</i>"
        if ad['photo_id']:
            text += "\n\n✅ <b>Rasm biriktirilgan.</b>"
    else:
        text += "❌ Hali e'lon kiritilmagan."
        
    text += "\n\n🆕 Yangi e'lon matnini yuboring (rasm bilan bo'se, matnini rasm izohiga yozing):"
    
    await callback.message.edit_text(text, reply_markup=main_control_kb(), parse_mode="HTML")
    await state.set_state(AdCreate.waiting_for_text)


@router.message(AdCreate.waiting_for_text)
async def process_ad_content(message: types.Message, state: FSMContext):
    from bot.utils.avto_xabar_scheduler import schedule_ad_task
    
    text = ""
    photo_id = None
    
    if message.text:
        text = message.text
    elif message.photo:
        text = message.caption or ""
        photo_id = message.photo[-1].file_id
    else:
        await message.answer("❌ Iltimos, matn yoki rasm yuboring.")
        return

    default_groups = "-1002447913364,-1001402280735,-1001198647576"
    
    await db.update_ad_message(message.from_user.id, text=text, photo_id=photo_id, is_active=1)
    
    ad = await db.get_ad_message(message.from_user.id)
    schedule_ad_task(message.from_user.id, ad['interval_min'])
        
    await message.answer(
        "✅ <b>E'lon saqlandi va avto-yuborish yoqildi!</b>",
        reply_markup=main_control_kb(),
        parse_mode="HTML"
    )
    await state.clear()


@router.callback_query(F.data == "ad_manage_stat")
async def handle_stat(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    if not await check_sub(callback, callback.from_user.id):
        return
    
    ad = await db.get_ad_message(callback.from_user.id)
    if not ad:
        await callback.message.edit_text("❌ Sizda hali faol e'lon yo'q.", reply_markup=main_control_kb())
        return

    # f-string ichida apostrof muammosini hal qilish uchun o'zgaruvchilarga chiqarildi
    last_sent = ad['last_sent'] if ad['last_sent'] else "Hali yo'q"
    holati = "✅ Faol" if ad['is_active'] else "🛑 To'xtatilgan"

    text = (
        "📊 <b>E'lon statistikasi</b>\n\n"
        f"📝 Matn: {ad['text'][:50]}...\n"
        f"⏱ Interval: {ad['interval_min']} daqiqa\n"
        f"📅 Obuna tugash: {ad['expires_at']}\n"
        f"🔄 Oxirgi yuborilgan: {last_sent}\n"
        f"⚙️ Holati: {holati}"
    )
    await callback.message.edit_text(text, reply_markup=main_control_kb(), parse_mode="HTML")


@router.callback_query(F.data == "ad_manage_interval")
async def handle_interval(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    if not await check_sub(callback, callback.from_user.id):
        return
    
    ad = await db.get_ad_message(callback.from_user.id)
    interval = ad['interval_min'] if ad and ad['interval_min'] else 5
    await callback.message.edit_text(
        f"⏱ <b>Xabar yuborish oralig'ini tanlang:</b>",
        reply_markup=interval_kb(interval),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("set_int_"))
async def set_interval_callback(callback: types.CallbackQuery):
    new_interval = int(callback.data.split("_")[2])
    await db.update_ad_message(callback.from_user.id, interval=new_interval)
    await callback.answer(f"✅ Interval {new_interval}m ga o'zgartirildi.")
    await callback.message.edit_text(
        f"⏱ <b>Vaqt oralig'i:</b> {new_interval} daqiqa",
        reply_markup=interval_kb(new_interval),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "ad_manage_groups")
async def handle_groups(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    text = (
        "📋 <b>E'lon tarqatiladigan asosiy guruhlar:</b>\n\n"
        "🚕 Vodiy-Toshkent (20+ guruh)\n"
        "🚕 Toshkent-Andijon (15+ guruh)\n"
        "🚕 Toshkent-Namangan (15+ guruh)\n"
        "🚕 Toshkent-Farg'ona (15+ guruh)\n\n"
        "<i>Xabaringiz har kuni jami 60+ ta eng faol guruhlarga yuboriladi.</i>"
    )
    await callback.message.edit_text(text, reply_markup=main_control_kb(), parse_mode="HTML")


@router.callback_query(F.data == "ad_manage_start")
async def handle_start_ad(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    logger.info(f"handle_start_ad triggered for user {callback.from_user.id}")
    await state.clear()
    if not await check_sub(callback, callback.from_user.id):
        return
    
    ad = await db.get_ad_message(callback.from_user.id)
    if not ad or not ad['text']:
        await callback.message.edit_text("❌ Avval e'lon matnini kiriting!", reply_markup=main_control_kb())
        return
        
    from core.config import ADMIN_IDS
    all_workers = []
    for admin_id in ADMIN_IDS:
        accounts = await db.get_accounts(admin_id)
        if accounts:
            all_workers.extend(accounts)
            
    if not all_workers:
        logger.info(f"Starting ad {callback.from_user.id} in Bot Fallback mode (No workers found)")

    from bot.utils.avto_xabar_scheduler import schedule_ad_task
    await db.update_ad_message(callback.from_user.id, is_active=1)
    ad = await db.get_ad_message(callback.from_user.id)
    schedule_ad_task(callback.from_user.id, ad['interval_min'])
    await callback.message.edit_text(
        "🚀 <b>Ishga tushdi!</b>\n\nE'loningiz navbatga qo'shildi va guruhlarga yuboriladi.",
        reply_markup=main_control_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "ad_manage_stop")
async def handle_stop_ad(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("To'xtatildi", show_alert=True)
    await state.clear()
    await db.update_ad_message(callback.from_user.id, is_active=0)
    await callback.message.edit_text(
        "🛑 <b>To'xtatildi.</b>",
        reply_markup=main_control_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "ad_manage_home")
async def handle_back_home(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    await state.clear()
    from bot.handlers.common import cmd_start
    await callback.message.delete()
    await cmd_start(callback.message, state, bot)


@router.callback_query(F.data == "ad_manage_profiles")
async def handle_profiles(callback: types.CallbackQuery):
    if not await check_sub(callback, callback.from_user.id):
        return
    accounts = await db.get_accounts(callback.from_user.id)
    await callback.message.edit_text(
        "👤 <b>PROFILLARNI BOSHQARISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Bu yerda siz ulangan akauntlaringizni ko'rishingiz yoki yangi akaunt qo'shishingiz mumkin.",
        reply_markup=profiles_kb(accounts),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sel_acc_"))
async def handle_sel_acc(callback: types.CallbackQuery):
    acc_id = int(callback.data.split("_")[-1])
    await callback.answer("Profil tanlandi. O'chirish funksiyasi tez orada qo'shiladi.", show_alert=True)


@router.callback_query(F.data == "back_to_main")
async def handle_back_to_ad_main(callback: types.CallbackQuery):
    await callback.answer()
    text = (
        "🤖 <b>AVTO XABAR BO'LIMI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<i>Boshqaruv menyusidan kerakli bo'limni tanlang:</i>"
    )
    await callback.message.edit_text(text, reply_markup=main_control_kb(), parse_mode="HTML")


@router.message(Command("check_bot_groups"))
async def check_bot_groups_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    groups = await db.get_bot_groups()
    text = f"📋 <b>Bot guruhlari statistikasi:</b>\n\nJami: {len(groups)} ta guruh\n"
    if groups:
        text += f"IDlar:\n<code>{', '.join(map(str, groups))}</code>"
    await message.answer(text, parse_mode="HTML")


@router.message(Command("add_groups"))
async def add_groups_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "⚠️ Guruh IDlarini vergul bilan yuboring.\n\nMisol:\n<code>/add_groups -100123,-100456</code>",
            parse_mode="HTML"
        )
        return
    
    ids_raw = args[1].replace("\n", ",").split(",")
    count = 0
    for rid in ids_raw:
        try:
            gid = int(rid.strip())
            await db.save_bot_group(gid, f"Qo'lda qo'shildi ({gid})")
            count += 1
        except:
            continue
        
    await message.answer(f"✅ {count} ta guruh IDlari muvaffaqiyatli saqlandi!")
    logger.info(f"Admin {message.from_user.id} manually added {count} groups")
