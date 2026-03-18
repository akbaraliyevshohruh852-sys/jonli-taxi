from aiogram import Router, types, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio
import logging
import os
from datetime import datetime, timedelta

from core import database as db
from core.config import (
    DRIVER_GROUP_ID, VIP_GROUP_ID, ADMIN_IDS, GRABBER_SOURCES, DB_PATH
)
from bot.keyboards.inline import (
    admin_panel_kb, admin_back_kb, admin_driver_manage_kb,
    admin_order_manage_kb, admin_avto_xabar_kb,
    admin_avto_pay_manage_kb, admin_drivers_menu_kb, admin_payments_menu_kb,
    admin_users_kb
)
from bot.states.states import AdminState
from bot.utils.filters import IsAdmin

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("admin"), IsAdmin())
async def admin_main(message: types.Message, state: FSMContext):
    await state.clear()
    now = datetime.now().strftime("%H:%M:%S | %d.%m.%Y")
    text = (
        "👑 **ADMINSTRATOR BOSHQARUV MARKAZI**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🕑 **Tizim vaqti:** `{now}`\n"
        "🤖 **Bot holati:** High Performance ⚡️\n\n"
        "Kerakli boshqaruv bo'limini tanlang:"
    )
    await message.answer(text, reply_markup=admin_panel_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin_main_menu", IsAdmin())
async def admin_main_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    now = datetime.now().strftime("%H:%M:%S")
    text = (
        "👑 **ADMINSTRATOR BOSHQARUV MARKAZI**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🕑 **Tizim vaqti:** `{now}`\n"
        "🤖 **Bot holati:** High Performance ⚡️\n\n"
        "Kerakli boshqaruv bo'limini tanlang:"
    )
    try:
        await callback.message.edit_text(text, reply_markup=admin_panel_kb(), parse_mode="HTML")
    except:
        await callback.message.answer(text, reply_markup=admin_panel_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_stats", IsAdmin())
async def admin_stats_callback(callback: types.CallbackQuery):
    stats = await db.get_stats()
    bl = await db.get_blacklist()
    bl_count = len(bl) if bl else 0

    total_users = stats['total_drivers'] + stats['total_passengers']
    active_percent = (stats['active_drivers'] / stats['total_drivers'] * 100) if stats['total_drivers'] > 0 else 0

    text = (
        "📊 **MUKAMMAL ANALITIKA & DASHBOARD**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👥 **FOYDALANUVCHILAR:**\n"
        f"├ Jami baza: `{total_users:,}` ta\n"
        f"├ Haydovchilar: `{stats['total_drivers']:,}` (`{active_percent:.1f}%` faol)\n"
        f"└ Yo'lovchilar: `{stats['total_passengers']:,}` ta\n\n"
        "📈 **OSISh DINAMIKASI (BUGUN):**\n"
        f"├ Yangi qo'shilganlar: `+{stats['new_drivers_today'] + stats['new_passengers_today']:,}`\n"
        f"├ Yangi haydovchilar: `+{stats['new_drivers_today']:,}`\n"
        f"└ Amalga oshirilgan buyurtmalar: `{stats['today_orders']:,}` ta\n\n"
        "💰 **MOLIYAVIY KO'RSATKICHLAR:**\n"
        f"├ Bugungi tushum: `{stats['today_revenue']:,} so'm`\n"
        f"├ Shu oylik: `{stats['month_revenue']:,} so'm`\n"
        f"└ **Jami sof foyda:** `{stats['total_revenue']:,} so'm`\n\n"
        "🛡 **XAVFSIZLIK:**\n"
        f"└ Qora ro'yxatdagilar: `{bl_count}` kishi\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


# ==========================================
# 3. HAYDOVCHILAR MARKAZI
# ==========================================
@router.callback_query(F.data == "admin_drivers_menu", IsAdmin())
async def admin_drivers_menu_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🚗 **HAYDOVCHILARNI BOSHQARISH MARKAZI**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Kerakli toifa bo'yicha haydovchilarni boshqaring. Sizda ular ustidan to'liq nazorat bor.",
        reply_markup=admin_drivers_menu_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.in_(["show_active_drivers", "show_pending_drivers", "show_rejected_drivers", "show_vip_drivers"]), IsAdmin())
async def show_drivers_by_status_handler(callback: types.CallbackQuery):
    action = callback.data
    status_map = {
        "show_active_drivers": "active",
        "show_pending_drivers": "pending",
        "show_rejected_drivers": "rejected",
        "show_vip_drivers": "vip"
    }

    status = status_map.get(action)
    if not status:
        return

    if status == 'vip':
        drivers = await db.get_users_by_role('driver', is_vip=True)
        title = "💎 VIP HAYDOVCHILAR"
    else:
        drivers = await db.get_drivers_by_status(status)
        title = f"{'🟢' if status == 'active' else '⏳' if status == 'pending' else '🔴'} {status.upper()} HAYDOVCHILAR"

    if not drivers:
        await callback.answer(f"📭 {title} ro'yxati hozircha bo'sh.", show_alert=True)
        return

    await callback.message.delete()
    for d in drivers[:20]:
        status_emoji = "🟢" if d['status'] == 'active' else "⏳" if d['status'] == 'pending' else "🔴"
        chat_link = f"tg://user?id={d['telegram_id']}"
        car_name = d.get('car_type', "Noma'lum")
        phone = d.get('phone', '')
        balance = d.get('balance', 0)
        text = (
            f"{status_emoji} **{d['full_name']}**\n"
            f"\U0001f464 Profil: [Sizning do'stingiz]({chat_link})\n"
            f"\U0001f194 ID: `{d['telegram_id']}`\n"
            f"\U0001f4de Tel: `+{phone}`\n"
            f"\U0001f697 Mashina: **{car_name}**\n"
            f"\U0001f4b0 Balans: `{balance:,} so'm`"
        )
        kb = admin_driver_manage_kb(d['telegram_id'], d['status'])
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")

    await callback.message.answer(
        f"☝️ {title} (Eng oxirgi {len(drivers[:20])} tasi).\n"
        "To'liq baza (1000+) uchun Dashboard -> Barcha haydovchilar (CSV) bo'limidan foydalaning.",
        reply_markup=admin_back_kb()
    )
    await callback.answer()


# ==========================================
# 4. ADMINLARNI BOSHQARISH
# ==========================================
@router.callback_query(F.data == "admin_manage_admins", IsAdmin())
async def admin_manage_list(callback: types.CallbackQuery):
    current_admins = await db.get_setting('additional_admins', "")
    no_admins_label = "Yo'q"
    admins_display = current_admins if current_admins else no_admins_label
    text = (
        "🛡 **ADMINLAR RO'YXATI**\n\n"
        f"Qo'shimcha adminlar ID lari:\n`{admins_display}`\n\n"
        "Yangi admin qo'shish uchun pastdagi tugmani bosing (Admin ID kerak)."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="add_new_admin")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "add_new_admin", IsAdmin())
async def add_new_admin_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Yangi adminning **Telegram ID** raqamini yuboring:")
    await state.set_state(AdminState.waiting_new_admin_id)


@router.message(AdminState.waiting_new_admin_id, IsAdmin())
async def add_new_admin_save(message: types.Message, state: FSMContext):
    try:
        new_id = int(message.text.strip())
        current = await db.get_setting('additional_admins', '')
        ids = [i.strip() for i in current.split(",") if i.strip()]
        if str(new_id) not in ids:
            ids.append(str(new_id))
            await db.set_setting('additional_admins', ",".join(ids))
            await message.answer(
                f"✅ Admin qo'shildi: `{new_id}`\n\n"
                "Yangi admin botni `/admin` komandasi orqali boshqarishi mumkin.",
                parse_mode="Markdown"
            )
        else:
            await message.answer("ℹ️ Bu ID allaqachon admin ro'yxatida.")
    except:
        await message.answer("❌ ID faqat raqamlardan iborat bo'lishi kerak.")
    await state.clear()


# ==========================================
# 5. TO'LOVLARNI TASDIQLASH / RAD ETISH
# ==========================================
@router.callback_query(F.data.startswith("pay_approve_"), IsAdmin())
async def pay_approve(callback: types.CallbackQuery):
    _, _, pid_str, uid_str = callback.data.split("_")
    pid = int(pid_str)
    uid = int(uid_str)

    await db.update_payment_status(pid, 'approved')

    pay = await db._execute("SELECT amount FROM payments WHERE id = ?", (pid,), fetch_one=True)
    if pay:
        amount = pay['amount']
        avto_fee = await db.get_setting("avto_xabar_fee", "25000")

        if str(amount) == str(avto_fee):
            expires_at = datetime.now() + timedelta(days=30)
            ad = await db.get_ad_message(uid)
            if not ad:
                await db._execute(
                    "INSERT INTO ad_messages (user_id, interval_min, is_active, expires_at) VALUES (?, ?, ?, ?)",
                    (uid, 10, 0, expires_at), commit=True
                )
            else:
                current_exp = ad['expires_at']
                if current_exp:
                    if isinstance(current_exp, str):
                        try:
                            current_exp = datetime.strptime(current_exp, '%Y-%m-%d %H:%M:%S.%f')
                        except:
                            try:
                                current_exp = datetime.strptime(current_exp, '%Y-%m-%d %H:%M:%S')
                            except:
                                current_exp = datetime.now()
                    new_exp = max(current_exp, datetime.now()) + timedelta(days=30)
                else:
                    new_exp = datetime.now() + timedelta(days=30)
                await db._execute(
                    "UPDATE ad_messages SET expires_at = ? WHERE user_id = ?",
                    (new_exp, uid), commit=True
                )
            try:
                await callback.bot.send_message(
                    uid,
                    "✅ <b>Tabriklaymiz!</b>\n\nAvto Xabar xizmati 30 kunga faollashtirildi.",
                    parse_mode="HTML"
                )
            except:
                pass
        else:
            await db.update_driver_balance(uid, amount, mode='add')
            sub_end = datetime.now() + timedelta(days=30)
            await db.update_driver_subscription(uid, sub_end)

    vip_ids_str = await db.get_setting('vip_group_ids', str(VIP_GROUP_ID))
    vip_ids = [int(i.strip()) for i in vip_ids_str.split(",") if i.strip()]

    links = []
    for g_id in vip_ids:
        try:
            invite = await callback.bot.create_chat_invite_link(g_id, member_limit=1)
            links.append(invite.invite_link)
        except Exception as e:
            logger.error(f"Invite link xatosi {g_id}: {e}")

    buttons = []
    if links:
        for idx, link in enumerate(links, 1):
            buttons.append([InlineKeyboardButton(text=f"💎 VIP Guruhga qo'shilish #{idx}", url=link)])

    buttons.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="back_to_role")])

    welcome = (
        "✅ **TO'LOVINGIZ TASDIQLANDI!**\n\n"
        "Balansingiz to'ldirildi va obuna faollashtirildi.\n"
        "Buyurtmalarni qabul qilishingiz mumkin!\n\n"
        "👇 **Quyidagi tugma orqali VIP guruhga qo'shiling:**"
    )

    try:
        await callback.bot.send_message(
            uid,
            welcome,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    except:
        pass

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ **TASDIQLANDI**",
        reply_markup=None
    )
    await callback.answer("To'lov tasdiqlandi!")


