from aiogram import Router, types, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from bot.states.states import OrderProcess, UserUpdate
from bot.keyboards.inline import destinations_kb, time_kb, skip_kb, confirm_order_kb, back_kb, locations_kb, role_kb, accept_order_kb, skip_location_kb
from bot.keyboards.reply import location_kb, main_menu_passenger, location_only_kb
from bot.utils.filters import SettingBtn
from core.config import DRIVER_GROUP_ID, VIP_GROUP_ID, PUBLIC_GROUP_URL
from core import database as db
from core.sms import sms_client
import re, logging, random

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "❌ Bekor qilish", StateFilter("*"))
async def p_cancel_order(message: types.Message, state: FSMContext, bot: Bot):
    from bot.handlers.common import cmd_start
    await state.clear()
    await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())
    await cmd_start(message, state, bot)

def fmt_p(p):
    p = re.sub(r'[^0-9]', '', str(p))
    return f"+{p}" if p else "Noma'lum"

@router.callback_query(F.data == "p_vip", StateFilter("*"))
@router.message(F.text == "👥 VIP Xizmatlar")
async def vip_services(message: types.Message | types.CallbackQuery):
    user_id = message.from_user.id
    if isinstance(message, types.CallbackQuery):
        msg_obj = message.message
        await message.answer()
    else:
        msg_obj = message

    if not await db.get_passenger(user_id):
        await msg_obj.answer("⚠️ Botdan to'liq foydalanish uchun ro'yxatdan o'ting!", reply_markup=role_kb())
        return
    
    group_url = await db.get_setting('public_group_url', 'https://t.me/jonlitaxivodiy')
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👥 Guruhga o'tish", url=group_url)],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role")]
    ])
    
    text = (
        "📢 <b>OMMAVIY GURUHIMIZ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Hurmatli yo'lovchi! Siz buyurtmalarni bizning ommaviy guruhimiz orqali ham qoldirishingiz mumkin. "
        "U yerda ko'plab haydovchilar Sizning so'rovingizni kutishmoqda.\n\n"
        "👇 <b>Guruhga qo'shilish uchun quyidagi tugmani bosing:</b>"
    )

    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")



