import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
from datetime import datetime
import os
from flask import Flask
import threading

# ===== আপনার তথ্য দিন =====
BOT_TOKEN = "8647557143:AAGTt9kbdYySkstBgqVxJLEDYjbNt8LBubo"
ADMIN_IDS = [7587190804, 8271698133]
CHANNEL_LINK = "https://t.me/your_channel"  # আপনার চ্যানেল লিংক দিন
# =========================

# Flask অ্যাপ
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 বট চলছে! টেলিগ্রামে /start দিন"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# লগিং
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ইউজার ডাটাবেজ
USERS_FILE = 'users.json'

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # ইউজার সেভ
    users = load_users()
    users[str(user.id)] = {
        'name': user.first_name,
        'username': user.username,
        'joined': str(datetime.now())
    }
    save_users(users)
    
    # বাটন
    keyboard = [
        [InlineKeyboardButton("📢 চ্যানেল", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🆘 হেল্প", callback_data='help')]
    ]
    
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 এডমিন", callback_data='admin')])
    
    await update.message.reply_text(
        f"👋 স্বাগতম {user.first_name}!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'help':
        await query.edit_message_text("""🆘 হেল্প
/start - শুরু
/users - মোট ইউজার (এডমিন)
/broadcast - প্রচার (এডমিন)""")
    
    elif query.data == 'admin':
        await query.edit_message_text("👑 এডমিন প্যানেল\n/users\n/broadcast")

async def users_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ অনুমতি নেই")
        return
    
    users = load_users()
    await update.message.reply_text(f"📊 মোট ইউজার: {len(users)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ অনুমতি নেই")
        return
    
    if not context.args:
        await update.message.reply_text("লিখুন: /broadcast মেসেজ")
        return
    
    users = load_users()
    msg = ' '.join(context.args)
    success = 0
    
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 {msg}")
            success += 1
        except:
            pass
    
    await update.message.reply_text(f"✅ পাঠানো হয়েছে: {success}/{len(users)}")

def main():
    print("🤖 বট চালু হচ্ছে...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("users", users_count))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(button))
    
    app.run_polling()

if __name__ == '__main__':
    main()