@router.callback_query(F.data.startswith("pay_reject_"), IsAdmin())
async def pay_reject(callback: types.CallbackQuery):
    _, _, pid_str, uid_str = callback.data.split("_")
    pid = int(pid_str)
    uid = int(uid_str)

    await db.update_payment_status(pid, 'rejected')
    await db.update_driver_status(uid, 'rejected')

    try:
        await callback.bot.send_message(
            uid,
            "❌ **To'lovingiz rad etildi.**\n\n"
            "Iltimos, **chekni qaytadan yuboring** yoki admin bilan bog'laning.\n\n"
            "<b>Qayta ariza yuborish uchun:</b>\n"
            "1. /start ni bosing\n"
            "2. Haydovchi bo'limiga o'ting\n"
            "3. To'lov chekini qayta yuboring",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Haydovchiga rad etildi xabari yuborib bo'lmadi: {e}")

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ **RAD ETILDI**",
        reply_markup=None
    )
    await callback.answer("To'lov rad etildi!")


# ==========================================
# 6. QORA RO'YXAT VA BLOKLASH
# ==========================================
@router.callback_query(F.data == "admin_blacklist", IsAdmin())
async def admin_blacklist_view(callback: types.CallbackQuery):
    bl = await db.get_blacklist()
    if not bl:
        text = "🚫 **Qora ro'yxat hozirda bo'sh.**"
        await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="Markdown")
        return

    await callback.message.edit_text(
        f"🚫 **QORA RO'YXATDA:** ({len(bl)} ta)",
        reply_markup=None
    )

    for b in bl:
        u = await db.get_user_by_query(str(b['user_id']))
        name = u['full_name'] if u else "Noma'lum"
        reason = b.get('reason', "Noma'lum")
        txt = (
            f"👤 **{name}** (`{b['user_id']}`)\n"
            f"📅 Vaqt: {b['created_at']}\n"
            f"💬 Sabab: {reason}"
        )
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="✅ Bloqdan chiqarish",
                callback_data=f"unblock_global_{b['user_id']}"
            )]
        ])
        await callback.message.answer(txt, reply_markup=kb, parse_mode="Markdown")

    await callback.message.answer(
        "☝️ Foydalanuvchini bloqdan chiqarishingiz mumkin.",
        reply_markup=admin_back_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("block_global_"), IsAdmin())
