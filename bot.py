import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import json
from datetime import datetime
import asyncio
import os

# কনফিগারেশন - আপনার দেওয়া তথ্য ব্যবহার করা হয়েছে
BOT_TOKEN = "8647557143:AAGTt9kbdYySkstBgqVxJLEDYjbNt8LBubo"
ADMIN_IDS = [7587190804, 8271698133]  # আপনার এডমিন আইডি
CHANNEL_LINK = "https://t.me/your_channel"  # আপনার চ্যানেল লিংক দিন

# কনভারসেশন স্টেটস
BROADCAST_MEDIA = 1

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ইউজার ডাটাবেজ ফাইল
USERS_FILE = 'users.json'

def load_users():
    """ইউজার ডাটাবেজ লোড করুন"""
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    """ইউজার ডাটাবেজ সংরক্ষণ করুন"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def update_user(user_id, user_data):
    """ইউজার আপডেট করুন (ডুপ্লিকেট হবে না)"""
    users = load_users()
    user_id_str = str(user_id)
    
    if user_id_str in users:
        # পুরাতন ইউজার আপডেট করুন
        users[user_id_str].update({
            'first_name': user_data.get('first_name', users[user_id_str]['first_name']),
            'username': user_data.get('username', users[user_id_str].get('username')),
            'last_active': datetime.now().isoformat()
        })
        logger.info(f"পুরাতন ইউজার আপডেট: {user_data.get('first_name')} (ID: {user_id})")
    else:
        # নতুন ইউজার যোগ করুন
        users[user_id_str] = {
            'first_name': user_data.get('first_name', 'Unknown'),
            'username': user_data.get('username'),
            'joined_date': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        logger.info(f"নতুন ইউজার যোগ হয়েছে: {user_data.get('first_name')} (ID: {user_id})")
    
    save_users(users)
    return users

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """স্টার্ট কমান্ড হ্যান্ডলার"""
    user = update.effective_user
    user_id = user.id
    
    # ইউজার আপডেট করুন (ডুপ্লিকেট হবে না)
    user_data = {
        'first_name': user.first_name,
        'username': user.username
    }
    update_user(user_id, user_data)
    
    # ইউজার ইনফো সংরক্ষণ করুন
    context.user_data['user_id'] = user_id
    context.user_data['first_name'] = user.first_name
    
    # ইনলাইন বাটন তৈরি
    keyboard = [
        [
            InlineKeyboardButton("📢 জয়েন্ট আপডেট চ্যানেল", url=CHANNEL_LINK)
        ],
        [
            InlineKeyboardButton("🆘 হেল্প", callback_data='help')
        ]
    ]
    
    # এডমিন হলে অতিরিক্ত বাটন দেখান
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 এডমিন প্যানেল", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"👋 স্বাগতম {user.first_name}!\n\nআমার বটে আপনাকে স্বাগতম। নিচের বাটনগুলো ব্যবহার করুন।"
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """বাটন ক্লিক হ্যান্ডলার"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == 'help':
        help_text = """
🆘 **হেল্প সেকশন**

এই বট ব্যবহার করার জন্য:

• /start - বট রিস্টার্ট করুন
• জয়েন্ট আপডেট চ্যানেল - চ্যানেলে জয়েন করুন
• এডমিন প্যানেল - শুধুমাত্র এডমিনদের জন্য

**এডমিন কমান্ড:**
• /users - মোট ইউজার সংখ্যা
• /show_users - সব ইউজারের তালিকা
• /broadcast - ব্রডকাস্ট করুন
"""
        await query.edit_message_text(help_text, parse_mode='Markdown')
    
    elif query.data == 'admin_panel' and user.id in ADMIN_IDS:
        admin_text = f"""
👑 **এডমিন প্যানেল**

আপনি এডমিন হিসেবে লগইন করেছেন।

**কমান্ডসমূহ:**
• /users - মোট ইউজার সংখ্যা
• /show_users - সব ইউজারের তালিকা
• /broadcast - ব্রডকাস্ট শুরু করুন
• /cancel - ব্রডকাস্ট বাতিল করুন
"""
        await query.edit_message_text(admin_text, parse_mode='Markdown')
    
    elif query.data.startswith('users_page_'):
        page = int(query.data.split('_')[2])
        await show_users_list(update, context, page)

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """মোট ইউজার সংখ্যা দেখান"""
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ এই কমান্ড শুধুমাত্র এডমিনদের জন্য!")
        return
    
    users = load_users()
    total_users = len(users)
    
    # পরিসংখ্যান তৈরি
    today = datetime.now().date()
    today_count = 0
    for data in users.values():
        joined = datetime.fromisoformat(data.get('joined_date', datetime.now().isoformat())).date()
        if joined == today:
            today_count += 1
    
    text = f"📊 **ইউজার পরিসংখ্যান**\n\n"
    text += f"• **মোট ইউজার:** {total_users}\n"
    text += f"• **আজকের জয়েন:** {today_count}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def show_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """সব ইউজারের তালিকা দেখান"""
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ এই কমান্ড শুধুমাত্র এডমিনদের জন্য!")
        return
    
    await show_users_list(update, context, page=1)

async def show_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
    """ইউজার লিস্ট দেখান"""
    users = load_users()
    total_users = len(users)
    
    if not users:
        await update.message.reply_text("📭 এখনও কোন ইউজার জয়েন করেনি!")
        return
    
    # প্রতি পৃষ্ঠায় ৫ জন ইউজার
    per_page = 5
    total_pages = (total_users + per_page - 1) // per_page
    
    if page < 1 or page > total_pages:
        page = 1
    
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_users)
    
    # ইউজারদের সাজান (সবচেয়ে নতুন প্রথমে)
    sorted_users = sorted(users.items(), key=lambda x: x[1].get('joined_date', ''), reverse=True)
    
    text = f"📋 **ইউজার লিস্ট (পৃষ্ঠা {page}/{total_pages})**\n"
    text += f"মোট ইউজার: {total_users}\n\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    
    for i, (user_id, data) in enumerate(sorted_users[start_idx:end_idx], start=start_idx+1):
        name = data.get('first_name', 'Unknown')
        username = data.get('username', 'না দেওয়া')
        joined = datetime.fromisoformat(data.get('joined_date', datetime.now().isoformat()))
        joined_date = joined.strftime("%d-%m-%Y")
        joined_time = joined.strftime("%I:%M %p")
        
        text += f"**{i}. {name}**\n"
        text += f"👤 ইউজারনেম: @{username}\n"
        text += f"🆔 আইডি: `{user_id}`\n"
        text += f"📅 জয়েন: {joined_date} {joined_time}\n\n"
        text += "━━━━━━━━━━━━━━━━\n\n"
    
    # নেভিগেশন বাটন
    keyboard = []
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ আগের", callback_data=f'users_page_{page-1}'))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("পরবর্তী ▶️", callback_data=f'users_page_{page+1}'))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 ব্যাক টু এডমিন", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ব্রডকাস্ট শুরু করুন"""
    user = update.effective_user
    
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ এই কমান্ড শুধুমাত্র এডমিনদের জন্য!")
        return ConversationHandler.END
    
    users = load_users()
    total_users = len(users)
    
    keyboard = [[InlineKeyboardButton("❌ ব্রডকাস্ট বাতিল করুন", callback_data='cancel_broadcast')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📝 **ব্রডকাস্ট সেটআপ**\n\n"
        f"👥 মোট ইউজার: {total_users}\n\n"
        f"আপনি কি পাঠাতে চান?\n"
        f"• টেক্সট লিখুন\n"
        f"• ছবি পাঠান (ক্যাপশন সহ)\n"
        f"• ভিডিও পাঠান (ক্যাপশন সহ)\n"
        f"• ডকুমেন্ট পাঠান\n\n"
        f"আপনার মেসেজ/মিডিয়া পাঠান:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    return BROADCAST_MEDIA

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ব্রডকাস্ট বাতিল করুন"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ ব্রডকাস্ট বাতিল করা হয়েছে।")
    return ConversationHandler.END

async def receive_broadcast_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ব্রডকাস্ট মিডিয়া রিসিভ করুন"""
    users = load_users()
    
    if not users:
        await update.message.reply_text("❌ কোন ইউজার নেই!")
        return ConversationHandler.END
    
    total_users = len(users)
    status_msg = await update.message.reply_text(
        f"📤 ব্রডকাস্ট শুরু হচ্ছে...\n"
        f"মোট ইউজার: {total_users}\n\n"
        f"পাঠানো হচ্ছে: 0/{total_users}"
    )
    
    success = 0
    failed = 0
    current = 0
    
    for user_id in users:
        try:
            if update.message.text:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"📢 **ব্রডকাস্ট মেসেজ**\n\n{update.message.text}",
                    parse_mode='Markdown'
                )
            elif update.message.photo:
                photo = update.message.photo[-1]
                caption = f"📢 **ব্রডকাস্ট**\n\n{update.message.caption or ''}"
                await context.bot.send_photo(
                    chat_id=int(user_id),
                    photo=photo.file_id,
                    caption=caption,
                    parse_mode='Markdown'
                )
            elif update.message.video:
                caption = f"📢 **ব্রডকাস্ট**\n\n{update.message.caption or ''}"
                await context.bot.send_video(
                    chat_id=int(user_id),
                    video=update.message.video.file_id,
                    caption=caption,
                    parse_mode='Markdown'
                )
            elif update.message.document:
                caption = f"📢 **ব্রডকাস্ট**\n\n{update.message.caption or ''}"
                await context.bot.send_document(
                    chat_id=int(user_id),
                    document=update.message.document.file_id,
                    caption=caption,
                    parse_mode='Markdown'
                )
            
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"ইউজার {user_id} এ মেসেজ পাঠাতে ব্যর্থ: {e}")
        
        current += 1
        
        if current % 20 == 0:
            try:
                await status_msg.edit_text(
                    f"📤 ব্রডকাস্ট চলছে...\n"
                    f"পাঠানো হয়েছে: {current}/{total_users}\n"
                    f"✓ সফল: {success}\n"
                    f"✗ ব্যর্থ: {failed}"
                )
            except:
                pass
        
        await asyncio.sleep(0.05)
    
    final_text = f"✅ **ব্রডকাস্ট সম্পন্ন!**\n\n"
    final_text += f"📊 **পরিসংখ্যান:**\n"
    final_text += f"• মোট ইউজার: {total_users}\n"
    final_text += f"• ✓ সফল: {success}\n"
    final_text += f"• ✗ ব্যর্থ: {failed}"
    
    await status_msg.edit_text(final_text, parse_mode='Markdown')
    return ConversationHandler.END

async def broadcast_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ব্রডকাস্ট বাতিল কমান্ড"""
    await update.message.reply_text("❌ কোনো চলমান ব্রডকাস্ট নেই।")
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """সাধারণ মেসেজ হ্যান্ডলার"""
    await update.message.reply_text("আমি শুধু কমান্ড বুঝি। /start ব্যবহার করুন।")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """এরর হ্যান্ডলার"""
    logger.error(f"আপডেট {update} এরর হয়েছে: {context.error}")

def main():
    """মেইন ফাংশন"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # কনভারসেশন হ্যান্ডলার
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler('broadcast', broadcast_start)],
        states={
            BROADCAST_MEDIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast_media),
                MessageHandler(filters.PHOTO, receive_broadcast_media),
                MessageHandler(filters.VIDEO, receive_broadcast_media),
                MessageHandler(filters.DOCUMENT, receive_broadcast_media),
                CallbackQueryHandler(cancel_broadcast, pattern='^cancel_broadcast$')
            ],
        },
        fallbacks=[CommandHandler('cancel', broadcast_cancel_command)],
        allow_reentry=True
    )
    
    # হ্যান্ডলার যোগ করুন
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("show_users", show_users_command))
    application.add_handler(broadcast_conv)
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    print("🤖 বট চালু হচ্ছে... আপনার এডমিন আইডি:", ADMIN_IDS)
    print("✅ বট সফলভাবে চালু হয়েছে! /start দিন")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