@router.callback_query(F.data == "role_profile", StateFilter("*"))
async def p_profile_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    u = await db.get_passenger(callback.from_user.id)
    if not u:
        from bot.keyboards.inline import role_kb
        await callback.message.edit_text(
            "⚠️ **Avval ro'yxatdan o'ting!**\n\n"
            "Shaxsiy kabinetga kirish uchun yo'lovchi sifatida ro'yxatdan o'tishingiz kerak.",
            reply_markup=role_kb(),
            parse_mode="Markdown"
        )
        return
    
    text = (
        "👤 **SIZNING SHAXSIY SAHIFANGIZ**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ **Ismingiz:** {u['full_name']}\n"
        f"📞 **Bog'lanish raqami:** `{fmt_p(u['phone'])}` \n\n"
        "Biz bilan ekanligingizdan mamnunmiz! Sizning har bir safaringiz zavqli bo'lsin."
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Ismni o'zgartirish", callback_data="change_name_passenger")],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.message(F.text == "👤 Shaxsiy kabinet", StateFilter("*"))
async def p_profile_msg(message: types.Message):
    u = await db.get_passenger(message.from_user.id)
    if not u:
        from bot.keyboards.inline import role_kb
        await message.answer(
            "⚠️ **Avval ro'yxatdan o'ting!**\n\n"
            "Shaxsiy kabinetga kirish uchun yo'lovchi sifatida ro'yxatdan o'tishingiz kerak.",
            reply_markup=role_kb(),
            parse_mode="Markdown"
        )
        return
    
    text = (
        "👤 **SIZNING SHAXSIY SAHIFANGIZ**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ **Ismingiz:** {u['full_name']}\n"
        f"📞 **Bog'lanish raqami:** `{fmt_p(u['phone'])}` \n\n"
        "Biz bilan ekanligingizdan mamnunmiz! Sizning har bir safaringiz zavqli bo'lsin."
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Ismni o'zgartirish", callback_data="change_name_passenger")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "change_name_passenger")
async def p_change_name_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("📝 **Yangi ismingizni kiriting:**", parse_mode="Markdown")
    await state.set_state(UserUpdate.waiting_new_name)

@router.message(UserUpdate.waiting_new_name)
async def p_change_name_save(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    if len(new_name) < 3:
        await message.answer("⚠️ Ism juda qisqa! Iltimos, kamida 3 ta harf kiriting.")
        return
        
    if await db.update_passenger_name(message.from_user.id, new_name):
        await message.answer(f"✅ Ismingiz muvaffaqiyatli o'zgartirildi: **{new_name}**", parse_mode="Markdown")
        await state.clear()
        # Profilni qayta ko'rsatish
        # We need a message object here, luckily we have it from the handler.
        # But wait, p_profile is above. 
        # Actually in p_change_name_save we have message: types.Message.
        # Let's make sure it's defined.
        await p_profile_msg(message)
    else:
        await message.answer("❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.")
        await state.clear()

@router.message(F.text == "⬅️ Ortga qaytish")
async def p_back(message: types.Message, state: FSMContext, bot: Bot):
    from .common import cmd_start
    await state.clear()
    await cmd_start(message, state, bot)

@router.callback_query(F.data.in_(["p_taxi", "p_delivery"]), StateFilter("*"))
async def p_start_order_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    # Check registration
    if not await db.get_passenger(callback.from_user.id):
        from bot.keyboards.inline import role_kb
        await callback.message.edit_text(
            "⚠️ <b>TO'XTANG!</b>\n\n"
            "Buyurtma berish uchun avval yo'lovchi sifatida ro'yxatdan o'tishingiz shart.\n"
            "Ism va telefon raqamingiz haydovchiga bog'lanish uchun zarur.",
            reply_markup=role_kb(),
            parse_mode="HTML"
        )
        return

    otype = "Taxi" if callback.data == "p_taxi" else "Delivery"
    await state.update_data(otype=otype)

    proceed_cb = f"proceed_{otype.lower()}"
    groups_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text="📂 JONLI TAXI — 10 ta guruh (1 bosishda)",
                url="https://t.me/addlist/7N6UCOxaihcwM2M6"
            )
        ],
        [
            types.InlineKeyboardButton(text="✅ Buyurtma berish", callback_data=proceed_cb),
        ],
        [
            types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role"),
        ],
    ])

    await callback.message.edit_text(
        "🎯 <b>JONLI TAXI GURUHLARIGA ULANIB OLING!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📂 Bitta tugma orqali barcha <b>10 ta</b> Jonli Taxi guruhiga qo'shiling! "
        "Haydovchilar bilan to'g'ridan-to'g'ri bog'laning.\n\n"
        "👇 <b>Guruhga qo'shilgach yoki to'g'ridan-to'g'ri buyurtma bering:</b>",
        reply_markup=groups_kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.in_(["proceed_taxi", "proceed_delivery"]), StateFilter("*"))
async def p_proceed_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    otype = data.get("otype", "Taxi")
    emoji = "🚕" if otype == "Taxi" else "📦"
    title = "Jo'nab ketish bo'limi" if otype == "Taxi" else "Jo'natma yuborish bo'limi"

    await callback.message.edit_text(
        f"📍 <b>{emoji} {title.upper()}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Qayerdan</b> yo'lga chiqasiz? Iltimos, viloyatingizni tanlang:\n\n"
        "<i>Namuna: Namangan, Markaziy dehqon bozori oldi</i> 🗺",
        reply_markup=locations_kb(), parse_mode="HTML"
    )
    await state.set_state(OrderProcess.choosing_from)
    await state.update_data(last_msg_id=callback.message.message_id)


@router.message(F.text.in_(["🚖 Jo'nab ketish", "📦 Jo'natma yuborish"]), StateFilter("*"))
async def p_start_order(message: types.Message, state: FSMContext):
    if not await db.get_passenger(message.from_user.id):
        from bot.keyboards.inline import role_kb
        await message.answer(
            "⚠️ <b>TO'XTANG!</b>\n\n"
            "Buyurtma berish uchun avval yo'lovchi sifatida ro'yxatdan o'tishingiz shart.\n"
            "Ism va telefon raqamingiz haydovchiga bog'lanish uchun zarur.",
            reply_markup=role_kb(),
            parse_mode="HTML"
        )
        return
    
    otype = "Taxi" if "Jo‘nab" in message.text else "Delivery"
    await state.update_data(otype=otype)
    
    msg = await message.answer(
        "📍 <b>JO'NAB KETISH MANZILI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Qayerdan</b> yo'lga chiqasiz? Iltimos, viloyatni tanlang:\n\n"
        "<i>Namuna: Andijon, Eskishahar bozori</i> 🗺", 
        reply_markup=locations_kb(), parse_mode="HTML"
    )
    await state.set_state(OrderProcess.choosing_from)
    await state.update_data(last_msg_id=msg.message_id)

