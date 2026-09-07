import logging
import sys
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatMemberHandler, ContextTypes
from telegram.constants import ChatMemberStatus

# 1. Flask सर्वर सेटअप (Render 8080 पोर्ट आवश्यकता के लिए)
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Pro Max Anti-Premium Live Bot is running smoothly!"

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

# 2. एडवांस लॉगिंग सिस्टम सेटअप
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# आपका बॉट टोकन यहाँ अपडेट कर दिया गया है
BOT_TOKEN = "8385272773:AAE50Y6-TkZ9FjxXcDV50i6OP1NlpMy5aSE"

async def handle_live_entry_and_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pro Max सुरक्षा और स्पीड के साथ प्रीमियम यूजर्स को तुरंत बैन करने वाला फंक्शन"""
    try:
        chat_member_update = update.chat_member
        if not chat_member_update:
            return

        chat_id = chat_member_update.chat.id
        new_member = chat_member_update.new_chat_member
        user = new_member.user

        if not user:
            return

        # यदि यूजर चैनल या लाइव चैट से जुड़ा है
        if new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]:
            
            # ओनर या एडमिन को पूरी सुरक्षा प्रदान करना
            try:
                member_info = await context.bot.get_chat_member(chat_id, user.id)
                if member_info.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                    logger.info(f"[SAFE ADMIN] Owner/Admin allowed securely: {user.full_name} ({user.id})")
                    return
            except Exception as admin_err:
                logger.warning(f"Admin verification warning for {user.id}: {admin_err}")

            # कड़ाई से जांच: क्या यूजर टेलीग्राम प्रीमियम है?
            if getattr(user, "is_premium", False):
                try:
                    # 1. बिना एक पल गंवाए तुरंत बैन करें
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                    logger.warning(f"[PRO MAX BAN] Instant banned premium user: {user.full_name} (ID: {user.id})")

                except Exception as ban_err:
                    logger.error(f"Failed to execute ban for premium user {user.id}: {ban_err}")
            else:
                logger.info(f"[SAFE MEMBER] Normal non-premium user allowed: {user.full_name} ({user.id})")

    except Exception as e:
        logger.error(f"Critical unhandled exception in handle_live_entry_and_members: {e}", exc_info=True)

def main():
    # Render को लाइव रखने के लिए Flask बैकग्राउंड सर्वर शुरू करें
    keep_alive()
    logger.info("Flask keep-alive background thread initialized.")

    # टेलीग्राम बॉट एप्लीकेशन बिल्ड करें
    try:
        telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # केवल चैट मेंबर अपडेट्स सुनने के लिए हैंडलर रजिस्टर करें
        telegram_app.add_handler(ChatMemberHandler(handle_live_entry_and_members, ChatMemberHandler.CHAT_MEMBER))

        logger.info("Pro Max Instant Anti-Premium Bot is active and polling securely...")
        
        # बॉट को बिना रुके, बिना क्रैश हुए लगातार चलाने के लिए पोलिंग शुरू करें
        telegram_app.run_polling(
            allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER],
            drop_pending_updates=True
        )
    except Exception as e:
        logger.critical(f"Fatal error starting Telegram bot application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
    
