import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes, MessageHandler, filters
import re
import os

# === YEH BOT DO CHEEZON PAR CHALEGA ===
# 1. BOT_TOKEN: BotFather se mila hua token
# 2. ADMIN_ID: Aapki apni Telegram User ID
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# User IDs ko store karne ke liye (jab bot restart hoga to yeh reset ho jayega)
user_ids = set()

# Logging set up karna
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# === SAFE CALCULATION KE LIYE FUNCTION ===
def safe_eval(expression):
    if not re.match(r"^[\d\s\+\-\*\/\(\)\.]*$", expression):
        return "Invalid Input"
    try:
        if any(keyword in expression for keyword in ["__", "import", "os", "eval", "exec"]):
            return "Unsafe Input"
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception:
        return "Error"

# === USER ID STORE KARNE KE LIYE FUNCTION ===
async def track_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_ids:
        user_ids.add(user_id)
        logging.info(f"New user: {user_id}. Total users: {len(user_ids)}")

# === START COMMAND ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_ids:
        user_ids.add(user_id)
        logging.info(f"New user from start: {user_id}. Total users: {len(user_ids)}")
    
    await update.message.reply_text(
        "Namaste! Main ek inline calculator bot hoon.\n"
        "Kisi bhi chat me mera username likho aur calculation karo.\n\n"
        "Agar aap admin hain, to /admin command ka istemal karein."
    )

# === INLINE CALCULATOR HANDLER ===
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    # User ko track karna jab wo inline query use kare
    user_id = update.inline_query.from_user.id
    if user_id not in user_ids:
        user_ids.add(user_id)
        logging.info(f"New user from inline: {user_id}. Total users: {len(user_ids)}")

    result_text = safe_eval(query)
    results = [
        InlineQueryResultArticle(
            id=query,
            title=f"Result: {result_text}",
            input_message_content=InputTextMessageContent(f"{query} = {result_text}"),
            description=f"'{query}' ka result bhejne ke liye click karein",
        )
    ]
    await update.inline_query.answer(results)

# === ADMIN COMMANDS ===
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "Admin Panel:\n"
            "/stats - Bot ke total users dekhein.\n"
            "/broadcast <message> - Sabhi users ko message bhejein."
        )
    else:
        await update.message.reply_text("Aap admin nahi hain.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text(f"Total unique users: {len(user_ids)}")
    else:
        await update.message.reply_text("Yeh command sirf admin ke liye hai.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Yeh command sirf admin ke liye hai.")
        return

    message_to_broadcast = " ".join(context.args)
    if not message_to_broadcast:
        await update.message.reply_text("Broadcast karne ke liye message likhein. Example: /broadcast Hello everyone!")
        return

    successful_sends = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message_to_broadcast)
            successful_sends += 1
        except Exception as e:
            logging.error(f"User {uid} ko message nahi bhej paya: {e}")
    
    await update.message.reply_text(f"Message {successful_sends} users ko bhej diya gaya hai.")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    
    application.add_handler(InlineQueryHandler(inline_query))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_users))

    application.run_polling()

if __name__ == "__main__":
    main()