# --- FLOW ---
@router.callback_query(F.data.startswith("loc_"), StateFilter("*"))
async def p_loc_from(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    loc = callback.data.split("_")[1]
    if loc == "custom":
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.edit_text(
            "✍️ <b>ANIQ MANZILNI KIRITING</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Iltimos, aniq boradigan manzilingizni (ko'cha, mo'ljal) batafsil yozib yuboring:\n\n"
            "📍 <i>Namuna: Toshkent, Chorsu bozori, 'GUM' savdo markazi oldi.</i>", 
            parse_mode="HTML"
        )
        await state.set_state(OrderProcess.entering_from_custom)
        return
        
    await state.update_data(floc=loc)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        "🏁 <b>BORISH MANZILI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Sizni qaysi manzilga sog'-salomat yetkazib qo'yamiz? <b>Qayerga?</b>\n\n"
        "<i>Namuna: Farg'ona, Viloyat shifoxonasi</i>", 
        reply_markup=destinations_kb(loc), parse_mode="HTML"
    )
    await state.set_state(OrderProcess.choosing_to)

@router.message(OrderProcess.entering_from_custom)
async def p_entering_from_custom(message: types.Message, state: FSMContext):
    await state.update_data(floc=message.text)
    data = await state.get_data()
    if data.get('last_msg_id'):
        try: await message.bot.delete_message(message.chat.id, data['last_msg_id'])
        except: pass

    msg = await message.answer(
        "🏁 <b>BORISH MANZILI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Sizni qaysi manzilga sog'-salomat yetkazib qo'yamiz? Manzilingizni tanlang:", 
        reply_markup=destinations_kb("custom"), parse_mode="HTML"
    )
    await state.set_state(OrderProcess.choosing_to)
    await state.update_data(last_msg_id=msg.message_id)

@router.callback_query(F.data.startswith("dest_"), StateFilter("*"))
async def p_loc_to(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    dest = callback.data.split("_")[1]
    if dest == "custom":
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.edit_text(
            "✍️ <b>ANIQ BORISH MANZILI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Iltimos, aniq <b>boradigan</b> manzilingizni (ko'cha, mo'ljal) batafsil yozib yuboring:\n\n"
            "🏁 <i>Namuna: Marg'ilon, 'Komsomol' ko'chasi, 24-uy.</i>", 
            parse_mode="HTML"
        )
        await state.set_state(OrderProcess.entering_to_custom)
        return

    await state.update_data(tloc=dest)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        "📅 <b>SAYOHAT VAQTI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Sizga qaysi vaqtda xizmat ko'rsatishimiz ma'qul? Iltimos, vaqtni belgilang: 🕒", 
        reply_markup=time_kb(), parse_mode="HTML"
    )
    await state.set_state(OrderProcess.choosing_time)

