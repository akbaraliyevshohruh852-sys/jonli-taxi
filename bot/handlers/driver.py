from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from core import database as db
from bot.keyboards.inline import back_to_main_kb
from bot.states.states import UserUpdate, DriverRefill
from bot.utils.filters import IsDriver
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = Router()

# --- PROFIL (INLINE TUGMA ORQALI) ---
@router.callback_query(F.data == "d_profile", IsDriver())
async def d_profile(callback: types.CallbackQuery):
    dr = await db.get_driver(callback.from_user.id)
    if not dr:
        await callback.answer("❌ Siz haydovchi emassiz!", show_alert=True)
        return

    # Status bo'yicha maxsus xabar
    status = dr.get('status', 'pending')
    if status == 'pending':
        await callback.answer("⏳ Arizangiz ko'rib chiqilmoqda!", show_alert=True)
        await callback.message.edit_text(
            "⏳ <b>ARIZA KO'RIB CHIQILMOQDA</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 <b>Ism:</b> {dr['full_name']}\n"
            f"📞 <b>Tel:</b> <code>+{dr['phone']}</code>\n"
            f"🚗 <b>Mashina:</b> {dr['car_type']}\n\n"
            "🕐 Adminlar arizangizni tez orada ko'rib chiqadi.\n"
            "<i>Tasdiqlangach, botdan to'liq foydalanishingiz mumkin bo'ladi.</i>",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role")]
            ]),
            parse_mode="HTML"
        )
        return

    if status == 'rejected':
        await callback.answer("❌ Arizangiz rad etilgan!", show_alert=True)
        await callback.message.edit_text(
            "❌ <b>ARIZA RAD ETILGAN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Arizangiz admin tomonidan rad etildi.\n"
            "Yangi ariza yuborishingiz mumkin.\n\n"
            "<i>Muammo bo'lsa admin bilan bog'laning.</i>",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔄 Qayta ariza yuborish", callback_data="role_driver")],
                [types.InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_role")]
            ]),
            parse_mode="HTML"
        )
        return

    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{dr['telegram_id']}"
    
    j_at = dr['joined_at']
    if isinstance(j_at, str):
        try:
            j_at = datetime.strptime(j_at, "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y')
        except:
            j_at = str(j_at)
    else:
        j_at = j_at.strftime('%d.%m.%Y')
    
    s_end = "Faol emas"
    if dr['subscription_end']:
        sub_end = dr['subscription_end']
        if isinstance(sub_end, str):
            try:
                sub_end = datetime.strptime(sub_end, "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y')
            except:
                sub_end = str(sub_end)
        else:
            sub_end = sub_end.strftime('%d.%m.%Y')
        s_end = sub_end
    
    from core.config import ADMIN_CONTACT
    contact_url = f"tg://user?id={ADMIN_CONTACT}" if ADMIN_CONTACT.isdigit() else f"https://t.me/{ADMIN_CONTACT.replace('@', '')}"
    
    text = (
        "👤 <b>HAYDOVCHI SHAXSIY KABINETI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ <b>Ism:</b> {dr['full_name']}\n"
        f"📞 <b>Tel:</b> <code>+{dr['phone']}</code>\n"
        f"🚗 <b>Mashina:</b> {dr['car_type']}\n"
        f"📝 <b>Ro'yxatdan o'tgan:</b> {j_at}\n"
        f"📅 <b>Obuna tugash sanasi:</b> <code>{s_end}</code>\n"
        f"⭐️ <b>Reyting:</b> {dr.get('rating', 5.0)}\n"
        f"💰 <b>Balans:</b> <code>{dr['balance']}</code> so'm\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 <b>REFERAL TIZIMI</b>\n"
        f"Siz taklif qilganlar: <b>{dr.get('invite_count', 0)}</b> ta\n"
        f"<i>Yana {max(0, 20 - dr.get('invite_count', 0))} ta azo qo'shilsa, 1 oy bepul VIP beriladi!</i>\n\n"
        f"🔗 <b>Sizning havolangiz:</b>\n<code>{ref_link}</code>"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗂 Qabul qilgan buyurtmalarim", callback_data="driver_orders")],
        [types.InlineKeyboardButton(text="✏️ Ismni o'zgartirish", callback_data="change_name_driver")],
        [types.InlineKeyboardButton(text="💰 Balansni to'ldirish", callback_data="d_refill")],
        [types.InlineKeyboardButton(text="👨‍💻 Admin bilan aloqa", url=contact_url)]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

# --- BALANSNI TO'LDIRISH ---
@router.callback_query(F.data == "d_refill", IsDriver())
async def d_refill(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "💰 <b>BALANSNI TO'LDIRISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Hisobingizni qancha summaga to'ldirmoqchisiz?\n"
        "⬇️ <b>Summani yozib yuboring:</b>\n\n"
        "<i>Namuna: 2000</i>", 
        parse_mode="HTML",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(DriverRefill.waiting_amount)

@router.message(DriverRefill.waiting_amount, IsDriver())
async def d_refill_amount(message: types.Message, state: FSMContext):
    amount_str = message.text.strip().replace(" ", "")
    if not amount_str.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqam kiriting (masalan: 50000).")
        return
    
    amount = int(amount_str)
    if amount < 1000:
        await message.answer("⚠️ Minimal to'lov miqdori: 1 000 so'm.")
        return
        
    await state.update_data(refill_amount=amount)
    
    card = await db.get_setting('payment_card', '9860 3501 4062 9212')
    owner = await db.get_setting('payment_card_owner', 'Usmonov Samandar')
    
    text = (
        "💳 <b>TO'LOV MA'LUMOTLARI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💸 <b>To'lov summasi:</b> {amount:,} so'm\n\n"
        f"💳 <b>Karta raqam:</b> <code>{card}</code>\n"
        f"👤 <b>Karta egasi:</b> {owner}\n\n"
        "📸 <b>DIQQAT!</b>\n"
        "To'lovni kiritilgan karta raqamiga o'tkazing va <b>CHEK RASMINI</b> shu yerga yuboring.\n"
        "<i>Rasmda sana, vaqt va summa aniq ko'rinishi shart!</i>"
    )
    
    await message.answer(text, parse_mode="HTML", reply_markup=back_to_main_kb())
    await state.set_state(DriverRefill.waiting_receipt)

@router.message(DriverRefill.waiting_receipt, F.photo, IsDriver())
async def d_refill_receipt(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = data.get('refill_amount', 0)
    photo_id = message.photo[-1].file_id
    
    # Bazaga yozish
    pid = await db.add_payment(message.from_user.id, amount, photo_id)
    
    await message.answer(
        "✅ <b>QABUL QILINDI!</b>\n\n"
        "To'lov cheki adminlarga yuborildi. Tez orada balansingiz tasdiqlanadi.\n"
        "Sizga xabar beramiz! 🔔",
        parse_mode="HTML",
        reply_markup=back_to_main_kb()
    )
    await state.clear()
    
    # Adminlarga xabar
    from core.config import ADMIN_IDS
    from bot.keyboards.inline import admin_payment_kb
    
    alert_text = (
        f"💰 <b>YANGI TO'LOV #{pid}</b>\n"
        f"👤 Haydovchi: {message.from_user.full_name}\n"
        f"💵 Summa: {amount:,} so'm"
    )
    
    for aid in ADMIN_IDS:
        try:
            await bot.send_photo(
                aid, 
                photo=photo_id, 
                caption=alert_text, 
                reply_markup=admin_payment_kb(pid, message.from_user.id),
                parse_mode="HTML"
            )
        except: pass

# --- ISMNI O'ZGARTIRISH ---
@router.callback_query(F.data == "change_name_driver", IsDriver())
async def d_change_name_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("📝 **Yangi ismingizni kiriting:**", parse_mode="Markdown")
    await state.set_state(UserUpdate.waiting_new_name)

@router.message(UserUpdate.waiting_new_name, IsDriver())
async def d_change_name_save(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    if len(new_name) < 3:
        await message.answer("⚠️ Ism juda qisqa! Iltimos, kamida 3 ta harf kiriting.")
        return
        
    if await db.update_driver_name(message.from_user.id, new_name):
        await message.answer(f"✅ Ismingiz muvaffaqiyatli o'zgartirildi: **{new_name}**", parse_mode="Markdown")
        await state.clear()
        await d_profile_from_message(message)
    else:
        await message.answer("❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.")
        await state.clear()

# Yordamchi funksiya: profilni xabar orqali ko'rsatish
async def d_profile_from_message(message: types.Message):
    dr = await db.get_driver(message.from_user.id)
    if not dr: return
    
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{dr['telegram_id']}"
    
    j_at = dr['joined_at']
    if isinstance(j_at, str):
        try:
            j_at = datetime.strptime(j_at, "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y')
        except:
            j_at = str(j_at)
    else:
        j_at = j_at.strftime('%d.%m.%Y')
    
    s_end = "Faol emas"
    if dr['subscription_end']:
        sub_end = dr['subscription_end']
        if isinstance(sub_end, str):
            try:
                sub_end = datetime.strptime(sub_end, "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y')
            except:
                sub_end = str(sub_end)
        else:
            sub_end = sub_end.strftime('%d.%m.%Y')
        s_end = sub_end
    
    from core.config import ADMIN_CONTACT
    contact_url = f"tg://user?id={ADMIN_CONTACT}" if ADMIN_CONTACT.isdigit() else f"https://t.me/{ADMIN_CONTACT.replace('@', '')}"
    
    text = (
        "👤 <b>HAYDOVCHI SHAXSIY KABINETI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ <b>Ism:</b> {dr['full_name']}\n"
        f"📞 <b>Tel:</b> <code>+{dr['phone']}</code>\n"
        f"🚗 <b>Mashina:</b> {dr['car_type']}\n"
        f"📝 <b>Ro'yxatdan o'tgan:</b> {j_at}\n"
        f"📅 <b>Obuna tugash sanasi:</b> <code>{s_end}</code>\n"
        f"⭐️ <b>Reyting:</b> {dr.get('rating', 5.0)}\n"
        f"💰 <b>Balans:</b> <code>{dr['balance']}</code> so'm\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🎁 <b>REFERAL TIZIMI</b>\n"
        f"Siz taklif qilganlar: <b>{dr.get('invite_count', 0)}</b> ta\n"
        f"<i>Yana {max(0, 20 - dr.get('invite_count', 0))} ta azo qo'shilsa, 1 oy bepul VIP beriladi!</i>\n\n"
        f"🔗 <b>Sizning havolangiz:</b>\n<code>{ref_link}</code>"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗂 Qabul qilgan buyurtmalarim", callback_data="driver_orders")],
        [types.InlineKeyboardButton(text="✏️ Ismni o'zgartirish", callback_data="change_name_driver")],
        [types.InlineKeyboardButton(text="💰 Balansni to'ldirish", callback_data="d_refill")],
        [types.InlineKeyboardButton(text="👨‍💻 Admin bilan aloqa", url=contact_url)]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# --- BUYURTMALAR RO'YXATI ---
@router.callback_query(F.data == "driver_orders", IsDriver())
async def d_orders_list(callback: types.CallbackQuery):
    orders = await db.get_driver_orders(callback.from_user.id)
    if not orders:
        await callback.answer("Sizda hali qabul qilingan buyurtmalar yo'q.", show_alert=True)
        return
    
    text = "🗂 <b>OXIRGI QABUL QILINGAN BUYURTMALAR</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, o in enumerate(orders, 1):
        dt = o['created_at']
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").strftime('%d.%m %H:%M')
            except:
                dt = str(dt)
        else:
            dt = dt.strftime('%d.%m %H:%M')
        text += f"{i}. <b>{o['from_loc']} ➡️ {o['to_loc']}</b>\n"
        text += f"📅 {dt} | 📞 +{o['phone']}\n\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Profilga qaytish", callback_data="back_to_profile_driver")]
    ]))

@router.callback_query(F.data == "back_to_profile_driver", IsDriver())
async def d_back_profile(callback: types.CallbackQuery):
    await callback.message.delete()
    await d_profile(callback.message)

# --- ORTGA (ASOSIY MENYUGA) ---
@router.callback_query(F.data == "back_to_role", IsDriver())
async def d_back_to_role(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    from bot.handlers.common import cmd_start
    await callback.message.delete()
    await cmd_start(callback.message, state, bot)

# --- BUYURTMA QABUL QILISH ---
@router.callback_query(F.data.startswith("accept_"))
async def d_accept(callback: types.CallbackQuery, bot: Bot):
    oid = int(callback.data.split("_")[1])
    dr = await db.get_driver(callback.from_user.id)
    
    if not dr or dr['status'] != 'active':
        await callback.answer("⚠️ Faol emassiz!", show_alert=True)
        return

    order = await db.get_order(oid)
    if not order or order['status'] != 'pending':
        await callback.answer("❌ Olingan yoki bekor!", show_alert=True)
        return

    if await db.update_order_driver(oid, dr['telegram_id']):
        await callback.answer("✅ Muvaffaqiyatli qabul qilindi!")
        
        # Yo'lovchiga xabar
        try:
            p_txt = (
                "🚕 <b>HAYDOVCHI TOPILDI!</b> ✨\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 <b>Haydovchi:</b> {dr['full_name']}\n"
                f"📞 <b>Telefon:</b> <code>+{dr['phone']}</code>\n"
                f"🚘 <b>Mashina:</b> {dr['car_type']}\n\n"
                "🌟 <b>Oq yo'l!</b> Haydovchi hozir Siz bilan bog'lanadi."
            )
            await bot.send_message(order['user_id'], p_txt, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to notify passenger: {e}")

        # Adminlarga xabar
        from core.config import ADMIN_IDS
        for aid in ADMIN_IDS:
            try:
                p_phone = order['phone'].replace('+', '')
                d_phone = dr['phone'].replace('+', '')
                
                a_txt = (
                    "👨‍✈️ <b>ADMIN: BUYURTMA QABUL QILINDI</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📦 <b>Buyurtma ID:</b> #{oid}\n"
                    f"🚕 <b>Haydovchi:</b> {dr['full_name']} (+{d_phone})\n"
                    f"👤 <b>Yo'lovchi ID:</b> <code>{order['user_id']}</code> (+{p_phone})\n"
                    f"📍 <b>Yo'nalish:</b> {order['from_loc']} ➡️ {order['to_loc']}"
                )
                
                mon_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="🚕 Haydovchi profili", callback_data=f"mon_dr_{dr['telegram_id']}"),
                        types.InlineKeyboardButton(text="👤 Yo'lovchi profili", callback_data=f"mon_pa_{order['user_id']}")
                    ]
                ])
                
                await bot.send_message(aid, a_txt, parse_mode="HTML", reply_markup=mon_kb)
            except: pass
        
        # Haydovchiga kontakt yuborish
        try:
            await bot.send_contact(
                chat_id=dr['telegram_id'],
                phone_number=f"+{order['phone']}",
                first_name="Mijoz"
            )
        except: pass

        # Haydovchiga xabar
        kb = [[types.InlineKeyboardButton(text="👤 Mijoz profili", url=f"tg://user?id={order['user_id']}")]]
        if order.get('lat') and order.get('lon'):
            kb.append([types.InlineKeyboardButton(text="🗺 Xaritada ko'rish", url=f"https://www.google.com/maps?q={order['lat']},{order['lon']}")])
            
        dr_txt = (
            "✅ <b>MUVAFFAQIYATLI QABUL QILINDI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 <b>Yo'nalish:</b> {order['from_loc']} → {order['to_loc']}\n"
            f"👤 <b>Mijoz:</b> <code>{order['user_id']}</code>\n"
            f"📞 <b>Mijoz tel:</b> <code>+{order['phone']}</code>\n\n"
            "Iltimos, mijoz bilan darhol bog'laning!"
        )
        await bot.send_message(dr['telegram_id'], dr_txt, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

        # Guruhdagi xabarni yangilash
        from html import escape
        passenger = await db.get_passenger(order['user_id'])
        p_name = escape(passenger['full_name'] or "Noma'lum") if passenger else str(order['user_id'])
        dr_name = escape(dr['full_name'])
        floc = escape(order['from_loc'])
        tloc = escape(order['to_loc'])
        
        group_text = (
            "✅ <b>MUVAFFAQIYATLI QABUL QILINDI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 <b>Yo'nalish:</b> {floc} → {tloc}\n"
            f"👤 <b>Mijoz:</b> {p_name}\n"
            f"📞 <b>Mijoz tel:</b> +{order['phone']}\n\n"
            f"🚘 <b>Qabul qildi:</b> {dr_name}\n"
            f"📞 <b>Haydovchi tel:</b> +{dr['phone']}"
        )
        
        try:
            await callback.message.edit_text(group_text, parse_mode="HTML", reply_markup=None)
        except Exception as e:
            logger.error(f"Failed to edit group message: {e}")
