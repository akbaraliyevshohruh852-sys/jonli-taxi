from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired, FloodWait
from core.config import API_ID, API_HASH, ADMIN_IDS
from bot.keyboards.avto_xabar import request_contact_kb, cancel_kb, code_not_received_kb, main_control_kb
from core import database as db
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

router = Router()

class AddAccount(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()

@router.callback_query(F.data == "add_profile")
async def start_add_account(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⚠️ Bu bo'lim faqat adminlar uchun!", show_alert=True)
        return
        
    await callback.message.delete()
    await callback.message.answer(
        "📲 Telegram akkauntingizni ulash uchun telefon raqamingiz kerak.\n\n"
        "👉 «📲 Raqamni yuborish» tugmasini bosing yoki +998... formatida yozing.",
        reply_markup=request_contact_kb()
    )
    await state.set_state(AddAccount.waiting_for_phone)

@router.message(F.text.contains("/cancel"))
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Amallar bekor qilindi.", reply_markup=main_control_kb())

@router.message(AddAccount.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    elif message.text:
        phone = message.text.strip().replace(" ", "")
        # Validate phone number: must be digits only after stripping +, and at least 9 digits
        clean_phone = phone.replace("+", "")
        if not (clean_phone.isdigit() and len(clean_phone) >= 9):
            await message.answer("⚠️ Iltimos, telefon raqamingizni to'g'ri formatda kiriting (masalan: +998901234567)")
            return
    else:
        return
        
    if not phone.startswith("+"):
        phone = "+" + phone

    logger.info(f"Attempting to send code to {phone}")
    msg = await message.answer("🔄 Kod yuborilmoqda, kuting...", reply_markup=cancel_kb())
    
    # Use absolute path for sessions directory
    session_dir = os.path.join(os.path.abspath(os.getcwd()), "sessions")
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
        
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    session_path = os.path.join(session_dir, clean_phone)

    client = Client(
        name=session_path,
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=phone,
        device_model="Motorola Moto G (6)",
        system_version="Android 8.1.0",
        app_version="10.8.1"
    )
    
    try:
        await client.connect()
        code_hash = await client.send_code(phone)
        await state.update_data(client=client, phone=phone, code_hash=code_hash.phone_code_hash)
        
        try:
            await msg.edit_text("✅ Kod yuborildi.")
        except:
            pass
        
        await message.answer(
            "📩 Telegram'dan kelgan 5 xonali kodni yuboring.\n\n"
            "⚠️ <b>DIQQAT:</b> Kodni o'zini yuborsangiz yoki forward qilsangiz, Telegram uni darhol <b>YAROQSIZ</b> qilib qo'yadi!\n\n"
            "🔹 Shuning uchun kodga <b>harf qo'shib</b> yuboring.\n"
            "✅ <b>Masalan:</b> <code>kod12345</code> yoki <code>a12345</code>\n\n"
            "⏱ Agar kod 1 daqiqada kelmasa, pastdagi tugmani bosing:",
            reply_markup=code_not_received_kb(),
            parse_mode="HTML"
        )
        await state.set_state(AddAccount.waiting_for_code)
    except Exception as e:
        err_text = str(e)
        logger.error(f"Send code error for {phone}: {err_text}")
        try:
            if "PHONE_NUMBER_BANNED" in err_text:
                await msg.edit_text("❌ Bu raqam Telegram tomonidan bloklangan.")
            elif "FLOOD_WAIT" in err_text:
                await msg.edit_text("⚠️ Ko'p urinish bo'ldi. Biroz kutib keyinroq harakat qiling.")
            else:
                await msg.edit_text(f"❌ Xatolik yuz berdi: {err_text}")
        except:
            await message.answer(f"❌ Xatolik: {err_text}")
            
        if client.is_connected:
            await client.disconnect()
        await state.clear()

@router.callback_query(F.data == "resend_code")
async def resend_code(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client = data.get('client')
    phone = data.get('phone')
    
    if not client or not phone:
        await callback.answer("Sessiya topilmadi, qaytadan boshlang", show_alert=True)
        return
    
    try:
        if not client.is_connected:
            await client.connect()
        code_hash = await client.send_code(phone)
        await state.update_data(code_hash=code_hash.phone_code_hash)
        await callback.answer("Kod qayta yuborildi!", show_alert=True)
    except Exception as e:
        await callback.answer(f"Xatolik qayta yuborishda: {e}", show_alert=True)

@router.message(AddAccount.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    if not message.text:
        return

    # If user sends a command, clear state and let other routers handle it
    if message.text.startswith("/"):
        if "/cancel" in message.text:
            await cancel_action(message, state)
        else:
            await state.clear()
            # We don't return here to let the dispatcher continue to other routers
            # Actually, in aiogram, once a handler matches, it stops. 
            # We should probably answer and clear.
            await message.answer("🔄 Jarayon to'xtatildi.", reply_markup=main_control_kb())
        return
        
    data = await state.get_data()
    client = data.get('client')
    phone = data.get('phone')
    code_hash = data.get('code_hash')
    
    if not client or not phone or not code_hash:
        await message.answer("⚠️ Sessiya yo'qolgan. Qaytadan boshlang: /cancel")
        await state.clear()
        return

    import re
    code = re.sub(r'\D', '', message.text)
    
    if not code:
        await message.answer("⚠️ Iltimos, kodni ichida raqamlar bo'lishiga ishonch hosil qiling (masalan: kod12345).")
        return
        
    logger.info(f"Processing code for {phone}: {code}")
    
    try:
        if not client.is_connected:
            await client.connect()
            
        # Add a small delay to mimic human behavior and avoid "Shared Code" detection
        await asyncio.sleep(3)
        
        await client.sign_in(phone, code_hash, code)
        session_string = await client.export_session_string()
        
        user_info = await client.get_me()
        name = user_info.first_name if user_info.first_name else "Profil"
        
        await db.save_account(message.from_user.id, phone, session_string, name)
        
        await message.answer("✅ Muvaffaqiyatli ulandi!", reply_markup=main_control_kb())
        await client.disconnect()
        await state.clear()
    except SessionPasswordNeeded:
        await message.answer(
            "🔐 <b>Ikki bosqichli tasdiqlash (2FA) yoqilgan.</b>\n\n"
            "Hisobingiz parolini kiriting:\n\n"
            "❌ /cancel — bekor qilish",
            parse_mode="HTML"
        )
        await state.set_state(AddAccount.waiting_for_password)
    except (PhoneCodeInvalid, PhoneCodeExpired):
        await message.answer("❌ Noto'g'ri yoki vaqti o'tgan kod kiritildi. Iltimos, tekshirib qayta yuboring.")
    except FloodWait as e:
        logger.error(f"FloodWait error during sign_in for {phone}: {e}")
        await message.answer(f"⚠️ Ko'p urinish bo'ldi. Iltimos, {e.value} soniya kutib keyinroq harakat qiling.")
        await client.disconnect()
        await state.clear()
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Sign in error for {phone} with code '{code}': {err_msg}")
        await message.answer(f"❌ Xatolik yuz berdi: {err_msg}\nQaytadan boshlang: /cancel")
        await client.disconnect()
        await state.clear()

@router.message(AddAccount.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    if not message.text:
        return

    if message.text.startswith("/"):
        if "/cancel" in message.text:
            await cancel_action(message, state)
        else:
            await state.clear()
            await message.answer("🔄 Jarayon to'xtatildi.", reply_markup=main_control_kb())
        return
        
    data = await state.get_data()
    client = data.get('client')
    phone = data.get('phone')
    password = message.text.strip()

    if not client or not phone:
        logger.warning("Session or phone number missing from state during password processing.")
        await message.answer("⚠️ Sessiya muddati o'tgan. Qaytadan boshlang: /cancel")
        await state.clear()
        return

    logger.info(f"Attempting to process password for phone: {phone}")

    try:
        if not client.is_connected:
            await client.connect()
            
        await client.check_password(password)
        session_string = await client.export_session_string()
        
        user_info = await client.get_me()
        name = user_info.first_name if user_info.first_name else "Bosh profil"
        
        await db.save_account(message.from_user.id, phone, session_string, name)
            
        await message.answer("✅ 2FA tasdiqlandi! Ulandi.", reply_markup=main_control_kb())
        await client.disconnect()
        await state.clear()
    except Exception as e:
        err_msg = str(e)
        if "PASSWORD_HASH_INVALID" in err_msg or "password" in err_msg.lower():
            await message.answer("❌ Parol noto'g'ri. Qayta kiriting yoki /cancel qiling.")
        else:
            logger.error(f"Password check error for {phone}: {err_msg}")
            await message.answer(f"❌ Xatolik: {err_msg}")
            await client.disconnect()
            await state.clear()