@router.callback_query(F.data == "back_to_to", StateFilter("*"))
@router.callback_query(F.data == "back_to_from", StateFilter("*"))
async def p_back_to_from(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(OrderProcess.choosing_from)
    await callback.message.edit_text(
        "📍 **JO'NAB KETISH BO'LIMI**\n\n"
        "Qayerdan yo'lga chiqasiz? Iltimos, viloyatni tanlang:",
        reply_markup=locations_kb(), parse_mode="Markdown"
    )

@router.callback_query(F.data == "back_to_dest", StateFilter("*"))
async def p_back_to_dest(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    loc = data.get('floc', 'custom')
    await state.set_state(OrderProcess.choosing_to)
    await callback.message.edit_text(
        "🏁 **BORISH MANZILI**\n\n"
        "Sizni qaysi manzilga sog'-salomat yetkazib qo'yamiz? Manzilingizni tanlang:", 
        reply_markup=destinations_kb(loc), parse_mode="Markdown"
    )

@router.message(OrderProcess.entering_to_custom)
async def p_entering_to_custom(message: types.Message, state: FSMContext):
    await state.update_data(tloc=message.text)
    await message.answer(
        "📅 **QULAY VAQT**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Sizga qaysi vaqtda xizmat ko'rsatishimiz ma'qul? Iltimos, vaqtni belgilang:", 
        reply_markup=time_kb(), parse_mode="Markdown"
    )
    await state.set_state(OrderProcess.choosing_time)

@router.callback_query(F.data.startswith("time_"), StateFilter("*"))
async def p_time(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    t = callback.data.split("_")[1]
    
    # Tugmani darhol o'chirish (faqat bir marta)
    try: await callback.message.edit_reply_markup(reply_markup=None)
    except: pass

    if t == "custom":
        await callback.message.edit_text(
            "🕒 <b>ANIC VAQTNI KIRITING</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Iltimos, sayohat vaqtini yozib yuboring:\n\n"
            "🕒 <i>Namuna: Bugun soat 14:30 da yoki Ertaga kechki payt 20:00 larda.</i>",
            parse_mode="HTML"
        )
        await state.set_state(OrderProcess.entering_time_custom)
        return

    await state.update_data(tval="Bugun" if t=="today" else "Ertaga" if t=="tomorrow" else "Keyin")
    
    # Raqam so'rash bosqichiga o'tish
    await p_ask_phone(callback.message, state, callback.from_user.id)

@router.message(OrderProcess.entering_time_custom)
async def p_entering_time_custom(message: types.Message, state: FSMContext):
    await state.update_data(tval=message.text.strip())
    # Raqam so'rash bosqichiga o'tish
    await p_ask_phone(message, state, message.from_user.id)

async def p_ask_phone(message: types.Message, state: FSMContext, user_id: int):
    # Bazadagi eski raqamni olish (taklif qilish uchun)
    u = await db.get_passenger(user_id)
    saved_phone = u.get('phone') if u else None
    
    from bot.keyboards.reply import phone_kb
    
    # Agar message CallbackQuery bo'lsa, uni oddiy message kabi ishlatolmaymiz,
    # shuning uchun message.answer yoki message.message.answer (agar u callback bo'lsa)
    # Biz p_time da callback.message ni uzatganmiz -> u Message obyekti.
    # p_entering_time_custom da message ni uzatganmiz -> u Message obyekti.
    # Demak message.answer ishlaydi.
    
    text = (
        "� <b>ALOQA UCHUN TELEFON RAQAM</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Haydovchi siz bilan bog'lanishi uchun ishlaydigan raqamingizni kiriting.\n\n"
        "👇 <b>Pastdagi tugmani bosing</b> yoki raqamni yozib yuboring:\n"
        "<i>(Masalan: +998901234567)</i>"
    )
    
    # Agar reply keyboard kerak bo'lsa, delete qilib yangisini yuborgan ma'qul
    # yoki shunchaki answer
    try: await message.delete() 
    except: pass
    
    await message.answer(text, reply_markup=phone_kb(), parse_mode="HTML")
    await state.set_state(OrderProcess.entering_phone)

@router.message(OrderProcess.entering_phone)
async def p_phone_handler(message: types.Message, state: FSMContext):
    from bot.handlers.registration import clean_phone
    
    if message.contact:
        phone = clean_phone(message.contact.phone_number)
    else:
        phone = clean_phone(message.text)
        if not re.match(r'^998[389][012345789]\d{7}$', phone):
            await message.answer(
                "❌ <b>Xatolik:</b> Noto'g'ri raqam formati!\n\n"
                "Iltimos, raqamni quyidagi ko'rinishda kiriting:\n"
                "<code>+998901234567</code> yoki pastdagi tugmani bosing.", 
                parse_mode="HTML"
            )
            return

    # SMS kod yuborish
    code = str(random.randint(100000, 999999))
    sent = await sms_client.send_sms(phone, f"JONLI TAXI: Buyurtma tasdiqlash kodi: {code}")
    
    if sent:
        await state.update_data(order_phone=phone, order_sms_code=code)
        await message.answer(
            f"📨 <b>TASDIQLASH KODI YUBORILDI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Raqam: <code>+{phone}</code>\n\n"
            f"Iltimos, SMS orqali kelgan <b>6 xonali kodni</b> kiriting:",
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode="HTML"
        )
        await state.set_state(OrderProcess.waiting_order_sms_code)
    else:
        # Agar SMS yuborilmasa (config yo'q yoki xato)
        from core.config import ESKIZ_EMAIL
        if not ESKIZ_EMAIL:
            # SMS API sozlanmagan bo'lsa, tekshiruvsiz davom etamiz
            await state.update_data(ph=phone)
            await message.answer(
                "✅ Raqam qabul qilindi! (SMS API sozlanmagan)",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await p_continue_to_location(message, state)
        else:
            await message.answer(
                "❌ SMS yuborishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring yoki admin bilan bog'laning.",
                parse_mode="HTML"
            )

@router.message(OrderProcess.waiting_order_sms_code)
async def p_verify_order_sms(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sent_code = data.get('order_sms_code')
    user_code = message.text.strip()
    
    if user_code != sent_code:
        await message.answer("❌ Noto'g'ri kod! Iltimos, qaytadan tekshirib kiriting:")
        return
    
    # Tasdiqlandi
    phone = data.get('order_phone')
    await state.update_data(ph=phone)
    await message.answer("✅ Telefon raqam tasdiqlandi!", parse_mode="HTML")
    
    # Lokatsiya bosqichiga o'tish
    await p_continue_to_location(message, state)

async def p_continue_to_location(message: types.Message, state: FSMContext):
    """Lokatsiya bosqichiga o'tish"""
    await message.answer(
        "📍 <b>LOKATSIYA (IXTIYORIY)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Haydovchi Sizni tezroq topishi uchun lokatsiyangizni yuborishingiz mumkin. "
        "Buning uchun pastdagi <b>📍 Lokatsiyamni yuborish</b> tugmasini bosing.\n\n"
        "Agar tushunmasangiz, o'tkazib yuboring:", 
        reply_markup=location_only_kb(), parse_mode="HTML" 
    )
    await message.answer(
        "⏩ <b>O'tkazib yuborish uchun:</b>",
        reply_markup=skip_location_kb(), parse_mode="HTML"
    )
    await state.set_state(OrderProcess.choosing_location)

@router.callback_query(F.data == "skip_location", StateFilter(OrderProcess.choosing_location))
async def p_skip_location_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(lat=None, lon=None)
    # Clear reply keyboard
    await callback.message.answer("✅ Lokatsiya o'tkazib yuborildi.", reply_markup=types.ReplyKeyboardRemove())
    await p_details_step(callback.message, state)

async def p_details_step(message: types.Message, state: FSMContext):
    data = await state.get_data()
    emoji = "🚕" if data.get("otype") == "Taxi" else "📦"
    
    text = (
        f"{emoji} <b>BUYURTMA UCHUN QO'SHIMCHA MA'LUMOT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Haydovchiga aytadigan qo'shimcha gaplaringiz bormi? \n\n"
        "📝 <b>Namuna:</b> <i>'2 ta sumkam bor', 'Konditsionerli moshina bo'lsin', 'Bolalar o'rindig'i kerak'</i>\n\n"
        "Siz izohni <b>matn</b> shaklida yozishingiz yoki <b>🎤 Ovozli xabar</b> yuborishingiz mumkin:"
    )
    
    msg = await message.answer(text, reply_markup=skip_kb("back_to_dest"), parse_mode="HTML")
    await state.set_state(OrderProcess.entering_details)
    await state.update_data(last_msg_id=msg.message_id)

@router.message(OrderProcess.choosing_location)
async def p_location(message: types.Message, state: FSMContext):
    if message.location:
        await state.update_data(lat=message.location.latitude, lon=message.location.longitude)
    else:
        await message.answer("Iltimos, lokatsiya yuboring yoki tepadan '⏩ O'tkazib yuborish' tugmasini bosing.")
        return

    await message.answer("✅ Manzil qabul qilindi.", reply_markup=types.ReplyKeyboardRemove())
    await p_details_step(message, state)

@router.callback_query(F.data == "order_voice", StateFilter("*"))
async def p_voice_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text("🎤 <b>Ovozli xabaringizni yuboring...</b>\n\n<i>(Masalan: 3 kishi, kiyimlar bor, soat 10 da...)</i>", parse_mode="HTML")
    await state.set_state(OrderProcess.waiting_voice)

@router.message(OrderProcess.waiting_voice, F.voice)
async def p_voice_handle(message: types.Message, state: FSMContext):
    await state.update_data(voice_id=message.voice.file_id, det="[Ovozli xabar]")
    await p_summary(message, state)

@router.callback_query(F.data == "skip_details", StateFilter("*"))
async def p_details_skip(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.update_data(det="Yo'q")
    await p_summary(callback.message, state)

@router.message(OrderProcess.entering_details)
async def p_details_msg(message: types.Message, state: FSMContext):
    details_text = message.text.strip()
    
    # URL va havolalarni aniqlash va bloklash
    url_pattern = r'(http[s]?://|www\.|t\.me/|@[a-zA-Z0-9_]+|\.com|\.uz|\.ru|\.org)'
    if re.search(url_pattern, details_text, re.IGNORECASE):
        await message.answer(
            "⚠️ <b>DIQQAT!</b>\n\n"
            "Buyurtma tafsilotida havola, username yoki web-sayt manzillari yuborish <b>QATI'YAN TAQIQLANGAN!</b>\n\n"
            "🚫 <b>Bunday harakatlar uchun siz botdan va guruhdan UMRBOD BLOKLANGAN bo'lasiz!</b>\n\n"
            "Iltimos, faqat buyurtma haqida zarur ma'lumotlarni yozing.\n"
            "<i>(Masalan: 3 kishi, katta sumkalar bor, konditsioner kerak)</i>",
            parse_mode="HTML"
        )
        return
    
    # Uzunlik cheklash
    if len(details_text) > 500:
        await message.answer("⚠️ Izoh juda uzun! Iltimos, qisqaroq yozing (maksimum 500 belgi).")
        return
    
    await state.update_data(det=details_text)
    await p_summary(message, state)

async def p_summary(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    emoji = "🚖" if data['otype'] == "Taxi" else "📦"
    loc_status = "✅ <b>Yuborildi</b>" if data.get('lat') else "❌ <b>Yuborilmadi</b>"
    
    # Foydalanuvchi ma'lumotlarini olish
    user = await db.get_passenger(msg.from_user.id)
    full_name = user['full_name'] if user else msg.from_user.full_name
    
    txt = (
        f"{emoji} <b>BUYURTMA TAFSILOTLARI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"� <b>Ism:</b> <code>{full_name}</code>\n"
        f"📞 <b>Telefon:</b> <code>{fmt_p(data['ph'])}</code>\n\n"
        f"📍 <b>Qayerdan:</b> <code>{data['floc']}</code>\n"
        f"📍 <b>Qayerga:</b> <code>{data['tloc']}</code>\n"
        f"⏰ <b>Vaqt:</b> <code>{data['tval']}</code>\n"
        f"🗺 <b>Lokatsiya:</b> {loc_status}\n"
        f"💬 <b>Izoh:</b> <i>{data['det']}</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <b>MUHIM OGOHLANTIRISH:</b>\n\n"
        "✅ Ma'lumotlaringiz to'g'riligini tekshiring!\n"
        "✅ Telefon raqamingiz ishlaydigan bo'lishi shart!\n"
        "🚫 <b>Yolg'on buyurtma berish QATI'YAN TAQIQLANGAN!</b>\n"
        "🚫 <b>Havola/reklama yuborish UMRBOD BLOKLASH!</b>\n\n"
        "Buyurtmani tasdiqlayman?"
    )
    await msg.answer(txt, reply_markup=confirm_order_kb(), parse_mode="HTML")
    await state.set_state(OrderProcess.confirming)

@router.callback_query(F.data == "confirm_order", StateFilter("*"))
async def p_confirm(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    # Loading holatini ko'rsatish
    await callback.message.edit_reply_markup(reply_markup=None)
    status_msg = await callback.message.answer("⏳ **Buyurtma rasmiylashtirilmoqda...**", parse_mode="Markdown")
    
    try:
        data = await state.get_data()
        
        # 1. Bazaga yozish
        oid = await db.create_order(
            callback.from_user.id, data.get('otype', 'Taxi'), data.get('floc'), data.get('tloc'), 0, 
            data.get('tval'), data.get('det'), data.get('ph'), data.get('lat'), data.get('lon'),
            data.get('voice_id')
        )
        
        if not oid:
            raise Exception("Bazaga yozishda xatolik!")

        # 2. Xabar matnini tayyorlash
        from html import escape
        phone_display = f"<code>+{data.get('ph')}</code>"
        d_text = data.get('det') if data.get('det') else "Ko'rsatilmagan"
        description = escape(d_text)
        floc = escape(str(data.get('floc')))
        tloc = escape(str(data.get('tloc')))
        tval = escape(str(data.get('tval')))
        fullname = escape(callback.from_user.full_name)
        
        txt = (
            f"🚕 <b>BUYURTMA #{oid}</b>\n\n"
            f"📍 <b>Qayerdan:</b> {floc}\n"
            f"📍 <b>Qayerga:</b> {tloc}\n"
            f"📅 <b>Vaqt:</b> {tval}\n"
            f"💬 <b>Izoh:</b> {description}\n\n"
            f"👤 <b>Yo'lovchi:</b> {fullname}\n"
            f"📞 <b>Tel:</b> {phone_display}\n\n"
            "⚠️ <b>ESLATMA:</b>\n"
            "❗️ Telefon raqam har doim ishchi holatda bo'lishi shart.\n"
            "❗️ Yolg'on chaqiruv yoki bekorchi buyurtmalar uchun javobgarlik mavjud.\n"
            "⛔️ <b>DIQQAT:</b> Reklama (havola) tarqatganlar va behayo xabar yuborganlar botdan va guruhdan umrbod bloklanadi!\n\n"
            "<i>(Raqam ustiga bossangiz nusxa oladi)</i>"
        )
        
        # 3. Guruhlarga yuborish
        vip_ids_str = await db.get_setting('vip_group_ids', str(VIP_GROUP_ID))
        vip_ids = [int(i.strip()) for i in vip_ids_str.split(",") if i.strip()]
        
        kb = accept_order_kb(oid, callback.from_user.id, data.get('ph'))
        
        sent_count = 0
        logger.info(f"Yuboriladigan guruhlar: {vip_ids}")
        for g_id in vip_ids:
            try:
                try:
                    sent_msg = await bot.send_message(g_id, txt, reply_markup=kb, parse_mode="HTML")
                except Exception as e:
                    if "BUTTON_USER_PRIVACY_RESTRICTED" in str(e):
                        # Agar foydalanuvchi profili yopiq bo'lsa, tugmasiz yuboramiz
                        logger.warning(f"User {callback.from_user.id} has privacy restricted. Sending without profile button.")
                        sent_msg = await bot.send_message(g_id, txt, reply_markup=None, parse_mode="HTML")
                    else:
                        raise e
                
                sent_count += 1
                logger.info(f"Guruhga ({g_id}) muvaffaqiyatli yuborildi.")
                
                if data.get('voice_id'):
                    try: await bot.send_voice(chat_id=g_id, voice=data['voice_id'], reply_to_message_id=sent_msg.message_id)
                    except Exception as ve: logger.error(f"Voice send error: {ve}")

                if data.get('lat') and data.get('lon'):
                    try: 
                        await bot.send_location(
                            chat_id=g_id, latitude=data['lat'], longitude=data['lon'], reply_to_message_id=sent_msg.message_id
                        )
                    except Exception as le: logger.error(f"Loc send error: {le}")
            except Exception as ge:
                logger.error(f"Guruhga ({g_id}) yuborishda xato: {ge}")
        
        if sent_count == 0:
            logger.warning("Buyurtma hech qaysi guruhga yuborilmadi! Guruh IDlarini tekshiring.")
        else:
            logger.info(f"Buyurtma {sent_count} ta guruhga yuborildi.")

        # 4. Muvaffaqiyatli yakunlash
        from bot.keyboards.inline import back_to_main_kb
        await status_msg.delete() # Loadingni o'chirish
        await callback.message.delete() # Eski xabarni o'chirish
        
        await callback.message.answer(
            "✅ <b>Buyurtmangiz muvaffaqiyatli qabul qilindi!</b> 🎉\n\n"
            "Haydovchilarimiz tez orada Siz bilan bog'lanishadi. Iltimos, qo'ng'iroqqa tayyor turing! 📞\n\n"
            "🌟 <b>Bizning xizmatimizdan foydalanganingiz uchun tashakkur!</b>",
            reply_markup=back_to_main_kb(),
            parse_mode="HTML"
        )
        await state.clear()
        
    except Exception as e:
        logger.exception(f"Order error: {e}")
        await status_msg.edit_text(f"❌ **Xatolik yuz berdi:**\n{e}\n\nIltimos admin bilan bog'laning.")


