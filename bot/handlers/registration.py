from aiogram import Router, types, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from bot.states.states import Registration
from bot.keyboards.inline import (
    car_types_kb, check_sub_kb,
    passenger_main_kb, driver_main_kb,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from bot.keyboards.reply import phone_kb, main_menu_passenger, main_menu_driver
from core import database as db
from core.config import (
    ADMIN_IDS, DRIVER_GROUP_ID, ADMIN_CONTACT,
    PAYMENT_CARD, PAYMENT_CARD_OWNER, PAYMENT_AMOUNT, PUBLIC_GROUP_URL,
    ESKIZ_EMAIL
)
from bot.utils.checks import check_user_sub
import re
import logging
import random
from core.sms import sms_client

logger = logging.getLogger(__name__)
router = Router()


def clean_phone(p):
    return re.sub(r'[^0-9]', '', str(p))


# ── YO'LOVCHI RO'YXATDAN O'TISH ──────────────────────────────────────────────
@router.callback_query(F.data == "role_passenger", StateFilter("*"))
async def reg_p_start(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    uid = callback.from_user.id

    if await db.is_blacklisted(uid):
        await callback.answer("🚫 Siz bloklangansiz!", show_alert=True)
        return

    if not await check_user_sub(bot, uid):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "⚠️ <b>AVVAL GURUHGA OBUA BO'LING!</b>",
            reply_markup=check_sub_kb(PUBLIC_GROUP_URL),
            parse_mode="HTML"
        )
        return

    p = await db.get_passenger(uid)
    if p:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "🙋‍♂️ <b>YO'LOVCHI BO'LIMI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Xizmat turini tanlang:",
            reply_markup=passenger_main_kb(),
            parse_mode="HTML"
        )
        return

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        "📝 <b>RO'YXATDAN O'TISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Haydovchi sizga murojaat qilishi uchun <b>Ismingizni</b> yozing:",
        parse_mode="HTML"
    )
    await state.set_state(Registration.passenger_name)


