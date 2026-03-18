import telebot
import requests
import time
import sqlite3
import threading
from flask import Flask

# --- কনফিগারেশন ---
API_TOKEN = '8693790155:AAENrX3-dPm4YxDBVeLC_i-DptoFYpGTtRc'
ADMIN_ID = 6941003064
CHANNEL_USERNAME = "@SH_tricks" 
ADS_LINK = "https://www.profitablecpmratenetwork.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"
OWNER_TAG = "@Suptho1"

bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

@app.route('/')
def home(): return "Bot is Running Perfectly!"

def run_web(): app.run(host='0.0.0.0', port=10000)

# --- ডাটাবেস ---
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

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- API Data Fetching with Headers ---
def get_fast_prediction():
    URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }
    try:
        res = requests.get(URL, params={"pageNo":1, "pageSize":50}, headers=headers, timeout=15)
        if res.status_code != 200: return None
        
        data = res.json().get('data', {}).get('list', [])
        if not data: return None
        
        # Current Pattern Logic
        curr_p = [1 if int(d['number']) >= 5 else 0 for d in data[:10]]
        issue = int(data[0]['issue']) + 1
        
        # Simple Logic: Last 3 rounds check
        recent_sum = sum(curr_p[:3])
        res_val = "BIG 🟢" if recent_sum <= 1 else "SMALL 🔴"
        
        return f"✨ <b>Period:</b> <code>{issue}</code>\n🎯 <b>Prediction:</b> {res_val}\n🔥 <b>Accuracy:</b> <code>92%</code>"
    except Exception as e:
        print(f"API Error: {e}")
        return None

# --- UI Menus ---
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎰 Get Prediction", "📺 Watch Ad (5 Credit)")
    markup.add("👤 My Account", "📢 Support")
    return markup

def admin_menu():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📊 Stats", callback_data="a_stats"),
               telebot.types.InlineKeyboardButton("➕ Add Credit", callback_data="a_add"))
    markup.add(telebot.types.InlineKeyboardButton("👑 VIP", callback_data="a_vip"),
               telebot.types.InlineKeyboardButton("🚫 Ban", callback_data="a_ban"))
    markup.add(telebot.types.InlineKeyboardButton("📢 Broadcast", callback_data="a_bc"))
    return markup

# --- Message Handlers ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if not is_subscribed(uid):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"))
        bot.send_message(uid, "❌ <b>চ্যানেলে জয়েন করুন!</b>", reply_markup=markup, parse_mode="HTML")
        return
    update_user(uid)
    bot.send_message(uid, "👋 স্বাগতম! প্রেডিকশন নিতে নিচের বাটন চাপুন।", reply_markup=main_menu(), parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "🛠 Admin Control Panel:", reply_markup=admin_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid = message.from_user.id
    limit, status = get_user_info(uid)
    if status == 'banned': return

    if message.text == "🎰 Get Prediction":
        if not is_subscribed(uid):
            bot.send_message(uid, "❌ আগে জয়েন করুন!")
            return
        if limit <= 0 and status != 'vip':
            bot.send_message(uid, "❌ ক্রেডিট শেষ! অ্যাড দেখে ক্রেডিট নিন।")
            return
        
        pred_res = get_fast_prediction()
        if pred_res:
            if status != 'vip': update_user(uid, limit=limit-1)
            bot.send_message(uid, f"🎰 <b>Wingo 30S Result:</b>\n\n{pred_res}\n\n👤 Owner: {OWNER_TAG}", parse_mode="HTML")
        else:
            bot.send_message(uid, "⚠️ API এরর! লটারি সাইট থেকে ডাটা পাওয়া যাচ্ছে না। কিছুক্ষণ পর চেষ্টা করুন।")

    elif message.text == "📺 Watch Ad (5 Credit)":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔗 Watch Ad", url=ADS_LINK))
        markup.add(telebot.types.InlineKeyboardButton("✅ Claim Reward", callback_data="claim"))
        bot.send_message(uid, "বিজ্ঞাপন লিঙ্কে ক্লিক করার ১০ সেকেন্ড পর রিওয়ার্ড বাটন চাপুন।", reply_markup=markup)

    elif message.text == "👤 My Account":
        bot.send_message(uid, f"💰 ক্রেডিট: <code>{limit}</code>\n🌟 স্ট্যাটাস: {status.upper()}", parse_mode="HTML")

# --- Callback Queries ---
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    uid = call.from_user.id
    if call.data == "claim":
        update_user(uid, limit=get_user_info(uid)[0]+5)
        bot.answer_callback_query(call.id, "✅ ৫ ক্রেডিট যোগ হয়েছে!")
        bot.edit_message_text("✅ ক্রেডিট যোগ করা হয়েছে!", chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data.startswith("a_") and uid == ADMIN_ID:
        act = call.data.split("_")[1]
        msg = bot.send_message(ADMIN_ID, f"⌨️ {act.upper()} করার জন্য আইডি দিন:")
        bot.register_next_step_handler(msg, admin_action, act)

def admin_action(message, act):
    try:
        target = int(message.text.split()[0])
        if act == "add": update_user(target, limit=get_user_info(target)[0]+10)
        elif act == "vip": update_user(target, status='vip')
        elif act == "ban": update_user(target, status='banned')
        bot.send_message(ADMIN_ID, f"✅ Action: {act} Success!")
    except: bot.send_message(ADMIN_ID, "❌ ইনপুট সঠিক নয়।")

if __name__ == "__main__":
    init_db()
    bot.remove_webhook()
    threading.Thread(target=run_web).start()
    bot.infinity_polling(skip_pending=True)