async def block_global_cb(callback: types.CallbackQuery):
    tid = int(callback.data.split("_")[2])
    await db.add_to_blacklist(tid)
    await callback.answer(f"🚫 ID: {tid} qora ro'yxatga qo'shildi!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("unblock_global_"), IsAdmin())
async def unblock_global_cb(callback: types.CallbackQuery):
    tid = int(callback.data.split("_")[2])
    await db.remove_from_blacklist(tid)
    await callback.answer(f"✅ ID: {tid} qora ro'yxatdan olindi!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)


# ==========================================
# 7. BROADCAST (XABAR YUBORISH)
# ==========================================
@router.callback_query(F.data == "admin_broadcast", IsAdmin())
async def admin_broadcast_menu(callback: types.CallbackQuery, state: FSMContext):
    text = (
        "📢 **ULTRA BROADCAST | REKLAMA MARKAZI**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Kimgacha xabar yetkazmoqchisiz?\n"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Barcha Foydalanuvchilar", callback_data="bc_target_all")],
        [
            InlineKeyboardButton(text="🚕 Haydovchilar", callback_data="bc_target_drivers"),
            InlineKeyboardButton(text="🚶 Yo'lovchilar", callback_data="bc_target_passengers")
        ],
        [InlineKeyboardButton(text="👤 Maxsus (ID/Tel)", callback_data="bc_target_custom")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("bc_target_"), IsAdmin())
async def admin_broadcast_set_target(callback: types.CallbackQuery, state: FSMContext):
    target = callback.data.replace("bc_target_", "")
    await state.update_data(bc_target=target)

    if target == "custom":
        await callback.message.edit_text("👤 **ID yoki Telefon raqamini kiriting:**", parse_mode="Markdown")
        await state.set_state(AdminState.waiting_broadcast_user_query)
    else:
        target_upper = target.upper()
        await callback.message.edit_text(
            f"📝 **Xabarni yuboring (Text, Photo, Video, File):**\nTarget: `{target_upper}`",
            parse_mode="Markdown"
        )
        await state.set_state(AdminState.waiting_broadcast_msg)


@router.message(AdminState.waiting_broadcast_user_query, IsAdmin())
async def admin_broadcast_custom_query(message: types.Message, state: FSMContext):
    query = message.text.strip().replace("+", "")
    user = await db.get_user_by_query(query)
    if not user:
        await message.answer("❌ **Foydalanuvchi topilmadi.** Qayta urinib ko'ring:")
        return

    await state.update_data(bc_user_id=user['telegram_id'])
    await message.answer(f"✅ Topildi: **{user['full_name']}**\nEndi xabarni yuboring:", parse_mode="Markdown")
    await state.set_state(AdminState.waiting_broadcast_msg)


@router.message(AdminState.waiting_broadcast_msg, IsAdmin())
async def admin_broadcast_get_content(message: types.Message, state: FSMContext):
    await state.update_data(bc_msg_id=message.message_id, bc_chat_id=message.chat.id)
    text = (
        "🎮 **TUGMALARNI SOZLASH (MODERN UI)**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Tugma qo'shish uchun quyidagi formatda yuboring (har biri yangi qatorda):\n"
        "`Tugma nomi - https://link.com`\n\n"
        "Tugmalar kerak bo'lmasa **'tm'** deb yozing."
    )
    await message.answer(text, parse_mode="Markdown")
    await state.set_state(AdminState.waiting_broadcast_button)


@router.message(AdminState.waiting_broadcast_button, IsAdmin())
async def admin_broadcast_confirm(message: types.Message, state: FSMContext, bot: Bot):
    user_input = message.text.strip()
    kb_data = []

    if user_input.lower() != 'tm':
        lines = user_input.split('\n')
        for line in lines:
            if '-' in line:
                try:
                    name, url = line.split('-', 1)
                    kb_data.append([InlineKeyboardButton(text=name.strip(), url=url.strip())])
                except:
                    pass

    await state.update_data(bc_kb=kb_data)
    data = await state.get_data()

    await message.answer("👀 **XABAR PREVIEW (KO'RINISHI):**\n━━━━━━━━━━━━━━━", parse_mode="Markdown")
    kb = InlineKeyboardMarkup(inline_keyboard=kb_data) if kb_data else None
    await bot.copy_message(
        chat_id=message.chat.id,
        from_chat_id=data['bc_chat_id'],
        message_id=data['bc_msg_id'],
        reply_markup=kb
    )

    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 TASDIQLASH (SEND)", callback_data="bc_confirm_send")],
        [InlineKeyboardButton(text="❌ BEKOR QILISH", callback_data="admin_broadcast")]
    ])
    await message.answer("❓ **Xabar barchaga yuborilsinmi?**", reply_markup=confirm_kb, parse_mode="Markdown")
    await state.set_state(AdminState.confirming_broadcast)


@router.callback_query(F.data == "bc_confirm_send", IsAdmin())
async def admin_broadcast_execute(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target = data['bc_target']
    msg_id = data['bc_msg_id']
    from_chat = data['bc_chat_id']
    kb = InlineKeyboardMarkup(inline_keyboard=data['bc_kb']) if data['bc_kb'] else None

    if target == 'all':
        u_list = await db.get_all_users_for_broadcast()
    elif target == 'drivers':
        drivers = await db.get_users_by_role('driver')
        u_list = [d['telegram_id'] for d in drivers]
    elif target == 'passengers':
        passengers = await db.get_users_by_role('passenger')
        u_list = [p['telegram_id'] for p in passengers]
    elif target == 'custom':
        u_list = [data['bc_user_id']]
    else:
        u_list = []

    await callback.message.edit_text(
        f"🚀 **REKLAMA YUKLANMOQDA...**\nTarget: `{len(u_list)}` kishi",
        parse_mode="Markdown"
    )

    success = 0
    fail = 0

    for uid in u_list:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=from_chat, message_id=msg_id, reply_markup=kb)
            success += 1
            if success % 10 == 0:
                await asyncio.sleep(0.1)
        except:
            fail += 1

    res_text = (
        "📊 **YAKUNIY HISOBOT**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Muvaffaqiyatli: `{success}`\n"
        f"🚫 Qabul qilmadi: `{fail}`\n"
        f"🏁 Jami: `{len(u_list)}` kishi"
    )
    await callback.message.edit_text(res_text, reply_markup=admin_back_kb(), parse_mode="Markdown")
    await state.clear()


# ==========================================
# 8. MOLIYAVIY BOSHQARUV
# ==========================================
@router.callback_query(F.data == "admin_payments_pending", IsAdmin())
async def admin_payments_pending_handler(callback: types.CallbackQuery):
    pays = await db.get_pending_payments()
    if not pays:
        await callback.answer("💰 Tasdiqlanishi kerak bo'lgan to'lovlar yo'q.", show_alert=True)
        return

    await callback.message.delete()
    for p in pays:
        txt = (
            f"💳 **TO'LOV #{p['id']}**\n"
            f"👤 Haydovchi: {p['full_name']} (`{p['user_id']}`)\n"
            f"💰 Summa: `{p['amount']:,}` so'm\n"
            f"📅 Vaqt: {p['created_at']}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"pay_approve_{p['id']}_{p['user_id']}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"pay_reject_{p['id']}_{p['user_id']}")
            ]
        ])
        await callback.message.answer_photo(p['photo_id'], caption=txt, reply_markup=kb)

    await callback.message.answer("☝️ To'lovlarni tasdiqlang.", reply_markup=admin_back_kb())


