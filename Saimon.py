import os
import sys
import logging
import time
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from telegram.constants import ChatMemberStatus
from telegram.error import NetworkError, TimedOut, Conflict

# लॉगिंग सेटअप
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# फ्लास्क हेल्थ-चेक सर्वर (रेंडर के लिए)
flask_app = Flask(__name__)

@flask_app.route('/')
def home() -> str:
    return "Bot is active and running smoothly!", 200

@flask_app.route('/healthz')
def health_check() -> str:
    return "OK", 200

def run_flask() -> None:
    try:
        port = int(os.environ.get("PORT", 10000))
        flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")

def keep_alive() -> None:
    try:
        thread = Thread(target=run_flask, daemon=True)
        thread.start()
    except Exception as e:
        logger.error(f"Keep-alive thread error: {e}")

# क्रेडेंशियल्स
BOT_TOKEN = "8716958222:AAGwJB4bjQhcexbEo_rEdKAeZ-CwBwQzMok"
OWNER_USER_ID = 8064395854  

checked_users_cache = set()

async def live_stream_instant_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if not update or not update.chat_member:
            return

        chat_member_update = update.chat_member
        chat = chat_member_update.chat
        new_member = chat_member_update.new_chat_member
        
        if not chat or not new_member or not new_member.user:
            return

        user = new_member.user
        user_id = user.id

        if user_id == OWNER_USER_ID or user_id in checked_users_cache:
            return

        checked_users_cache.add(user_id)

        status = new_member.status
        if status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return

        if getattr(user, "is_premium", False):
            try:
                await context.bot.ban_chat_member(chat_id=chat.id, user_id=user_id)
                logger.info(f"Instant-banned premium user ID: {user_id} from chat ID: {chat.id}")
            except Exception as ban_error:
                logger.error(f"Could not ban user {user_id}: {ban_error}")

    except Exception as e:
        logger.error(f"Error inside live_stream_instant_ban: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """लॉग्स में एरर को दबाने और क्रैश रोकने के लिए स्पेशल एरर हैंडलर"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    keep_alive()
    time.sleep(1)

    logger.info("Starting Telegram Bot Application...")
    
    while True:
        try:
            telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
            
            # हैंडलर्स जोड़ें
            telegram_app.add_handler(ChatMemberHandler(live_stream_instant_ban, ChatMemberHandler.CHAT_MEMBER))
            
            # एरर हैंडलर रजिस्टर किया ताकि स्क्रीनशॉट वाला 'No error handlers are registered' एरर कभी न आए
            telegram_app.add_error_handler(error_handler)
            
            telegram_app.run_polling(
                allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER],
                drop_pending_updates=True,
                close_loop=False
            )
        except Conflict:
            logger.warning("Conflict error: Another instance of this bot is running elsewhere! Pausing for 15 seconds...")
            time.sleep(15)
        except (NetworkError, TimedOut):
            logger.warning("Network connection lost. Reconnecting in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            logger.critical(f"Critical error: {e}. Restarting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
    
