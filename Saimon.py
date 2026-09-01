import logging
import sys
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from telegram.constants import ChatMemberStatus

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Join Request Anti-Premium Bot is active and running!"

@flask_app.route('/healthz')
def health_check():
    return "OK", 200

def run_flask():
    try:
        flask_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask server fatal error: {e}", file=sys.stderr)

def keep_alive():
    try:
        t = Thread(target=run_flask, daemon=True)
        t.start()
    except Exception as e:
        print(f"Thread error: {e}", file=sys.stderr)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8716958222:AAHgYYcicw1KQUYewlOJPF0RHaFy9CGCct0"
OWNER_USER_ID = 8064395854  

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        join_request = update.chat_join_request
        if not join_request:
            return

        chat_id = join_request.chat.id
        user = join_request.from_user

        if not user:
            return

        if user.id == OWNER_USER_ID:
            logger.info(f"[SAFE OWNER] Bot Owner join request allowed safely: {user.full_name} ({user.id})")
            await join_request.approve()
            return

        if getattr(user, "is_premium", False):
            try:
                await join_request.approve()
                await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                logger.warning(f"[ULTRA FAST BAN] Approved and instantly banned premium user: {user.full_name} (ID: {user.id})")
            except Exception as ban_err:
                logger.error(f"Failed to execute join request ban for premium user {user.id}: {ban_err}")
        else:
            logger.info(f"[SAFE USER] Approving normal non-premium user: {user.full_name} ({user.id})")
            await join_request.approve()

    except Exception as e:
        logger.error(f"Critical unhandled exception in handle_join_request: {e}", exc_info=True)

def main():
    keep_alive()
    logger.info("Flask keep-alive background thread initialized.")

    try:
        telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
        telegram_app.add_handler(ChatJoinRequestHandler(handle_join_request))

        logger.info("Bot is active and polling securely...")
        
        telegram_app.run_polling(
            allowed_updates=[Update.CHAT_JOIN_REQUEST],
            drop_pending_updates=True
        )
    except Exception as e:
        logger.critical(f"Fatal error starting Telegram bot application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
  
