import logging
import sys
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ChatMemberHandler, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ChatMemberStatus

# 1. Flask सर्वर सेटअप (Render 8080 पोर्ट आवश्यकता के लिए)
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Ultra Pro Max Anti-Premium Live Bot is running smoothly!"

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

# 2. एडवांस्ड लॉगिंग सिस्टम सेटअप
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# बॉट टोकन
BOT_TOKEN = "8385272773:AAE50Y6-TkZ9FjxXcDV50i6OP1NlpMy5aSE"

# ग्लोबल पावर स्टेटस (True = चालू, False = बंद)
BOT_ACTIVE_STATUS = True

# --- /start कमांड (Hinglish मैसेज और बटन्स के साथ) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if BOT_ACTIVE_STATUS:
            status_text = "🟢 **Bot filhal ACTIVE hai** aur premium users ko turant ban kar raha hai."
        else:
            status_text = "🔴 **Bot filhal STOPPED (band) hai** aur abhi koi action nahi le raha hai."
        
        # क्लिक करने योग्य बटन बनाना
        keyboard = [
            [
                InlineKeyboardButton("🟢 Active Bot", callback_data="btn_active"),
                InlineKeyboardButton("🔴 Stop Bot", callback_data="btn_stop")
            ],
            [
                InlineKeyboardButton("📊 Check Status", callback_data="btn_stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🤖 **Ultra Pro Max Protection Control Panel**\n\n"
            f"{status_text}\n\n"
            f"Neeche diye gaye buttons se ise control karo:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in start_command: {e}")

# --- बटन क्लिक हैंडलर ---
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE_STATUS
    query = update.callback_query
    try:
        await query.answer()

        if query.data == "btn_active":
            BOT_ACTIVE_STATUS = True
            logger.info("🟢 Bot activated via inline button.")
            status_text = "🟢 **Bot filhal ACTIVE hai** aur premium users ko turant ban kar raha hai."
            
            keyboard = [
                [InlineKeyboardButton("🟢 Active Bot", callback_data="btn_active"), InlineKeyboardButton("🔴 Stop Bot", callback_data="btn_stop")],
                [InlineKeyboardButton("📊 Check Status", callback_data="btn_stats")]
            ]
            await query.edit_message_text(
                text=f"🤖 **Ultra Pro Max Protection Control Panel**\n\n{status_text}\n\nNeeche diye gaye buttons se ise control karo:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

        elif query.data == "btn_stop":
            BOT_ACTIVE_STATUS = False
            logger.warning("⚠️ Bot stopped via inline button.")
            status_text = "🔴 **Bot filhal STOPPED (band) hai** aur abhi koi action nahi le raha hai."
            
            keyboard = [
                [InlineKeyboardButton("🟢 Active Bot", callback_data="btn_active"), InlineKeyboardButton("🔴 Stop Bot", callback_data="btn_stop")],
                [InlineKeyboardButton("📊 Check Status", callback_data="btn_stats")]
            ]
            await query.edit_message_text(
                text=f"🤖 **Ultra Pro Max Protection Control Panel**\n\n{status_text}\n\nNeeche diye gaye buttons se ise control karo:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

        elif query.data == "btn_stats":
            current_state = "🟢 Active (Chalu)" if BOT_ACTIVE_STATUS else "🔴 Stopped (Band)"
            await query.answer(f"Current Status: {current_state}", show_alert=True)

    except Exception as e:
        logger.error(f"Error in button_callback_handler: {e}")

# --- /stats कमांड ---
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        status_text = "🟢 Active (Chalu)" if BOT_ACTIVE_STATUS else "🔴 Stopped (Band)"
        await update.message.reply_text(f"✅ Bot status: {status_text}. Channel aur live stream par poori nazar rakhi ja rahi hai.")
    except Exception as e:
        logger.error(f"Error in stats_command: {e}")

# --- मुख्य एंटी-प्रीमियम और लाइव स्ट्रीम प्रोटेक्शन लॉजिक ---
async def handle_live_entry_and_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not BOT_ACTIVE_STATUS:
            return

        chat_member_update = update.chat_member
        if not chat_member_update:
            return

        chat_id = chat_member_update.chat.id
        new_member = chat_member_update.new_chat_member
        if not new_member:
            return

        user = new_member.user
        if not user:
            return

        if new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]:
            
            try:
                member_info = await context.bot.get_chat_member(chat_id, user.id)
                if member_info and member_info.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                    logger.info(f"[SAFE ADMIN] Owner/Admin allowed securely: {user.full_name} ({user.id})")
                    return
            except Exception as admin_err:
                logger.warning(f"Admin check warning for {user.id}: {admin_err}")

            if getattr(user, "is_premium", False):
                try:
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                    logger.warning(f"[PRO MAX BAN] Instantly banned premium user: {user.full_name} (ID: {user.id})")
                except Exception as ban_err:
                    logger.error(f"Failed to ban premium user {user.id}: {ban_err}")
            else:
                logger.info(f"[SAFE MEMBER] Normal non-premium user allowed: {user.full_name} ({user.id})")

    except Exception as e:
        logger.error(f"Critical exception in handle_live_entry_and_members: {e}", exc_info=True)

def main():
    keep_alive()
    logger.info("Flask keep-alive background thread initialized successfully.")

    try:
        telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        telegram_app.add_handler(CommandHandler("start", start_command))
        telegram_app.add_handler(CommandHandler("stats", stats_command))
        telegram_app.add_handler(CallbackQueryHandler(button_callback_handler))
        telegram_app.add_handler(ChatMemberHandler(handle_live_entry_and_members, ChatMemberHandler.CHAT_MEMBER))

        logger.info("Ultra Pro Max Anti-Premium Bot is active and polling securely...")
        
        telegram_app.run_polling(
            allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER, Update.MESSAGE, Update.CALLBACK_QUERY],
            drop_pending_updates=True
        )
    except Exception as e:
        logger.critical(f"Fatal error starting Telegram bot application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
    
