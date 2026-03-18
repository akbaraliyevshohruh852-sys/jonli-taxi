from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from core.config import ADMIN_IDS
from core import database as db
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.my_chat_member()
async def on_my_chat_member(update: types.ChatMemberUpdated):
    """Bot guruhga qo'shilganda yoki chiqarilganda ishlaydi"""
    new_status = update.new_chat_member.status
    chat_id = update.chat.id
    chat_title = update.chat.title or "Noma'lum guruh"

    logger.info(f"Chat Member Update: {chat_id} - {chat_title} - Status: {new_status}")

    if new_status in ["member", "administrator"]:
        logger.info(f"Bot added to group: {chat_title} ({chat_id})")
        await db.save_bot_group(chat_id, chat_title)
    elif new_status in ["left", "kicked"]:
        logger.info(f"Bot removed from group: {chat_title} ({chat_id})")
        await db.remove_bot_group(chat_id)

@router.message(Command("reg_group"))
async def register_group_cmd(message: types.Message):
    """Guruhni qo'lda ro'yxatdan o'tkazish buyrug'i"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("❌ Bu buyruq faqat guruhlarda ishlaydi.")
        return
    
    await db.save_bot_group(message.chat.id, message.chat.title)
    await message.answer(f"✅ <b>Guruh ro'yxatga olindi!</b>\n\nNom: {message.chat.title}\nID: <code>{message.chat.id}</code>", parse_mode="HTML")
    logger.info(f"Manual group registration in {message.chat.id} by {message.from_user.id}")

@router.message(F.forward_from_chat)
async def discover_via_forward(message: types.Message):
    """Xabar transferi (forward) orqali guruhni ro'yxatga olish"""
    if message.from_user.id not in ADMIN_IDS: return
    
    chat = message.forward_from_chat
    if chat.type in ["group", "supergroup"]:
        await db.save_bot_group(chat.id, chat.title)
        await message.answer(
            f"✅ <b>Guruh topildi va saqlandi!</b>\n\n"
            f"Nomi: {chat.title}\n"
            f"ID: <code>{chat.id}</code>\n\n"
            f"<i>Eslatma: Bot ushbu guruhda admin bo'lishi shart, aks holda reklama yubora olmaydi.</i>", 
            parse_mode="HTML"
        )
        logger.info(f"Group {chat.id} discovered via forward from {message.from_user.id}")
    else:
        await message.answer("❌ Faqat guruh yoki superguruhlardan xabar forward qiling.")

@router.message(F.chat.type.in_(["group", "supergroup"]))
async def discover_group(message: types.Message):
    """Guruhdagi har qanday xabardan guruh ID sini saqlab qolish (Passiv kashfiyot)"""
    # logger.debug(f"Passive discovery in group: {message.chat.id}")
    await db.save_bot_group(message.chat.id, message.chat.title)