@router.callback_query(F.data == "admin_payments_history", IsAdmin())
async def admin_payments_history_handler(callback: types.CallbackQuery):
    history = await db._execute("SELECT * FROM payments ORDER BY created_at DESC LIMIT 20", fetch_all=True)
    if not history:
        await callback.answer("📭 To'lovlar tarixi bo'sh.", show_alert=True)
        return

    text = "📜 **TO'LOVLAR TARIXI (Oxirgi 20 ta):**\n\n"
    for p in history:
        status_icon = "✅" if p['status'] == 'approved' else "❌" if p['status'] == 'rejected' else "⏳"
        text += f"{status_icon} #{p['id']} | {p['amount']:,} so'm | {p['user_id']}\n"

    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="Markdown")


@router.callback_query(F.data == "admin_edit_card", IsAdmin())
async def admin_edit_card_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(setting_key='payment_card')
    await callback.message.answer("💳 **Yangi plastik karta raqamini kiriting:**\n(Masalan: 9860 0000 0000 0000)")
    await state.set_state(AdminState.waiting_setting_value)


# ==========================================
# 9. GRABBER
# ==========================================
@router.callback_query(F.data == "admin_grabber", IsAdmin())
async def admin_grabber_menu(callback: types.CallbackQuery):
    grabber_on = await db.get_setting('grabber_enabled', '1')
    default_sources = ",".join(map(str, GRABBER_SOURCES))
    sources = await db.get_setting('grabber_sources', default_sources)

    status_emoji = "🟢 YOQILGAN" if grabber_on == '1' else "🔴 O'CHIRILGAN"

    text = (
        "🦅 **ORDERS GRABBER (BUYURTMA YIG'ISH)**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚙️ Holati: **{status_emoji}**\n"
        f"📋 Manbalar (ID): `{sources}`\n\n"
        "Grabber boshqa kanallardan buyurtmalarni avtomatik saralab, VIP guruhga yo'naltiradi."
    )

    toggle_label = "🔴 O'chirish" if grabber_on == '1' else "🟢 Yoqish"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_label, callback_data="toggle_grabber")],
        [InlineKeyboardButton(text="✏️ Manbalarni tahrirlash", callback_data="edit_grabber_sources")],
        [
            InlineKeyboardButton(text="📍 Joylar", callback_data="edit_grabber_locs"),
            InlineKeyboardButton(text="🎯 Maqsadlar", callback_data="edit_grabber_ints")
        ],
        [InlineKeyboardButton(text="🚫 Taqiqlar (Excludes)", callback_data="edit_grabber_excs")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "toggle_grabber", IsAdmin())
async def toggle_grabber_handler(callback: types.CallbackQuery):
    curr = await db.get_setting('grabber_enabled', '1')
    new = '0' if curr == '1' else '1'
    await db.set_setting('grabber_enabled', new)
    status_label = "Yoqildi" if new == '1' else "O'chirildi"
    await callback.answer(f"🦅 Grabber: {status_label}")
    await admin_grabber_menu(callback)


@router.callback_query(F.data.in_(["edit_grabber_sources", "edit_grabber_locs", "edit_grabber_ints", "edit_grabber_excs"]), IsAdmin())
async def edit_grabber_settings_flow(callback: types.CallbackQuery, state: FSMContext):
    key_map = {
        "edit_grabber_sources": "grabber_sources",
        "edit_grabber_locs": "grabber_locations",
        "edit_grabber_ints": "grabber_intents",
        "edit_grabber_excs": "grabber_excludes"
    }
    key = key_map[callback.data]
    await state.update_data(setting_key=key)

    prompts = {
        "grabber_sources": "Guruh ID larini vergul bilan yozing (masalan: -100123, -100456):",
        "grabber_locations": "Qaysi shaharlar/joylar bo'yicha qidirishini yozing (vergul bilan):",
        "grabber_intents": "Qanday kalit so'zlar bo'yicha qidirishini yozing (vergul bilan):",
        "grabber_excludes": "Qaysi so'zlar bo'lsa xabarni tashlab yuborishini yozing (vergul bilan):"
    }

    await callback.message.answer(f"✍️ **{prompts[key]}**")
    await state.set_state(AdminState.waiting_setting_value)


# ==========================================
# 10. FOYDALANUVCHI QIDIRUVI
# ==========================================
@router.callback_query(F.data == "admin_search_user", IsAdmin())
async def admin_search_user_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔎 **MULTIFILTR QIDIRUV TIZIMI**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Istalgan foydalanuvchini **ID raqami** yoki **Telefon raqami** orqali toping.\n\n"
        "📲 **Namuna:** `+998901234567` yoki `123456789`",
        reply_markup=admin_back_kb(),
        parse_mode="Markdown"
    )
    await state.set_state(AdminState.waiting_user_query)