@router.message(Registration.passenger_name)
async def reg_p_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()

    await state.update_data(name=full_name)

    await message.answer(
        "📞 <b>TELEFON RAQAM</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Iltimos, pastdagi <b>'📞 Raqamni yuborish'</b> tugmasini bosing:",
        reply_markup=phone_kb(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.passenger_phone)


@router.message(Registration.passenger_phone)
async def reg_p_phone(message: types.Message, state: FSMContext):
    if not message.contact:
        await message.answer(
            "⚠️ Faqat '📞 Raqamni yuborish' tugmasi orqali raqam yuboring!",
            reply_markup=phone_kb()
        )
        return

    phone = clean_phone(message.contact.phone_number)
    if not re.match(r'^998[389][012345789]\d{7}$', phone):
        await message.answer(
            "❌ Noto'g'ri O'zbekiston raqami formatida.\n"
            "Iltimos, to'g'ri raqam yuboring.",
            reply_markup=phone_kb()
        )
        return

    await state.update_data(phone=phone)
    data = await state.get_data()

    success = await db.register_passenger(
        message.from_user.id,
        data['name'],
        phone
    )

    if success:
        await message.answer(
            f"✅ <b>MUVAFFAQIYATLI RO'YXATDAN O'TDINGIZ!</b>\n"
            f"Xush kelibsiz, <b>{data['name']}</b>!",
            reply_markup=passenger_main_kb(),
            parse_mode="HTML"
        )
        await state.clear()
    else:
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


# ── HAYDOVCHI RO'YXATDAN O'TISH ──────────────────────────────────────────────
@router.callback_query(F.data == "role_driver", StateFilter("*"))
async def reg_d_intro(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    uid = callback.from_user.id

    if await db.is_blacklisted(uid):
        await callback.answer("🚫 Siz bloklangansiz!", show_alert=True)
        return

    if not await check_user_sub(bot, uid):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "⚠️ <b>AVVAL GURUHGA OBUNA BO'LING!</b>",
            reply_markup=check_sub_kb(PUBLIC_GROUP_URL),
            parse_mode="HTML"
        )
        return

    dr = await db.get_driver(uid)
    if dr:
        if dr['status'] == 'active':
            await callback.message.delete()
            await callback.message.answer(
                "🚕 <b>HAYDOVCHI KABINETI</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👋 Xush kelibsiz, <b>{dr['full_name']}</b>!\n\n"
                "👇 <b>Profilingizni ko'rish yoki sozlamalar:</b>",
                reply_markup=driver_main_kb(),
                parse_mode="HTML"
            )
            return

        elif dr['status'] == 'rejected':
            await callback.message.edit_text(
                "❌ **Oldingi arizangiz rad etilgan.**\n\n"
                "Ma'lumotlaringizni to'g'rilab, yangi ariza yuborishingiz mumkin!\n"
                "Quyidagi tugmani bosing va jarayonni boshlang:",
                reply_markup=None,
                parse_mode="HTML"
            )
            await callback.message.answer(
                "Yangi ariza yuborish:",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🚀 Yangi ariza boshlash", callback_data="d_reg_name")]
                ])
            )
            return

        elif dr['status'] == 'pending':
            await callback.message.edit_text(
                "⏳ **Arizangiz hali ko'rib chiqilmoqda.**\n"
                "Iltimos, admin tasdiqlashini kuting.\n\n"
                "<i>Agar rad etilgan bo'lsa, admin bilan bog'laning yoki qayta ma'lumotlaringizni tekshiring.</i>",
                parse_mode="HTML"
            )
            return

    # Yangi ariza boshlash (hech qanday ariza yo'q bo'lsa)
    p_amount = await db.get_setting('driver_subscription_fee', PAYMENT_AMOUNT)
    text = (
        "🏎 <b>HAYDOVCHILAR JAMOASIGA QO'SHILISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Assalomu alaykum, qadrli hamkasb!</b> 🤝\n\n"
        "🏁 <b>Ro'yxatdan o'tish bosqichlari:</b>\n"
        "1️⃣ Shaxsiy ma'lumotlarni kiritish\n"
        "2️⃣ Xizmat haqini to'lash (obuna)\n"
        "3️⃣ To'lov chekini tasdiqlash uchun yuborish\n\n"
        f"💰 <b>Oylik to'lov:</b> <code>{p_amount}</code> so'm"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚀 Davom etish", callback_data="d_reg_name")],
        [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role")]
    ])

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "d_reg_name")
async def reg_d_name_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        "🚗 <b>HAYDOVCHI: RO'YXATDAN O'TISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Ism va Familiyangizni yozing:</b>",
        parse_mode="HTML"
    )
    await state.set_state(Registration.driver_name)


@router.message(Registration.driver_name)
async def reg_d_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()

    await state.update_data(name=full_name)
    await message.answer(
        "🚗 **MASHINANGIZ TURINI TANLANG:**",
        reply_markup=car_types_kb(),
        parse_mode="Markdown"
    )
    await state.set_state(Registration.driver_car_type)


