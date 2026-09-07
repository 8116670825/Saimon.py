import logging
import sys
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ChatMemberHandler,
    ContextTypes,
)
from telegram.constants import ChatMemberStatus

# ==========================================
# CONFIGURATION
# ==========================================
ALLOWED_CHAT_ID: int = -1002982567511
BOT_TOKEN: str = "8385272773:AAE50Y6-TkZ9FjxXcDV50i6OP1NlpMy5aSE"
PORT: int = int(os.environ.get("PORT", 8080))

# अपने Render का लाइव URL यहाँ डालें (बिना आखिरी स्लैश के)
WEBHOOK_URL: str = "https://newtelegram-4aor.onrender.com"

# ==========================================
# LOGGING
# ==========================================
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("EnterpriseSentinel")

# ==========================================
# FLASK & TELEGRAM SETUP
# ==========================================
flask_app = Flask(__name__)

# टेलीग्राम एप्लीकेशन बिल्ड करें
application = ApplicationBuilder().token(BOT_TOKEN).build()

@flask_app.route('/')
def health_check():
    return "🚀 Enterprise Sentinel Webhook Operational", 200

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """ टेलीग्राम से आने वाले अपडेट्स को प्रोसेस करने के लिए """
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        
        import asyncio
        asyncio.run(application.process_update(update))
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return "Error", 500

# ==========================================
# HANDLER: चेक करेगा कि एक्सेप्ट होने के बाद यूजर प्रीमियम है या नहीं
# ==========================================
async def is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR}
    except Exception:
        return False

async def process_chat_member_transition(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        member_update = update.chat_member
        if not member_update or not member_update.new_chat_member:
            return

        chat_id = member_update.chat.id
        if chat_id != ALLOWED_CHAT_ID:
            return

        state = member_update.new_chat_member
        user = state.user

        # अगर यूजर चैनल में शामिल हो गया है (यानी रिक्वेस्ट एक्सेप्ट हो चुकी है)
        if not user or state.status not in {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED}:
            return

        # अगर वह एडमिन है, तो उसे छोड़ दें
        if await is_admin(context, chat_id, user.id):
            return

        # चेक करें कि क्या वह प्रीमियम यूजर है
        if getattr(user, "is_premium", False):
            # अगर गलती से प्रीमियम यूजर एक्सेप्ट हो गया है, तो उसे तुरंत बैन कर दें
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
            logger.warning(f"[AUTO-PURGED] Accepted premium user banned -> ID: {user.id}, Name: {user.first_name}")
        else:
            logger.info(f"[ALLOWED] Non-premium user joined safely -> ID: {user.id}")

    except Exception as e:
        logger.error(f"Error in member transition: {e}")

# केवल मेंबर ट्रांजिट हैंडलर जोड़ें ताकि एक्सेप्ट होने पर यह काम करे
application.add_handler(ChatMemberHandler(process_chat_member_transition, ChatMemberHandler.CHAT_MEMBER))

# ==========================================
# MAIN ENTRYPOINT
# ==========================================
async def setup_webhook():
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    logger.info(f"Webhook set successfully to {WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_webhook())
    
    logger.info("Starting Flask Server...")
    flask_app.run(host="0.0.0.0", port=PORT, debug=False)
    