@router.message(AdminState.waiting_user_query, IsAdmin())
async def admin_search_user_result(message: types.Message, state: FSMContext):
    await state.clear()
    query = message.text.strip().replace("+", "")
    user = await db.get_user_by_query(query)

    if not user:
        await message.answer(
            "❌ **Foydalanuvchi topilmadi.**\nIltimos, ma'lumotlarni tekshirib qayta kiriting.",
            reply_markup=admin_back_kb(),
            parse_mode="Markdown"
        )
        return

    role = user.get('role', 'driver' if 'car_type' in user else 'passenger')
    j_at = user.get('joined_at', "Noma'lum")
    chat_link = f"tg://user?id={user['telegram_id']}"
    phone = user.get('phone', "Yo'q")
    role_upper = role.upper()

    text = (
        f"🔎 **DETAIL PROFIL: {user['full_name'].upper()}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 **Profil:** [Telegram Profil]({chat_link})\n"
        f"🛠 **Role:** `{role_upper}`\n"
        f"📞 **Tel:** `+{phone}`\n"
        f"🆔 **ID:** `{user['telegram_id']}`\n"
        f"📅 **A'zo:** `{j_at}`\n"
    )

    if role == 'driver':
        car = user.get('car_type', '-')
        balance = user.get('balance', 0)
        sub_end = user.get('subscription_end', '-')
        status = user.get('status', '-').upper()
        text += (
            f"🚗 **Mashina:** `{car}`\n"
            f"💰 **Balans:** `{balance:,} so'm`\n"
            f"📂 **Sub end:** `{sub_end}`\n"
            f"⚙️ **Status:** `{status}`\n"
        )
        kb = admin_driver_manage_kb(user['telegram_id'], user.get('status', 'pending'))
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Xabar yuborish", callback_data=f"message_user_{user['telegram_id']}")],
            [InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"block_global_{user['telegram_id']}")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_users_menu")]
        ])

    await message.answer(text, parse_mode="Markdown", reply_markup=kb, disable_web_page_preview=True)


# ==========================================
# 11. HAYDOVCHI STATUS / OBUNA / BALANS
# ==========================================
@router.callback_query(F.data.startswith("set_status_"), IsAdmin())
async def admin_set_status_manual(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    new_status = parts[2]
    uid = int(parts[3])
    await db.update_driver_status(uid, new_status)
    await callback.answer(f"Status {new_status} ga o'zgartirildi!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=admin_driver_manage_kb(uid, new_status))
    try:
        msg = "✅ Tabriklaymiz! Hisobingiz aktivlashtirildi." if new_status == 'active' else "❌ Arizangiz rad etildi."
        await callback.bot.send_message(uid, msg)
    except:
        pass


@router.callback_query(F.data.startswith("extend_sub_"), IsAdmin())
async def extend_sub_handler(callback: types.CallbackQuery):
    tid = int(callback.data.split("_")[2])

    d = await db.get_driver(tid)
    current_exp = d.get('subscription_end')

    if current_exp:
        if isinstance(current_exp, str):
            try:
                current_exp = datetime.strptime(current_exp, '%Y-%m-%d %H:%M:%S.%f')
            except:
                try:
                    current_exp = datetime.strptime(current_exp, '%Y-%m-%d %H:%M:%S')
                except:
                    current_exp = datetime.now()
        new_exp = max(current_exp, datetime.now()) + timedelta(days=30)
    else:
        new_exp = datetime.now() + timedelta(days=30)

    await db.update_driver_subscription(tid, new_exp)
    await callback.answer("✅ Obuna 30 kunga uzaytirildi!", show_alert=True)
    new_exp_str = new_exp.strftime('%Y-%m-%d')
    await callback.message.answer(f"✅ ID: {tid} obunasi uzaytirildi. Yangi muddat: {new_exp_str}")

    try:
        await callback.bot.send_message(
            tid,
            f"🚀 **VIP OBUNA UZAYTIRILDI!**\n\nAdmin tomonidan obunangiz 30 kunga uzaytirildi. Yangi muddat: {new_exp_str}"
        )
    except:
        pass


@router.callback_query(F.data.startswith("refill_one_"), IsAdmin())
async def refill_one_driver_start(callback: types.CallbackQuery, state: FSMContext):
    tid = int(callback.data.split("_")[2])
    await state.update_data(target_tid=tid)
    await callback.message.answer(
        f"💰 ID: {tid} haydovchi balansiga qancha qo'shmoqchisiz?\n(Faqat raqam yozing, masalan: 50000)"
    )
    await state.set_state(AdminState.waiting_amount_refill)


@router.message(AdminState.waiting_amount_refill, IsAdmin())
async def refill_amount_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Support both target_tid (from refill_one) and target_uid (from admin_refill)
    tid = data.get('target_tid') or data.get('target_uid')
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    amount = int(message.text)
    await db.update_driver_balance(tid, amount, mode='add')
    await message.answer(f"✅ ID: {tid} balansiga {amount:,} so'm qo'shildi.", parse_mode="Markdown")
    try:
        await message.bot.send_message(tid, f"💰 Admin tomonidan balansingiz {amount:,} so'mga to'ldirildi.")
    except:
        pass
    await state.clear()


@router.callback_query(F.data.startswith("message_user_"), IsAdmin())
async def message_user_start(callback: types.CallbackQuery, state: FSMContext):
    tid = int(callback.data.split("_")[2])
    await state.update_data(target_tid=tid)
    await callback.message.answer(f"✉️ ID: {tid} foydalanuvchiga xabar matnini yuboring:")
    await state.set_state(AdminState.waiting_direct_message)


@router.message(AdminState.waiting_direct_message, IsAdmin())
async def message_user_send(message: types.Message, state: FSMContext):
    data = await state.get_data()
    tid = data.get('target_tid') or data.get('target_uid')
    text = message.text
    try:
        await message.bot.send_message(tid, f"👨‍💼 **ADMIN XABARI:**\n\n{text}", parse_mode="Markdown")
        await message.answer("✅ Xabar yuborildi.")
    except:
        await message.answer("❌ Xabar yuborishda xatolik (foydalanuvchi botni bloklagan bo'lishi mumkin).")
    await state.clear()


# ==========================================
# 12. FOYDALANUVCHILAR MENYUSI
# ==========================================
@router.callback_query(F.data == "admin_users_menu", IsAdmin())
async def admin_users_menu_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👥 **FOYDALANUVCHILARNI BOSHQARISH**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Baza bo'yicha qidirish yoki guruhlarni ko'rish:",
        reply_markup=admin_users_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "show_all_drivers", IsAdmin())
async def admin_show_all_drivers(callback: types.CallbackQuery):
    drivers = await db.get_all_drivers(limit=1000)
    if not drivers:
        await callback.answer("📭 Haydovchilar topilmadi.", show_alert=True)
        return

    if len(drivers) > 30:
        report = "Telegram ID, Full Name, Phone, Car, Status, Balance, Joined At\n"
        for d in drivers:
            report += (
                f"{d['telegram_id']}, {d.get('full_name', '?')}, {d.get('phone', '?')}, "
                f"{d.get('car_type', '?')}, {d.get('status', '?')}, "
                f"{d.get('balance', 0)}, {d.get('joined_at', '')}\n"
            )
        from aiogram.types import BufferedInputFile
        file = BufferedInputFile(report.encode('utf-8'), filename="barcha_haydovchilar.csv")
        await callback.message.answer_document(file, caption="📂 Barcha haydovchilar (.csv)")

    text = "🚗 **BARCHA HAYDOVCHILAR (Oxirgi 30 ta):**\n\n"
    for d in drivers[:30]:
        text += f"• `{d['telegram_id']}` | **{d['full_name']}** | `+{d['phone']}`\n"

    await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="Markdown")


