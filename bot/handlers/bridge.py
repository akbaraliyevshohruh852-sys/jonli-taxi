from aiogram import Router, types, F, Bot
from core.config import GRABBER_SOURCES, VIP_GROUP_ID
import logging
import re
from core import database as db

logger = logging.getLogger(__name__)
router = Router()

# Default keywords (Fallbacks)
DEFAULT_LOCATIONS = [
    "namangan", "andijon", "fargona", "farg'ona", "toshkent", "tosh", 
    "margilon", "marg'ilon", "qo'qon", "qoqon", "chust", "pop", 
    "asaka", "shahrixon", "oltiariq", "rishton", "quva", "vodiy",
    "piter", "maskva", "moskva", "uychi", "uchqorgon", "uchqo'rg'on",
    "mingbuloq", "kosonsoy", "norin", "toraqo", "to'raqo", "yangiqorgon",
    "наманган", "андижон", "фаргона", "фарғона", "тошкент", "тош",
    "маргилон", "марғилон", "қуқон", "қўқон", "чуст", "поп",
    "асака", "шаҳрихон", "олтиариқ", "риштон", "қува", "водий",
    "питер", "масква", "москва", "уйчи", "учқоргон", "учқўрғон",
    "мингбулоқ", "косонсой", "норин", "тўрақўрғон", "янгиқўрғон", "тўрақорғон"
]

DEFAULT_INTENTS = [
    "odam", "kishi", "kisi", "pochta", "yuk", "dastavka", "dastuka", 
    "bor", "ketamiz", "ketaman", "yuraman", "yuramiz", "boramiz", 
    "qachon", "nechida", "nechi pul", "qancha", "taxi kerak", "taksi kerek",
    "taxsi kerak", "mashina kerak", "moshina kerak", "komplek", "komplekt",
    "kim ketadi", "bir kishi", "ikki kishi", "uch kishi", "tort kishi", "to'rt kishi",
    "одам", "киши", "киси", "почта", "юк", "даставка", "дастука",
    "бор", "кетамиз", "кетаман", "юраман", "юрамиз", "борамиз",
    "қачон", "нечида", "нечи пул", "қанча", "такси керак", "такси керек",
    "тахси керак", "машина керак", "мошина керак", "комплек", "комплект",
    "ким кетади", "бир киши", "икки киши", "уч киши", "тўрт киши", "торт киши"
]

