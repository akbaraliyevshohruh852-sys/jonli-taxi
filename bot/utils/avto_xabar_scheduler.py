from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, enums
from core import database as db
from core.config import API_ID, API_HASH, ADMIN_IDS
import asyncio
import logging
import random

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()
_bot_instance = None # Store globally after initialization

async def send_ad_message_job(user_id: int):
    global _bot_instance
    from datetime import datetime
    ad = await db.get_ad_message(user_id)
    if not ad or not ad['is_active']:
        return
    
    # Expiration check
    if ad['expires_at']:
        exp = ad['expires_at']
        if isinstance(exp, str):
            try:
                exp = datetime.strptime(exp, '%Y-%m-%d %H:%M:%S.%f')
            except:
                try:
                    exp = datetime.strptime(exp, '%Y-%m-%d %H:%M:%S')
                except:
                    pass
        
        if isinstance(exp, datetime) and exp < datetime.now():
            logger.info(f"Ad for user {user_id} has expired. Deactivating.")
            await db._execute("UPDATE ad_messages SET is_active = 0 WHERE user_id = ?", (user_id,), commit=True)
            return
    
    # Get all worker accounts (those added by admins)
    all_workers = []
    # Fetching accounts for all admins to have a pool of workers
    for admin_id in ADMIN_IDS:
        accounts = await db.get_accounts(admin_id)
        if accounts:
            all_workers.extend(accounts)
            
    if not all_workers:
        logger.info(f"No worker accounts found in system. Falling back to main Bot for user {user_id}")
        if not _bot_instance:
            logger.warning("Bot instance not available for fallback.")
            return
            
        # Get groups where the bot is a member
        bot_groups = await db.get_bot_groups()
        if not bot_groups:
            logger.warning("Bot is not in any tracked groups. No messages sent via Fallback.")
            return
            
        logger.info(f"Bot Fallback: Sending ad {user_id} to {len(bot_groups)} groups: {bot_groups}")
        for g_id in bot_groups:
            try:
                logger.info(f"Attempting to send ad {user_id} to group {g_id} via Bot API")
                if ad['photo_id']:
                    await _bot_instance.send_photo(g_id, ad['photo_id'], caption=ad['text'], parse_mode="HTML")
                else:
                    await _bot_instance.send_message(g_id, ad['text'], parse_mode="HTML")
                logger.info(f"✅ Success: Ad {user_id} sent to group {g_id}")
                await asyncio.sleep(60) # Delay for Bot to avoid flood
            except Exception as e:
                logger.error(f"❌ Failed: Ad {user_id} NOT sent to group {g_id}. Error: {e}")
        
        await db._execute("UPDATE ad_messages SET last_sent = ? WHERE user_id = ?", (datetime.now(), user_id), commit=True)
        return

    # Select a random worker account to distribute load
    worker = random.choice(all_workers)

    try:
        import os
        session_path = os.path.join(os.getcwd(), "sessions", worker['phone'].replace("+", ""))
        
        async with Client(
            name=session_path,
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=worker['session_string']
        ) as app:
            # Check if admin set a manual list or wants 'all'
            groups_setting = await db.get_setting('avto_xabar_groups', 'all')
            group_ids = []
            
            if groups_setting == 'all':
                async for dialog in app.get_dialogs():
                    if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                        group_ids.append(dialog.chat.id)
            else:
                # Manual list from setting
                try:
                    group_ids = [int(i.strip()) for i in groups_setting.split(",") if i.strip()]
                except:
                    logger.error(f"Invalid avto_xabar_groups setting: {groups_setting}")
                    return
            
            if not group_ids:
                logger.warning(f"Worker {worker['phone']} is not in any groups.")
                return

            for g_id in group_ids:
                try:
                    if ad['photo_id']:
                        await app.send_photo(g_id, ad['photo_id'], caption=ad['text'])
                    else:
                        await app.send_message(g_id, ad['text'])
                    
                    await asyncio.sleep(3) # Delay between groups
                except Exception as e:
                    logger.error(f"Error sending to {g_id}: {e}")
                    
            # Record last sent time
            from datetime import datetime
            await db._execute("UPDATE ad_messages SET last_sent = ? WHERE user_id = ?", (datetime.now(), user_id), commit=True)
            
    except Exception as e:
        logger.error(f"Worker account error {worker['phone']}: {e}")

def schedule_ad_task(user_id: int, interval_minutes: int):
    from datetime import datetime
    logger.info(f"Scheduling ad task for user {user_id} with interval {interval_minutes}m")
    scheduler.add_job(
        send_ad_message_job,
        'interval',
        minutes=interval_minutes,
        args=[user_id],
        id=f"ad_{user_id}",
        replace_existing=True,
        next_run_time=datetime.now()
    )

async def start_all_ads(bot_instance=None):
    if bot_instance:
        global _bot_instance
        _bot_instance = bot_instance
        
    ads = await db.get_all_active_ads()
    for ad in ads:
        schedule_ad_task(ad['user_id'], ad['interval_min'])
    if not scheduler.running:
        scheduler.start()
        logger.info("Avto Xabar scheduler started with Bot Fallback support")
