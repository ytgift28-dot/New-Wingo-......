import telebot
from telebot import types
import requests
import time
import threading
import sqlite3
from flask import Flask
import os

# ==========================================
# 🌐 WEB SERVER (For Render Port Fix)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ SH AI Predictor is Online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 🔧 CONFIGURATION
# ==========================================
API_TOKEN = "8693790155:AAEa3kfHAkgWHWRzY9Xfsnb7R1AmEPsd2dw" 
ADMIN_ID = 6941003064
CHANNEL_USERNAME = "@SH_tricks"
OWNER_TAG = "@Suptho1"
ADS_LINK = "https://www.profitablecpmratenetwork.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"

bot = telebot.TeleBot(API_TOKEN)
active_auto_users = {} # Auto loop tracker

# ==========================================
# 📂 DATABASE SYSTEM
# ==========================================
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                    (user_id INTEGER PRIMARY KEY, credits INTEGER, status TEXT)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT credits, status FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (0, 'active')

def update_user(user_id, credits=None, status=None):
    c, s = get_user(user_id)
    new_c = credits if credits is not None else c
    new_s = status if status is not None else s
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (user_id, new_c, new_s))
    conn.commit()
    conn.close()

# ==========================================
# 🧠 PREDICTION LOGIC (300 Round Support)
# ==========================================
def fetch_prediction():
    URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://draw.ar-lottery01.com/"
    }
    try:
        # ৩০০ রাউন্ড ডাটা আনা হচ্ছে
        res = requests.get(URL, params={"pageNo":1, "pageSize":300}, headers=headers, timeout=15)
        data = res.json().get('data', {}).get('list', [])
        if not data: return None
        
        issue = data[0]['issueNumber']
        num = int(data[0]['number'])
        actual = "BIG 🐘" if num >= 5 else "SMALL 🐜"
        
        # Simple Pattern Analysis
        last_5 = [1 if int(d['number']) >= 5 else 0 for d in data[:5]]
        pred_val = "SMALL 🐜" if sum(last_5) >= 3 else "BIG 🐘"
        
        return issue, actual, pred_val, "Pattern: " + ("Dragon" if sum(last_5) >= 4 else "Trend")
    except: return None

# ==========================================
# 🔄 AUTO LOOP FUNCTION
# ==========================================
def auto_loop(chat_id):
    last_issue = None
    while active_auto_users.get(chat_id, False):
        try:
            credits, status = get_user(chat_id)
            if credits <= 0 and status != 'vip':
                bot.send_message(chat_id, "❌ ক্রেডিট শেষ! অটো সিগন্যাল বন্ধ হয়ে গেছে।")
                active_auto_users[chat_id] = False
                break
                
            res = fetch_prediction()
            if res:
                issue, actual, pred, logic = res
                if issue != last_issue:
                    if status != 'vip': update_user(chat_id, credits=credits-1)
                    
                    next_issue = int(issue) + 1
                    msg = f"🆔 **Period:** `{issue}`\n🎲 **Result:** {actual}\n\n🔮 **NEXT:** `{next_issue}`\n🔥 **PRED:** `{pred}`\n💡 **Logic:** {logic}\n\n👤 Owner: {OWNER_TAG}"
                    
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("🛑 STOP", callback_data="stop_auto"))
                    bot.send_message(chat_id, msg, parse_mode='Markdown', reply_markup=markup)
                    last_issue = issue
            time.sleep(10)
        except: time.sleep(10)

# ==========================================
# 🛡️ HANDLERS & HELPERS
# ==========================================
def is_joined(user_id):
    try:
        m = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in ['member', 'administrator', 'creator']
    except: return False

@bot.message_handler(commands=['start'])
def start(m):
    update_user(m.chat.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
    markup.add(types.InlineKeyboardButton("✅ Start Using", callback_data="main_menu"))
    bot.send_message(m.chat.id, f"👋 Welcome to **SH AI Predictor**!\n\nJoin our channel to continue.", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_panel(m):
    if m.chat.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add Credit", callback_data="a_add"), types.InlineKeyboardButton("👑 Make VIP", callback_data="a_vip"))
        markup.add(types.InlineKeyboardButton("📢 Broadcast", callback_data="a_bc"))
        bot.send_message(ADMIN_ID, "🛠 **Admin Panel**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    if call.data == "main_menu":
        if not is_joined(uid):
            bot.answer_callback_query(call.id, "❌ Join Channel First!", show_alert=True)
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎰 Auto Signal", "📺 Watch Ad (+5)")
        markup.add("👤 My Account", "📢 Support")
        bot.send_message(uid, "✅ Verified! Select an option:", reply_markup=markup)

    elif call.data == "start_auto":
        credits, status = get_user(uid)
        if credits <= 0 and status != 'vip':
            bot.answer_callback_query(call.id, "❌ No Credits!", show_alert=True)
            return
        active_auto_users[uid] = True
        threading.Thread(target=auto_loop, args=(uid,)).start()
        bot.edit_message_text("🚀 Auto Signals Started!", uid, call.message.message_id)

    elif call.data == "stop_auto":
        active_auto_users[uid] = False
        bot.send_message(uid, "🛑 Auto Signal Stopped.")

    elif call.data == "claim":
        update_user(uid, credits=get_user(uid)[0]+5)
        bot.edit_message_text("✅ +5 Credits added!", uid, call.message.message_id)

    elif call.data.startswith("a_") and uid == ADMIN_ID:
        act = call.data.split("_")[1]
        msg = bot.send_message(ADMIN_ID, f"Enter User ID for {act}:")
        bot.register_next_step_handler(msg, admin_action, act)

def admin_action(m, act):
    try:
        tid = int(m.text)
        if act == "add": update_user(tid, credits=get_user(tid)[0]+50)
        elif act == "vip": update_user(tid, status='vip')
        bot.send_message(ADMIN_ID, "✅ Done!")
    except: bot.send_message(ADMIN_ID, "❌ Error!")

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    uid = m.chat.id
    credits, status = get_user(uid)
    
    if m.text == "🎰 Auto Signal":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ START AUTO", callback_data="start_auto"))
        bot.send_message(uid, f"💰 Credits: {credits}\n🌟 Status: {status.upper()}", reply_markup=markup)

    elif m.text == "📺 Watch Ad (+5)":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Watch Ad", url=ADS_LINK))
        markup.add(telebot.types.InlineKeyboardButton("✅ Claim", callback_data="claim"))
        bot.send_message(uid, "Click Watch and wait 10s.", reply_markup=markup)

    elif m.text == "👤 My Account":
        bot.send_message(uid, f"👤 User: `{uid}`\n💰 Credits: `{credits}`\n🌟 Status: `{status.upper()}`", parse_mode='Markdown')

    elif m.text == "📢 Support":
        bot.send_message(uid, f"Contact: {OWNER_TAG}")

# ==========================================
# 🔥 EXECUTION
# ==========================================
if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_web).start()
    bot.infinity_polling(skip_pending=True)