@router.callback_query(F.data == "show_all_passengers", IsAdmin())
async def admin_show_all_passengers(callback: types.CallbackQuery):
    ps = await db.get_users_by_role('passenger')
    if not ps:
        await callback.answer("📭 Yo'lovchilar topilmadi.", show_alert=True)
        return

    if len(ps) > 30:
        report = "Telegram ID, Full Name, Phone, Joined At\n"
        for p in ps:
            report += f"{p['telegram_id']}, {p.get('full_name', '?')}, {p.get('phone', '?')}, {p.get('joined_at', '')}\n"
        from aiogram.types import BufferedInputFile
        file = BufferedInputFile(report.encode('utf-8'), filename="barcha_yolovchilar.csv")
        await callback.message.answer_document(file, caption="📂 Barcha yo'lovchilar (.csv)")

    text = "🚶 **BARCHA YO'LOVCHILAR (Oxirgi 30 ta):**\n"
    text += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    for p in ps[:30]:
        chat_link = f"tg://user?id={p['telegram_id']}"
        text += f"• `{p['telegram_id']}` | **[{p['full_name']}]({chat_link})** | `+{p['phone']}`\n"

    await callback.message.edit_text(
        text, reply_markup=admin_back_kb(), parse_mode="Markdown", disable_web_page_preview=True
    )


@router.callback_query(F.data == "show_all_users_combined", IsAdmin())
async def admin_show_all_users_combined(callback: types.CallbackQuery):
    drivers = await db.get_all_drivers(limit=5000)
    passengers = await db.get_users_by_role('passenger')

    report = "Role, Telegram ID, Full Name, Phone, Car/Join Status, Balance/Joined At\n"
    for d in drivers:
        report += (
            f"Driver, {d['telegram_id']}, {d.get('full_name', '?')}, "
            f"{d.get('phone', '?')}, {d.get('car_type', '?')}, {d.get('balance', 0)}\n"
        )
    for p in passengers:
        report += (
            f"Passenger, {p['telegram_id']}, {p.get('full_name', '?')}, "
            f"{p.get('phone', '?')}, {p.get('status', '?')}, {p.get('joined_at', '')}\n"
        )

    from aiogram.types import BufferedInputFile
    file = BufferedInputFile(report.encode('utf-8'), filename="jonli_taxi_toplam_baza.csv")
    await callback.message.answer_document(
        file,
        caption="📂 **MASTER BAZA (Barcha foydalanuvchilar)**\n\n_Ushbu faylda barcha haydovchi va yo'lovchilar ma'lumotlari jamlangan._",
        parse_mode="Markdown"
    )
    await callback.answer()


# ==========================================
# 13. BUYURTMALAR BOSHQARUVI
# ==========================================
@router.callback_query(F.data == "admin_orders", IsAdmin())
async def admin_orders_menu(callback: types.CallbackQuery):
    orders = await db.get_pending_orders(limit=20)
    if not orders:
        await callback.answer("📭 Hozirda ochiq buyurtmalar yo'q.", show_alert=True)
        return

    text = "🚕 **OCHIQ BUYURTMALAR (Oxirgi 20 ta):**\n"
    text += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    kb = []
    for o in orders:
        o_id = o['id']
        p_name = o.get('passenger_name', 'Mijoz')
        order_type = o['type'].upper()
        text += f"📍 `{o_id}` | **{p_name}** | {order_type} | `{o['status']}`\n"
        kb.append([InlineKeyboardButton(text=f"❌ O'chirish ({o_id})", callback_data=f"del_order_{o_id}")])

    kb.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


@router.callback_query(F.data.startswith("del_order_"), IsAdmin())
async def admin_delete_order(callback: types.CallbackQuery):
    o_id = int(callback.data.split("_")[2])
    await db.delete_order(o_id)
    await callback.answer(f"Buyurtma #{o_id} o'chirildi!", show_alert=True)
    await admin_orders_menu(callback)


# ==========================================
# 14. MOLIYA VA PROMO-KODLAR
# ==========================================
@router.callback_query(F.data == "admin_payments_menu", IsAdmin())
async def admin_payments_extended_menu(callback: types.CallbackQuery):
    stats = await db.get_stats()
    text = (
        "💰 **MOLIYA & TO'LOVLAR**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Daromad (Total): `{stats['total_revenue']:,} so'm`\n"
        "Quyidagilardan birini tanlang:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Kutilayotgan To'lovlar", callback_data="admin_payments_pending")],
        [InlineKeyboardButton(text="🎟 Promo-kodlar", callback_data="admin_promocodes")],
        [InlineKeyboardButton(text="💳 Karta sozlamalari", callback_data="admin_edit_card")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "admin_promocodes", IsAdmin())
async def admin_promocodes_menu(callback: types.CallbackQuery):
    promos = await db.get_all_promocodes()
    text = "🎟 **PROMO-KODLAR RO'YXATI:**\n"
    text += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    if not promos:
        text += "_Hozircha promo-kodlar yo'q._"

    kb = []
    for p in promos:
        text += f"• `{p['code']}` | `{p['amount']:,} so'm` | `{p['used_count']}/{p['max_uses']}`\n"
        kb.append([InlineKeyboardButton(text=f"🗑 {p['code']}", callback_data=f"del_promo_{p['code']}")])

    kb.append([InlineKeyboardButton(text="➕ Yangi yaratish", callback_data="add_promocode")])
    kb.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_payments_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


@router.callback_query(F.data == "add_promocode", IsAdmin())
async def add_promocode_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ **Yangi promo-kod nomini yuboring:**\n(Masalan: JONLI5000)")
    await state.set_state(AdminState.waiting_promo_code)


@router.message(AdminState.waiting_promo_code, IsAdmin())
async def add_promocode_code(message: types.Message, state: FSMContext):
    await state.update_data(promo_code=message.text.upper().strip())
    await message.answer(
        "💰 **Ushbu kod necha so'm chegirma yoki balans berishini yozing:**\n(Faqat raqam, masalan: 5000)"
    )
    await state.set_state(AdminState.waiting_promo_amount)