DEFAULT_EXCLUDES = [
    "taxi bor", "taksi bor", "haydovchiman", "haydovchi man", "prava", "prawa",
    "pochta olamiz", "yuk olamiz", "pochta olaman", "yuk olaman", "pochta olyapmiz",
    "bo'sh joy", "bitta joy", "joy bor", "zapravka", "benzin", "gaz", "propan", "metan",
    "gentra", "jentra", "cobalt", "kobalt", "nexia", "neksiya", "lacetti", "lasetti", "spark", "matiz", "damas", "jentira",
    "odam olaman", "odam olamiz", "odam olib ketaman", "odam olyapmiz", "olamiz", "opketamiz",
    "yuramiz hozir", "boraman hozir", "tel kililar", "tel qiling", "tel qilila", 
    "aloqa", "murojaat", "daqiqadan keyin", "chiqamiz", "mashina bor", "moshina bor",
    "kamdamiz", "oldi bosh", "oldi bos", "ta kam", "ta qoldi", "ta qoldi", "avto ",
    "такси бор", "тахси бор", "ҳайдовчиман", "ҳаpайдовчи ман", "права",
    "почта оламиз", "юк оламиз", "почта оламан", "юк оламан", "почта оляпмиз",
    "бўш жой", "битта жой", "жой бор", "заправка", "бензин", "газ", "пропан", "метан",
    "жентра", "кобалт", "нексия", "ласетти", "спарк", "матиз", "дамас",
    "одам оламан", "одам оламиз", "одам олиб кетаман", "одам оляпмиз", "оламиз", "опкетамиз",
    "юрамиз ҳозир", "бораман ҳозир", "тел қилилар", "тел қилинг", "тел қилила",
    "алоқа", "мурожаат", "дақиқадан кейин", "чиқамиз", "машина бор", "мошина бор",
    "камдамиз", "олди бўш", "та кам", "та қолди", "авто "
]

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def bridge_grabber(message: types.Message, bot: Bot):
    """
    Ommaviy guruhdagi xabarlarni saralab faqat buyurtmalarni VIP guruhga yo'naltiradi.
    """
    # 1. Grabber yoqilganmi?
    grabber_on = await db.get_setting('grabber_enabled', '1')
    if grabber_on != '1':
        return

    # 2. Ushbu guruh kuzatiladimi?
    sources_str = await db.get_setting('grabber_sources', "")
    if sources_str:
        try:
            allowed_sources = [int(i.strip()) for i in sources_str.split(",") if i.strip()]
        except:
            allowed_sources = GRABBER_SOURCES
    else:
        allowed_sources = GRABBER_SOURCES

    if message.chat.id not in allowed_sources:
        return

    if not message.text:
        return

    text_lower = message.text.lower()
    user = message.from_user
    user_id = user.id
    
    # Aniqroq tahlil uchun bazadagi kalit so'zlarni olamiz
    loc_setting = await db.get_setting('grabber_locations', "")
    int_setting = await db.get_setting('grabber_intents', "")
    exc_setting = await db.get_setting('grabber_excludes', "")

    locations = [i.strip().lower() for i in loc_setting.split(",") if i.strip()] if loc_setting else DEFAULT_LOCATIONS
    intents = [i.strip().lower() for i in int_setting.split(",") if i.strip()] if int_setting else DEFAULT_INTENTS
    excludes = [i.strip().lower() for i in exc_setting.split(",") if i.strip()] if exc_setting else DEFAULT_EXCLUDES

    # Qoida 1: Xabar juda qisqa bo'lsa yubormaymiz
    if len(text_lower) < 3:
        # logger.info(f"Grabber: Xabar juda qisqa ({len(text_lower)})")
        return

    # Qoida 2: Havolalar yoki reklamalarni taqiqlash
    if message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link", "mention", "mention_name"]:
                logger.info(f"Grabber: Havola/reklama aniqlandi (Entity: {entity.type})")
                return
    
    if any(x in text_lower for x in ["t.me/", "http", "https:", "www.", "@"]):
        logger.info("Grabber: Havola matn ichida aniqlandi")
        return

    # Qoida 3: Haydovchi reklamasi bo'lmasligi shart
    is_driver_ad = any(word in text_lower for word in excludes)
    
    # Qo'shimcha REGEX tekshiruvlar (Haydovchilar uchun xos naqshlar)
    # 1. "2 ta kam", "1 ta qoldi", "2та кам" kabi naqshlar (Lotin va Kirill)
    if re.search(r'\d\s*(ta|та)?\s*(kam|кам|qoldi|қолди|бўш|буш|бош|бош)', text_lower):
        is_driver_ad = True
    
    # 2. Mashina nomeri (masalan: 01A777AA yoki 40P371GB)
    if re.search(r'\d{2}\s*[a-zа-я]\s*\d{3}\s*[a-zа-я]{2}', text_lower):
        is_driver_ad = True
    
    # 3. Mashina va joy birgalikda (masalan: "Jentra 2 ta joy")
    if any(car in text_lower for car in ["jentra", "gentra", "cobalt", "nexia", "spark"]) and \
       any(word in text_lower for word in ["joy", "жой", "kam", "кам", "бўш", "буш"]):
        is_driver_ad = True

    if is_driver_ad:
        logger.info(f"Grabber: Haydovchi reklamasi deb topildi (Matn: {text_lower[:50]}...)")
        return

    # Qoida 4: Manzil (Location) YOKI Maqsad (Intent) bo'lishi yetarli
    # Oldin ikkalasi ham bo'lishi shart edi, endi bittasi bo'lsa ham olamiz (faqat haydovchi bo'lmasa)
    
    has_location = any(word in text_lower for word in locations)
    has_intent = any(word in text_lower for word in intents)
    
    # Agar manzil nomi bo'lsa, bu 90% buyurtma bo'ladi (chunki haydovchilarni exclude qildik)
    if not (has_location or has_intent):
        logger.info(f"Grabber: Manzil ham, Maqsad ham topilmadi (Matn: {text_lower[:50]}...)")
        return

    logger.info(f"✅ Grabber: Buyurtma tasdiqlandi! (User: {user_id})")

    # Agar hamma qoidalardan o'tsa -> Bu yo'lovchi buyurtmasi
    user = message.from_user
    full_name = user.full_name
    user_id = user.id
    username = user.username
    
    # 1. VIP guruhlarga buyurtmani yo'naltirish
    vip_setting = await db.get_setting('vip_group_ids', str(VIP_GROUP_ID))
    vip_list = [int(i.strip()) for i in vip_setting.split(",") if i.strip().replace("-", "").isdigit()]
    
    if not vip_list:
        vip_list = [VIP_GROUP_ID]

    contact_url = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📱 Mijoz bilan bog'lanish", url=contact_url)]
    ])
    
    bridge_text = (
        "🚕 <b>GURUHIDAN YANGI BUYURTMA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>Xabar:</b>\n<i>{message.text}</i>\n\n"
        f"👤 <b>Yozgan:</b> {full_name}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "👆 Bog'lanish uchun pastdagi tugmani bosing."
    )
    
    forwarded_count = 0
    for v_id in vip_list:
        try:
            try:
                await bot.send_message(
                    chat_id=v_id,
                    text=bridge_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
                forwarded_count += 1
            except Exception as e:
                if "BUTTON_USER_PRIVACY_RESTRICTED" in str(e):
                    await bot.send_message(
                        chat_id=v_id,
                        text=bridge_text + "\n\n⚠️ <i>Foydalanuvchi maxfiylik sozlamalari tufayli tugma qo'shilmadi.</i>",
                        parse_mode="HTML"
                    )
                    forwarded_count += 1
                else:
                    logger.error(f"Error sending to VIP group {v_id}: {e}")
        except: pass

    if forwarded_count > 0:
        # 2. Original xabarni o'chirish
        deleted = False
        try:
            await message.delete()
            deleted = True
        except Exception as de:
            logger.warning(f"⚠️ Grabber: Xabarni o'chirishda xatolik (Group: {message.chat.id}): {de}")

        # 3. Klientga (yo'lovchiga) shaxsiy xabar yuborish
        try:
            client_msg = (
                "🏦 <b>JONLI TAXI | BUYURTMA QABUL QILINDI</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Sizning buyurtmangiz haydovchilar guruhiga yetkazildi. ✅\n\n"
                "✨ <b>Tez orada haydovchilarimiz Siz bilan bog'lanishadi.</b>\n\n"
                "<i>Ishonchingiz uchun rahmat!</i>"
            )
            await bot.send_message(chat_id=user_id, text=client_msg, parse_mode="HTML")
        except Exception as ce:
            logger.warning(f"⚠️ Grabber: Klientga shaxsiy xabar yuborib bo'lmadi: {ce}")
