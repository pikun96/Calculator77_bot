import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes, MessageHandler, filters
import re
import os
from flask import Flask
from threading import Thread

# === FLASK APP (RENDER KO ZINDA RAKHNE KE LIYE) ===
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def start_flask_thread():
    t = Thread(target=run_flask)
    t.start()

# === YEH BOT DO CHEEZON PAR CHALEGA ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

user_ids = set()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# === SAFE CALCULATION FUNCTION ===
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

# === USER TRACKING FUNCTION ===
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
    await update.message.reply_text("Namaste! Main ek inline calculator bot hoon.")

# === INLINE CALCULATOR HANDLER ===
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return
    user_id = update.inline_query.from_user.id
    if user_id not in user_ids:
        user_ids.add(user_id)
        logging.info(f"New user from inline: {user_id}. Total users: {len(user_ids)}")
    result_text = safe_eval(query)
    results = [InlineQueryResultArticle(id=query, title=f"Result: {result_text}", input_message_content=InputTextMessageContent(f"{query} = {result_text}"))]
    await update.inline_query.answer(results)

# === ADMIN COMMANDS ===
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id == ADMIN_ID:
        await update.message.reply_text("Admin Panel:\n/stats\n/broadcast <message>")
    else:
        await update.message.reply_text("Aap admin nahi hain.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id == ADMIN_ID:
        await update.message.reply_text(f"Total unique users: {len(user_ids)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id != ADMIN_ID:
        return
    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("Usage: /broadcast <your message>")
        return
    successful_sends = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            successful_sends += 1
        except Exception as e:
            logging.error(f"Failed to send to {uid}: {e}")
    await update.message.reply_text(f"Message sent to {successful_sends} users.")

def main() -> None:
    # Flask server ko alag thread me chalao
    start_flask_thread()

    # Bot ko chalao
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