@router.message(AdminState.waiting_promo_amount, IsAdmin())
async def add_promocode_finish(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return

    data = await state.get_data()
    code = data['promo_code']
    amount = int(message.text)

    await db.create_promocode(code, amount)
    await message.answer(f"✅ Promo-kod yaratildi: `{code}` - `{amount:,} so'm`", parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data.startswith("del_promo_"), IsAdmin())
async def del_promo_handler(callback: types.CallbackQuery):
    code = callback.data.split("_")[2]
    await db.delete_promocode(code)
    await callback.answer(f"Promo-kod {code} o'chirildi!", show_alert=True)
    await admin_promocodes_menu(callback)


# ==========================================
# 15. GURUHLARNI BOSHQARISH
# ==========================================
@router.callback_query(F.data == "admin_groups", IsAdmin())
async def admin_groups_menu(callback: types.CallbackQuery):
    vip = await db.get_setting('vip_group_ids', "Noma'lum")
    free = await db.get_setting('free_group_ids', "Noma'lum")

    text = (
        "👥 **GURUHLAR BOSHQARUVI**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💎 VIP Guruhlar: <code>{vip}</code>\n"
        f"🆓 Bepul Guruhlar: <code>{free}</code>\n\n"
        "Guruh ID larini o'zgartirish uchun tugmalarni bosing:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 VIP ID larni tahrirlash", callback_data="edit_vip_groups")],
        [InlineKeyboardButton(text="🆓 Bepul ID larni tahrirlash", callback_data="edit_free_groups")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "edit_vip_groups", IsAdmin())
async def edit_vip_groups_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(setting_key='vip_group_ids')
    await callback.message.answer("✍️ **Yangi VIP guruh ID larini yuboring:**\n(Vergul bilan, masalan: -1001, -1002)")
    await state.set_state(AdminState.waiting_setting_value)


@router.callback_query(F.data == "edit_free_groups", IsAdmin())
async def edit_free_groups_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(setting_key='free_group_ids')
    await callback.message.answer("✍️ **Yangi Bepul guruh ID larini yuboring:**\n(Vergul bilan, masalan: -1003, -1004)")
    await state.set_state(AdminState.waiting_setting_value)


# ==========================================
# 16. SOZLAMALAR
# ==========================================
@router.callback_query(F.data == "admin_settings", IsAdmin())
async def admin_settings_menu(callback: types.CallbackQuery):
    min_taxi = await db.get_setting('min_price_taxi', '20000')
    sub_fee = await db.get_setting('driver_subscription_fee', '20000')
    mand_sub = await db.get_setting('mandatory_sub', 'off')
    maint_mode = await db.get_setting('maintenance_mode', 'off')

    try:
        mt = f"{int(min_taxi):,}"
    except:
        mt = min_taxi
    try:
        sf = f"{int(sub_fee):,}"
    except:
        sf = sub_fee

    mand_status = "🟢 ACTIVATED" if mand_sub == 'on' else "🔴 DISABLED"
    maint_status = "⚠️ EMERGENCY" if maint_mode == 'on' else "🟢 STABLE"
    mand_upper = mand_sub.upper()
    maint_upper = maint_mode.upper()

    text = (
        "⚙️ **TIZIM KRITIK SOZLAMALARI**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🚖 Min Taxi Narxi: `{mt} so'm`\n"
        f"💰 Haydovchi oylik obuna: `{sf} so'm`\n"
        f"📢 Majburiy obuna: **{mand_status}**\n"
        f"🛠 Texnik ish (Maintenance): **{maint_status}**\n\n"
        "O'zgartirish uchun bo'limni tanlang 👇"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚖 Taxi narxi", callback_data="edit_price_taxi"),
            InlineKeyboardButton(text="💰 Obuna narxi", callback_data="edit_sub_fee")
        ],
        [
            InlineKeyboardButton(text=f"📢 Sub: {mand_upper}", callback_data="toggle_mand_sub"),
            InlineKeyboardButton(text=f"🛠 Maint: {maint_upper}", callback_data="toggle_maint_mode")
        ],
        [InlineKeyboardButton(text="📋 Majburiy Kanallar", callback_data="edit_mand_channels")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except:
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "toggle_maint_mode", IsAdmin())
async def toggle_maint_mode_handler(callback: types.CallbackQuery):
    curr = await db.get_setting('maintenance_mode', 'off')
    new = 'on' if curr == 'off' else 'off'
    await db.set_setting('maintenance_mode', new)
    await callback.answer(f"🛠 Texnik holat: {new.upper()}")
    await admin_settings_menu(callback)


@router.callback_query(F.data == "edit_price_taxi", IsAdmin())
async def edit_price_taxi_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(setting_key='min_price_taxi')
    await callback.message.answer("✍️ Yangi taksi minimal narxini kiriting (faqat raqam):")
    await state.set_state(AdminState.waiting_setting_value)


@router.message(AdminState.waiting_setting_value, IsAdmin())
async def process_setting_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    key = data.get('setting_key')
    val = message.text.strip()
    await db.set_setting(key, val)
    await message.answer(f"✅ O'zgarish saqlandi: `{key}` -> `{val}`", parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data == "edit_sub_fee", IsAdmin())
async def edit_sub_fee_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(setting_key='driver_subscription_fee')
    await callback.message.answer("✍️ Yangi obuna narxini yozing (so'mda):")
    await state.set_state(AdminState.waiting_setting_value)


@router.callback_query(F.data == "toggle_mand_sub", IsAdmin())
async def toggle_mand_sub_callback(callback: types.CallbackQuery):
    curr = await db.get_setting('mandatory_sub', 'off')
    new = 'on' if curr == 'off' else 'off'
    await db.set_setting('mandatory_sub', new)
    await callback.answer(f"📢 Majburiy obuna: {new.upper()}", show_alert=True)
    await admin_settings_menu(callback)


@router.callback_query(F.data == "edit_mand_channels", IsAdmin())
async def edit_mand_channels_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(setting_key='mandatory_channels')
    await callback.message.answer(
        "✍️ **Yangi majburiy kanallarni kiriting:**\n\n"
        "Faqat guruh/kanal **ID raqamlarini** vergul bilan yozing:\n"
        "Masalan: `-100123456789,-100987654321`\n\n"
        "*(Bot bu guruhlarda admin bo'lishi shart)*",
        parse_mode="Markdown"
    )
    await state.set_state(AdminState.waiting_setting_value)


