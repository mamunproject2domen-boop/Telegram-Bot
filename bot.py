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

# Flask আলাদা থ্রেডে চালু করুন
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# লগিং
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ইউজার ডাটাবেজ
USERS_FILE = 'users.json'

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {}

def save_users(users):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

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
    
    # বাটন তৈরি
    keyboard = [
        [InlineKeyboardButton("📢 জয়েন্ট আপডেট চ্যানেল", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🆘 হেল্প", callback_data='help')]
    ]
    
    # এডমিন হলে বাটন দেখান
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 এডমিন প্যানেল", callback_data='admin')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 স্বাগতম {user.first_name}!\n\nআমার বটে আপনাকে স্বাগতম। নিচের বাটনগুলো ব্যবহার করুন।",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'help':
        await query.edit_message_text("""
🆘 **হেল্প সেকশন**

**কমান্ডসমূহ:**
• /start - বট চালু করুন
• /users - মোট ইউজার সংখ্যা (শুধু এডমিন)
• /broadcast - বার্তা পাঠান (শুধু এডমিন)

**বাটন:**
• জয়েন্ট আপডেট চ্যানেল - চ্যানেলে জয়েন করুন
• হেল্প - এই মেসেজ দেখুন
""", parse_mode='Markdown')
    
    elif query.data == 'admin':
        await query.edit_message_text("""
👑 **এডমিন প্যানেল**

**আপনার কমান্ড:**
• /users - মোট ইউজার দেখুন
• /broadcast [বার্তা] - সবাইকে বার্তা পাঠান

**উদাহরণ:**
/broadcast সবাইকে অভিনন্দন
""", parse_mode='Markdown')

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ এই কমান্ড শুধুমাত্র এডমিনদের জন্য!")
        return
    
    users = load_users()
    total = len(users)
    
    # আজকে জয়েন করেছে কতজন
    today = datetime.now().date()
    today_count = 0
    for data in users.values():
        try:
            joined = datetime.fromisoformat(data.get('joined', '')).date()
            if joined == today:
                today_count += 1
        except:
            pass
    
    text = f"📊 **ইউজার পরিসংখ্যান**\n\n"
    text += f"• মোট ইউজার: {total}\n"
    text += f"• আজকের জয়েন: {today_count}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ এই কমান্ড শুধুমাত্র এডমিনদের জন্য!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "⚠️ ** ব্যবহার নিয়ম:**\n"
            "/broadcast আপনার বার্তা\n\n"
            "উদাহরণ: /broadcast সবাইকে শুভ সকাল"
        )
        return
    
    users = load_users()
    if not users:
        await update.message.reply_text("❌ কোন ইউজার নেই!")
        return
    
    message = ' '.join(context.args)
    total = len(users)
    
    status = await update.message.reply_text(f"📤 বার্তা পাঠানো হচ্ছে... 0/{total}")
    
    success = 0
    failed = 0
    
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"📢 **ব্রডকাস্ট বার্তা**\n\n{message}",
                parse_mode='Markdown'
            )
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send to {user_id}: {e}")
        
        # প্রতি ১০ জন পর পর আপডেট
        if (success + failed) % 10 == 0:
            await status.edit_text(f"📤 পাঠানো হচ্ছে... {success + failed}/{total}")
        
        # একটু বিরতি
        import asyncio
        await asyncio.sleep(0.05)
    
    await status.edit_text(
        f"✅ **সম্পন্ন!**\n\n"
        f"📊 ফলাফল:\n"
        f"• সফল: {success}\n"
        f"• ব্যর্থ: {failed}\n"
        f"• মোট: {total}"
    )

def main():
    """মেইন ফাংশন"""
    print("\n" + "="*50)
    print("🤖 টেলিগ্রাম বট চালু হচ্ছে...")
    print("="*50)
    print(f"👑 এডমিন আইডি: {ADMIN_IDS}")
    print(f"📡 Flask সার্ভার: চালু (পোর্ট 8080)")
    print("="*50)
    
    # বট অ্যাপ্লিকেশন তৈরি
    application = Application.builder().token(BOT_TOKEN).build()
    
    # হ্যান্ডলার যোগ করুন
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ বট চালু হয়েছে! টেলিগ্রামে /start দিন")
    print("="*50 + "\n")
    
    # বট চালু করুন
    application.run_polling()

if __name__ == '__main__':
    main()