@router.callback_query(Registration.driver_car_type, F.data.startswith("car_"))
async def reg_d_car(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    car = callback.data.split("_")[1]

    if car == "custom":
        await callback.message.answer(
            "<b>MASHINA RUSUMINI YOZING:</b>\n<i>(Masalan: Chevrolet Gentra)</i>",
            parse_mode="HTML"
        )
        await state.set_state(Registration.driver_car_type)
        return

    await state.update_data(car=car)
    await callback.message.answer(
        "📱 **Iltimos, telefon raqamingizni quyidagi tugma orqali yuboring:**",
        reply_markup=phone_kb()
    )
    await state.set_state(Registration.driver_phone)


@router.message(Registration.driver_car_type)
async def reg_d_car_custom(message: types.Message, state: FSMContext):
    car_name = message.text.strip()

    await state.update_data(car=car_name)
    await message.answer(
        "📱 **Iltimos, telefon raqamingizni quyidagi tugma orqali yuboring:**",
        reply_markup=phone_kb()
    )
    await state.set_state(Registration.driver_phone)


@router.message(Registration.driver_phone)
async def reg_d_phone_only_contact(message: types.Message, state: FSMContext):
    if not message.contact:
        await message.answer(
            "⚠️ Faqat '📞 Raqamni yuborish' tugmasi orqali raqam yuboring!",
            reply_markup=phone_kb()
        )
        return

    phone = clean_phone(message.contact.phone_number)
    if not re.match(r'^998[389][012345789]\d{7}$', phone):
        await message.answer(
            "❌ Noto'g'ri O'zbekiston raqami.\nIltimos, to'g'ri raqam yuboring.",
            reply_markup=phone_kb()
        )
        return

    # SMS tasdiqlash (agar faol bo'lsa)
    if ESKIZ_EMAIL:
        code = str(random.randint(100000, 999999))
        sent = await sms_client.send_sms(phone, f"JONLI TAXI: Tasdiqlash kodi: {code}")

        if sent:
            await state.update_data(phone=phone, sms_code=code, reg_type="driver")
            await message.answer(
                f"📨 **TASDIQLASH KODI YUBORILDI**\n"
                f"Raqam: +{phone}\n"
                f"Iltimos, kodni kiriting:",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown"
            )
            await state.set_state(Registration.waiting_sms_code)
            return

    # SMS bo'lmasa yoki ishlamasa — to'g'ridan to'lov ma'lumotlarini so'rash
    await state.update_data(phone=phone, lic="Suralmadi") # Guvohnoma maydonini to'ldirib ketamiz
    await message.answer(
        "✅ Telefon raqamingiz qabul qilindi!",
        reply_markup=types.ReplyKeyboardRemove()
    )

    p_amount = await db.get_setting('driver_subscription_fee', PAYMENT_AMOUNT)
    p_card = await db.get_setting('payment_card', PAYMENT_CARD)
    p_owner = await db.get_setting('payment_card_owner', PAYMENT_CARD_OWNER)

    text = (
        "💳 **TO'LOV MA'LUMOTLARI**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 **To'lov miqdori:** <code>{p_amount}</code> so'm\n"
        f"💳 **Karta:** <code>{p_card}</code>\n"
        f"👤 **Egasi:** <b>{p_owner}</b>\n\n"
        "📸 Endi to'lov chekini (rasmini) yuboring:\n"
        "<i>(To'liq ko'rinishi, sana/vaqt va summa bo'lishi shart)</i>"
    )
    await message.answer(text, parse_mode="HTML")
    await state.set_state(Registration.waiting_receipt)


@router.message(Registration.waiting_receipt, F.photo)
async def reg_d_final(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = int(data.get('pay_amount', PAYMENT_AMOUNT))
    # Driver save to DB
    await db.register_driver(
        message.from_user.id,
        data['name'],
        data['phone'],
        data['car'],
        data['lic']
    )

    pid = await db.add_payment(
        message.from_user.id,
        amount,
        message.photo[-1].file_id
    )

    # Haydovchiga xabar
    await message.answer(
        "📩 **Arizangiz qabul qilindi!**\n"
        "Adminlar tez orada tekshirib, sizni faollashtirishadi.\n\n"
        "Iltimos, kuting!",
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )

    # Adminlarga bildirishnoma + tasdiqlash/rad etish tugmalari
    for aid in ADMIN_IDS:
        try:
            txt = (
                f"🆕 **Yangi haydovchi arizasi**\n"
                f"👤 Ism: {data['name']}\n"
                f"📞 Tel: +{data['phone']}\n"
                f"🚗 Mashina: {data['car']}\n"
                f"💰 To'lov: {amount:,} so'm"
            )

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Tasdiqlash",
                        callback_data=f"pay_approve_{pid}_{message.from_user.id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Rad etish",
                        callback_data=f"pay_reject_{pid}_{message.from_user.id}"
                    )
                ]
            ])

            await bot.send_photo(
                aid,
                photo=message.photo[-1].file_id,
                caption=txt,
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Admin {aid} ga ariza yuborishda xato: {e}")

    await state.clear()
