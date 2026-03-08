import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
from datetime import datetime
from flask import Flask
import threading

# ===== আপনার তথ্য =====
BOT_TOKEN = "8647557143:AAGTt9kbdYySkstBgqVxJLEDYjbNt8LBubo"
ADMIN_IDS = [7587190804, 8271698133]
CHANNEL_LINK = "https://t.me/your_channel"  # আপনার চ্যানেল লিংক দিন
# ====================

# Flask সার্ভার (Rendar এর জন্য)
app = Flask(__name__)

@app.route('/')
def home():
    return "বট চলছে! টেলিগ্রামে /start দিন"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Flask আলাদা থ্রেডে চালান
threading.Thread(target=run_flask, daemon=True).start()

# লগিং
logging.basicConfig(level=logging.INFO)

# ইউজার স্টোর
users_file = 'users.json'

def get_users():
    try:
        with open(users_file, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(users_file, 'w') as f:
        json.dump(users, f)

# স্টার্ট কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # ইউজার সেভ
    users = get_users()
    users[str(user.id)] = {
        'name': user.first_name,
        'username': user.username,
        'time': str(datetime.now())
    }
    save_users(users)
    
    # বাটন তৈরি
    buttons = [
        [InlineKeyboardButton("📢 চ্যানেল", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🆘 হেল্প", callback_data='help')]
    ]
    
    # এডমিন হলে
    if user.id in ADMIN_IDS:
        buttons.append([InlineKeyboardButton("👑 এডমিন", callback_data='admin')])
    
    await update.message.reply_text(
        f"👋 হ্যালো {user.first_name}!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# বাটন ক্লিক
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'help':
        await query.edit_message_text(
            "🔰 **হেল্প**\n\n"
            "/start - শুরু\n"
            "/users - মোট ইউজার (এডমিন)\n"
            "/broadcast - বার্তা পাঠান (এডমิน)"
        )
    elif query.data == 'admin':
        await query.edit_message_text(
            "👑 **এডমিন মেনু**\n\n"
            "/users - ইউজার সংখ্যা\n"
            "/broadcast মেসেজ - সবাইকে পাঠান"
        )

# ইউজার সংখ্যা
async def total_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ অনুমতি নেই")
        return
    
    users = get_users()
    await update.message.reply_text(f"📊 মোট ইউজার: {len(users)}")

# ব্রডকাস্ট
async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ অনুমতি নেই")
        return
    
    if not context.args:
        await update.message.reply_text("📝 ব্যবহার: /broadcast আপনার বার্তা")
        return
    
    users = get_users()
    msg = ' '.join(context.args)
    
    status = await update.message.reply_text(f"পাঠানো হচ্ছে... 0/{len(users)}")
    
    success = 0
    for uid in users:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"📢 {msg}"
            )
            success += 1
        except:
            pass
    
    await status.edit_text(f"✅ সম্পন্ন: {success}/{len(users)}")

# মেইন ফাংশন
def main():
    print("🤖 বট চালু হচ্ছে...")
    print(f"👑 এডমিন: {ADMIN_IDS}")
    
    # বট তৈরি
    app = Application.builder().token(BOT_TOKEN).build()
    
    # কমান্ড যোগ করুন
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("users", total_users))
    app.add_handler(CommandHandler("broadcast", send_broadcast))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("✅ বট রেডি! টেলিগ্রামে /start দিন")
    
    # বট চালান
    app.run_polling()

if __name__ == "__main__":
    main()