# ==========================================
# 17. AVTO XABAR BOSHQARUVI
# ==========================================
@router.callback_query(F.data == "admin_avto_xabar", IsAdmin())
async def admin_avto_xabar_menu(callback: types.CallbackQuery):
    fee = await db.get_setting('avto_xabar_fee', '25000')
    groups = await db.get_setting('avto_xabar_groups', 'all')

    groups_display = "🔄 Barcha guruhlar (Avtomatik)" if groups == 'all' else groups

    all_pending = await db.get_pending_payments()
    avto_pending = [p for p in all_pending if str(p['amount']) == str(fee)]

    text = (
        "🤖 <b>AVTO XABAR SOZLAMALARI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Xizmat narxi (30 kun): <code>{fee}</code> so'm\n"
        f"📋 Guruhlar: <code>{groups_display}</code>\n"
        f"💳 Kutilayotgan to'lovlar: <b>{len(avto_pending)} ta</b>\n"
    )
    await callback.message.edit_text(text, reply_markup=admin_avto_xabar_kb(len(avto_pending)), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_avto_payments", IsAdmin())
async def admin_avto_payments(callback: types.CallbackQuery):
    fee = await db.get_setting('avto_xabar_fee', '25000')
    all_pending = await db.get_pending_payments()
    avto_pending = [p for p in all_pending if str(p['amount']) == str(fee)]

    if not avto_pending:
        await callback.answer("📭 Yangi to'lovlar yo'q.", show_alert=True)
        return

    await callback.message.delete()
    for p in avto_pending:
        text = (
            f"👤 <b>Foydalanuvchi:</b> {p['full_name']}\n"
            f"🆔 <b>ID:</b> <code>{p['user_id']}</code>\n"
            f"💰 <b>Summa:</b> {p['amount']} so'm\n"
            f"📅 <b>Sana:</b> {p['created_at']}"
        )
        await callback.message.answer_photo(
            p['photo_id'],
            caption=text,
            reply_markup=admin_avto_pay_manage_kb(p['id'], p['user_id']),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("avtopay_"), IsAdmin())
async def handle_avto_payment_action(callback: types.CallbackQuery, bot: Bot):
    _, action, pid, uid = callback.data.split("_")
    pid, uid = int(pid), int(uid)

    if action == "ok":
        await db.update_payment_status(pid, 'approved')
        new_exp = datetime.now() + timedelta(days=30)
        await db.update_ad_message(uid, expires_at=new_exp, is_active=1)
        try:
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n✅ <b>TASDIQLANDI!</b>",
                parse_mode="HTML"
            )
        except:
            pass
        try:
            await bot.send_message(
                uid,
                "✅ <b>Avto Xabar to'lovingiz tasdiqlandi!</b>\n\nXizmat 30 kunga faollashtirildi.",
                parse_mode="HTML"
            )
        except:
            pass
    else:
        await db.update_payment_status(pid, 'rejected')
        try:
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n❌ <b>RAD ETILDI!</b>",
                parse_mode="HTML"
            )
        except:
            pass
        try:
            await bot.send_message(
                uid,
                "❌ <b>Sizning Avto Xabar to'lovingiz rad etildi.</b>\n\nIltimos, qayta rasm yuboring yoki admin bilan bog'laning.",
                parse_mode="HTML"
            )
        except:
            pass
    await callback.answer()


@router.callback_query(F.data == "edit_avto_fee", IsAdmin())
async def edit_avto_fee_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(setting_key='avto_xabar_fee')
    await callback.message.answer("✍️ Yangi Avto Xabar narxini yozing (so'mda):")
    await state.set_state(AdminState.waiting_setting_value)


@router.callback_query(F.data == "edit_avto_groups", IsAdmin())
async def edit_avto_groups_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(setting_key='avto_xabar_groups')
    await callback.message.answer(
        "✍️ **Guruhlar ro'yxatini kiriting:**\n\n"
        "Guruh ID larini vergul bilan yozing.\n"
        "Agar `all` deb yozsangiz, bot admin bo'lgan **barcha** guruhlarga yuboradi.\n\n"
        "Masalan: `-100123,-100456` yoki `all`",
        parse_mode="Markdown"
    )
    await state.set_state(AdminState.waiting_setting_value)


# ==========================================
# 18. BAZANI YUKLAB OLISH & LOGLAR
# ==========================================
@router.callback_query(F.data == "admin_download_db", IsAdmin())
async def admin_download_db_handler(callback: types.CallbackQuery):
    from aiogram.types import FSInputFile

    if os.path.exists(DB_PATH):
        filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
        file = FSInputFile(DB_PATH, filename=filename)
        await callback.message.answer_document(
            file,
            caption="📁 **Asosiy ma'lumotlar bazasi (SQLite)**",
            parse_mode="Markdown"
        )
        await callback.answer("✅ Baza yuborildi.")


@router.callback_query(F.data == "admin_view_logs", IsAdmin())
async def admin_view_logs_handler(callback: types.CallbackQuery):
    log_path = os.path.join(os.getcwd(), "bot_new.log")
    if not os.path.exists(log_path):
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Log initialized at {datetime.now()}\n")

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 3500))
            text = f.read()

        if not text:
            text = "Tizim jurnallari hozircha bo'sh."

        size_kb = size / 1024
        log_name = os.path.basename(log_path)
        header = (
            "📝 **TIZIM JURNALLARI (REAL-TIME LOGS)**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Fayl: `{log_name}` | Hajmi: `{size_kb:.1f} KB`\n"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_view_logs")],
            [InlineKeyboardButton(text="🗑 Jurnalni Tozalash", callback_data="admin_clear_logs")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
        ])

        await callback.message.edit_text(
            f"{header}```\n...{text}\n```",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.answer(f"❌ Log Error: {e}", show_alert=True)
        logger.error(f"Admin log logic failed: {e}")


@router.callback_query(F.data == "admin_clear_logs", IsAdmin())
async def admin_clear_logs_handler(callback: types.CallbackQuery):
    log_path = os.path.join(os.getcwd(), "bot_new.log")
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"--- LOG CLEARED BY ADMIN AT {datetime.now()} ---\n")
        await callback.answer("✅ Log fayli muvaffaqiyatli tozalandi.", show_alert=True)
        await admin_view_logs_handler(callback)
    except Exception as e:
        await callback.answer(f"❌ Error: {e}", show_alert=True)


# ==========================================
# 19. TIZIM MONITORINGI
# ==========================================
@router.callback_query(F.data == "admin_health", IsAdmin())
async def admin_health_handler(callback: types.CallbackQuery):
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_mb = db_size / (1024 * 1024)
    os_name = os.name.upper()

    text = (
        "🏥 **TIZIM MONITORINGI (BOT HEALTH)**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 **Server vaqti:** `{now}`\n"
        f"🗄 **Baza hajmi (DB):** `{db_mb:.2f} MB`\n"
        "🕒 **Uptime kodi:** STABLE\n"
        f"📍 **OS:** `{os_name}`\n\n"
        "Tizim eng yuqori performans (High CPU Priority) darajasida ishlamoqda. ✅"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_health")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


# ==========================================
# 20. UNBLOCK USER (users menu)
# ==========================================
@router.callback_query(F.data.startswith("unblock_user_"), IsAdmin())
async def admin_unblock_user_callback(callback: types.CallbackQuery):
    tid = int(callback.data.split("_")[2])
    await db.remove_from_blacklist(tid)
    await callback.answer(f"✅ {tid} blokdan chiqarildi!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)
