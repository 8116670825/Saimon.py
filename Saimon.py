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
    return "Zero-Error Production Bot is running successfully!"

def run_flask():
    try:
        flask_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask background service error: {e}", file=sys.stderr)

def keep_alive():
    try:
        t = Thread(target=run_flask, daemon=True)
        t.start()
    except Exception as e:
        print(f"Thread initialization error: {e}", file=sys.stderr)

# 2. एडवांस्ड लॉगिंग सिस्टम
logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ZeroErrorBot")

# बॉट टोकन
BOT_TOKEN = "8385272773:AAE50Y6-TkZ9FjxXcDV50i6OP1NlpMy5aSE"

# ग्लोबल पावर स्टेटस
BOT_ACTIVE_STATUS = True

# --- /start कमांड ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if BOT_ACTIVE_STATUS:
            status_text = "🟢 **Bot STATUS: ULTRA ACTIVE** (Protection Enabled)"
        else:
            status_text = "🔴 **Bot STATUS: STOPPED** (Currently paused)"
        
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

        if update and update.effective_message:
            await update.effective_message.reply_text(
                f"🤖 **Production Control Panel**\n\n{status_text}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Exception in start_command: {e}", exc_info=True)

# --- बटन क्लिक हैंडलर ---
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE_STATUS
    query = update.callback_query
    if not query:
        return

    try:
        await query.answer()

        if query.data == "btn_active":
            BOT_ACTIVE_STATUS = True
            status_text = "🟢 **Bot STATUS: ULTRA ACTIVE** (Protection Enabled)"
            keyboard = [
                [InlineKeyboardButton("🟢 Active Bot", callback_data="btn_active"), InlineKeyboardButton("🔴 Stop Bot", callback_data="btn_stop")],
                [InlineKeyboardButton("📊 Check Status", callback_data="btn_stats")]
            ]
            if query.message:
                await query.edit_message_text(
                    text=f"🤖 **Production Control Panel**\n\n{status_text}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )

        elif query.data == "btn_stop":
            BOT_ACTIVE_STATUS = False
            status_text = "🔴 **Bot STATUS: STOPPED** (Currently paused)"
            keyboard = [
                [InlineKeyboardButton("🟢 Active Bot", callback_data="btn_active"), InlineKeyboardButton("🔴 Stop Bot", callback_data="btn_stop")],
                [InlineKeyboardButton("📊 Check Status", callback_data="btn_stats")]
            ]
            if query.message:
                await query.edit_message_text(
                    text=f"🤖 **Production Control Panel**\n\n{status_text}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )

        elif query.data == "btn_stats":
            current_state = "🟢 Active & Protecting" if BOT_ACTIVE_STATUS else "🔴 Stopped"
            await query.answer(f"System State: {current_state}", show_alert=True)

    except Exception as e:
        logger.error(f"Exception in button_callback_handler: {e}", exc_info=True)

# --- /stats कमांड ---
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        status_text = "🟢 Active" if BOT_ACTIVE_STATUS else "🔴 Stopped"
        if update and update.effective_message:
            await update.effective_message.reply_text(f"⚡ Core Status: {status_text} | Error-Free Protection Active")
    except Exception as e:
        logger.error(f"Exception in stats_command: {e}", exc_info=True)

# --- इंस्टेंट मेंबर और लाइव स्ट्रीम प्यूरिफिकेशन लॉजिक (Fully Safe) ---
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
        if not user or not user.id:
            return

        # सुरक्षित स्टेटस चेक
        valid_statuses = {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED, ChatMemberStatus.ADMINISTRATOR}
        if new_member.status in valid_statuses:
            
            try:
                # बॉट परमिशन क्रैश से बचने के लिए try-except ब्लॉक के अंदर API कॉल
                member_info = await context.bot.get_chat_member(chat_id, user.id)
                if not member_info:
                    return

                admin_statuses = {ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR}
                if member_info.status in admin_statuses:
                    return

                target_user = getattr(member_info, "user", None)
                is_premium_target = getattr(target_user, "is_premium", False) if target_user else False
                is_premium_local = getattr(user, "is_premium", False)
                
                is_user_premium = is_premium_target or is_premium_local

                if is_user_premium:
                    try:
                        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                        logger.warning(f"[INSTANT-BAN] Successfully removed Premium user -> ID: {user.id}")
                    except Exception as ban_err:
                        logger.warning(f"Could not ban user (Check Bot Admin Permissions): {ban_err}")
                else:
                    logger.info(f"[SAFE-USER] Allowed normal user -> ID: {user.id}")

            except Exception as api_sub_err:
                logger.warning(f"Sub-level API warning for user {user.id}: {api_sub_err}")

    except Exception as e:
        logger.error(f"Critical exception in handle_live_entry_and_members: {e}", exc_info=True)

def main():
    keep_alive()
    logger.info("Background keep-alive system successfully booted.")

    try:
        telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        telegram_app.add_handler(CommandHandler("start", start_command))
        telegram_app.add_handler(CommandHandler("stats", stats_command))
        telegram_app.add_handler(CallbackQueryHandler(button_callback_handler))
        
        # ChatMemberHandler के साथ सही chat_member_types कॉन्स्टेंट जोड़ना
        telegram_app.add_handler(ChatMemberHandler(handle_live_entry_and_members, ChatMemberHandler.CHAT_MEMBER))

        logger.info("Bot polling engine initiated successfully...")
        
        telegram_app.run_polling(
            allowed_updates=[Update.CHAT_MEMBER, Update.MY_CHAT_MEMBER, Update.MESSAGE, Update.CALLBACK_QUERY],
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        logger.critical(f"Fatal crash prevented in main loop: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
    
