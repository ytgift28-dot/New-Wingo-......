import telebot
import requests
import time
import sqlite3
import threading

# --- কনফিগারেশন ---
API_TOKEN = '8693790155:AAEEIi4IIumkYTtsQISh6uG9JWPJsCXPPW8'
ADMIN_ID = 6941003064
CHANNEL_USERNAME = "@SH_tricks" 
ADS_LINK = "https://www.profitablecpmratenetwork.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"
OWNER_TAG = "@Suptho1"

bot = telebot.TeleBot(API_TOKEN)

# --- ডাটাবেস ফাংশন ---
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, limit_count INTEGER, status TEXT)''')
    conn.commit()
    conn.close()

def get_user_info(user_id):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT limit_count, status FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (0, 'active')

def update_user(user_id, limit=None, status=None):
    cl, cs = get_user_info(user_id)
    nl = limit if limit is not None else cl
    ns = status if status is not None else cs
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, limit_count, status) VALUES (?, ?, ?)", (user_id, nl, ns))
    conn.commit()
    conn.close()

# --- Force Join Check ---
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- 10-Round Advanced Logic ---
def get_advanced_prediction():
    URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    try:
        res = requests.get(URL, params={"pageNo":1, "pageSize":100}, timeout=10)
        data = res.json().get('data', {}).get('list', [])
        if len(data) < 20: return None
        
        current_p = [1 if int(d['number']) >= 5 else 0 for d in data[:10]]
        best_match = None
        max_m = 0

        for i in range(1, len(data) - 11):
            past_p = [1 if int(data[j]['number']) >= 5 else 0 for j in range(i, i + 10)]
            m = sum(1 for a, b in zip(current_p, past_p) if a == b)
            if m >= 9:
                best_match = "BIG 🟢" if int(data[i-1]['number']) >= 5 else "SMALL 🔴"
                max_m = m
                break
            elif m == 8:
                best_match = "BIG 🟢" if int(data[i-1]['number']) >= 5 else "SMALL 🔴"
                max_m = m

        if best_match:
            issue = int(data[0]['issue']) + 1
            return f"✨ <b>Period:</b> <code>{issue}</code>\n🎯 <b>Prediction:</b> {best_match}\n🔥 <b>Accuracy:</b> <code>{(max_m/10)*100}%</code>"
        return "⏳ <b>Analyzing Market...</b>"
    except: return None

# --- User Keyboards ---
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎰 Get Prediction", "📺 Watch Ad (5 Credit)")
    markup.add("👤 My Account", "📢 Support")
    return markup

# --- Admin Inline Keyboard ---
def admin_menu():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats"))
    markup.add(telebot.types.InlineKeyboardButton("➕ Add Credits", callback_data="admin_add"),
               telebot.types.InlineKeyboardButton("👑 Make VIP", callback_data="admin_vip"))
    markup.add(telebot.types.InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
               telebot.types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_bc"))
    return markup

# --- Handlers ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if not is_subscribed(uid):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"))
        bot.send_message(uid, "❌ <b>Access Denied!</b>\nআগে চ্যানেলে জয়েন করুন।", reply_markup=markup, parse_mode="HTML")
        return
    update_user(uid)
    bot.send_message(uid, "👋 স্বাগতম! প্রেডিকশন নিতে নিচের বাটন ব্যবহার করুন।", reply_markup=main_menu(), parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "🛠 <b>Admin Control Panel</b>\nনিচের বাটনগুলো ব্যবহার করুন:", reply_markup=admin_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = message.from_user.id
    limit, status = get_user_info(uid)
    if status == 'banned': return

    if message.text == "🎰 Get Prediction":
        if not is_subscribed(uid):
            bot.send_message(uid, "❌ চ্যানেলে জয়েন নেই!")
            return
        if limit <= 0 and status != 'vip':
            bot.send_message(uid, "❌ ক্রেডিট শেষ! অ্যাড দেখুন।")
            return
        res = get_advanced_prediction()
        if res:
            if "Analyzing" not in res and status != 'vip': update_user(uid, limit=limit-1)
            bot.send_message(uid, f"🎰 <b>Wingo 30S Result</b>\n\n{res}\n\n👤 Owner: {OWNER_TAG}", parse_mode="HTML")

    elif message.text == "📺 Watch Ad (5 Credit)":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔗 Watch Ad", url=ADS_LINK))
        markup.add(telebot.types.InlineKeyboardButton("✅ Claim Reward", callback_data="claim_reward"))
        bot.send_message(uid, "⏳ বিজ্ঞাপনে ক্লিক করার ১০ সেকেন্ড পর রিওয়ার্ড বাটনে চাপ দিন।", reply_markup=markup)

    elif message.text == "👤 My Account":
        bot.send_message(uid, f"👤 <b>Account</b>\n💰 ক্রেডিট: <code>{limit}</code>\n🌟 স্ট্যাটাস: {status.upper()}", parse_mode="HTML")

    elif message.text == "📢 Support":
        bot.send_message(uid, f"🛠 সাহায্য পেতে যোগাযোগ করুন: {OWNER_TAG}")

# --- Callback Queries ---
@bot.callback_query_handler(func=lambda call: True)
def callback_all(call):
    uid = call.from_user.id
    
    if call.data == "claim_reward":
        update_user(uid, limit=get_user_info(uid)[0]+5)
        bot.answer_callback_query(call.id, "✅ ৫ ক্রেডিট যোগ হয়েছে!")
        bot.edit_message_text("✅ ক্রেডিট যোগ করা হয়েছে!", chat_id=call.message.chat.id, message_id=call.message.message_id)

    elif call.data == "admin_stats":
        if uid != ADMIN_ID: return
        conn = sqlite3.connect('users.db')
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        bot.answer_callback_query(call.id, f"মোট ইউজার: {count}")
        bot.send_message(ADMIN_ID, f"📊 <b>Total Users:</b> <code>{count}</code>", parse_mode="HTML")

    elif call.data in ["admin_add", "admin_vip", "admin_ban", "admin_bc"]:
        if uid != ADMIN_ID: return
        action = call.data.split("_")[1]
        msg = bot.send_message(ADMIN_ID, f"⌨️ আপনি <b>{action.upper()}</b> করতে চান।\nদয়া করে প্রয়োজনীয় তথ্য পাঠান (যেমন: <code>ID Amount</code> বা <code>ID</code> বা <code>Message</code>)", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_admin_action, action)

def process_admin_action(message, action):
    try:
        if action == "add":
            target_id, amt = message.text.split()
            update_user(int(target_id), limit=get_user_info(int(target_id))[0]+int(amt))
            bot.send_message(ADMIN_ID, "✅ ক্রেডিট যোগ হয়েছে!")
        elif action == "vip":
            update_user(int(message.text), status='vip')
            bot.send_message(ADMIN_ID, "✅ VIP করা হয়েছে!")
        elif action == "ban":
            update_user(int(message.text), status='banned')
            bot.send_message(ADMIN_ID, "🚫 ব্যান করা হয়েছে!")
        elif action == "bc":
            conn = sqlite3.connect('users.db')
            users = conn.execute("SELECT user_id FROM users").fetchall()
            for u in users:
                try: bot.send_message(u[0], f"📢 <b>Notification:</b>\n\n{message.text}", parse_mode="HTML")
                except: pass
            bot.send_message(ADMIN_ID, "✅ ব্রডকাস্ট সম্পন্ন!")
    except: bot.send_message(ADMIN_ID, "❌ তথ্য ভুল! আবার চেষ্টা করুন।")

if __name__ == "__main__":
    init_db()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)e
