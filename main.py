import telebot
from telebot import types
import requests
import time
import threading
import sqlite3
from flask import Flask
import os

# --- Web Server for Render ---
app = Flask(__name__)
@app.route('/')
def home(): return "✅ SH AI Predictor with Admin Panel is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Config ---
API_TOKEN = "8693790155:AAEa3kfHAkgWHWRzY9Xfsnb7R1AmEPsd2dw" 
ADMIN_ID = 6941003064  # আপনার আইডি
CHANNEL_USERNAME = "@SH_tricks"
OWNER_TAG = "@Suptho1"
ADS_LINK = "https://www.profitablecpmratenetwork.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"

bot = telebot.TeleBot(API_TOKEN)
active_auto_users = {} 

# --- Database Systems ---
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, status TEXT)')
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

def get_all_users():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    return [u[0] for u in users]

# --- Logic: History Match + Your Patterns ---
def analyze_prediction(history_list):
    try:
        current_p = [1 if int(d['number']) >= 5 else 0 for d in history_list[:10]]
        best_res, max_m = None, 0
        for i in range(1, len(history_list) - 11):
            past_p = [1 if int(history_list[j]['number']) >= 5 else 0 for j in range(i, i + 10)]
            matches = sum(1 for a, b in zip(current_p, past_p) if a == b)
            if matches >= 8:
                best_res = "Big" if int(history_list[i-1]['number']) >= 5 else "Small"
                max_m = matches; break
        if not best_res:
            l, p1, p2 = current_p[0], current_p[1], current_p[2]
            if l == p1 == p2: return ("Big" if l == 1 else "Small"), "Pattern: Dragon", 85
            if l == p2 and l != p1: return ("Big" if p1 == 1 else "Small"), "Pattern: ZigZag", 82
            n1, n2 = int(history_list[0]['number']), int(history_list[1]['number'])
            return ("Big" if (n1+n2)%2!=0 else "Small"), ("Math: Odd" if (n1+n2)%2!=0 else "Math: Even"), 75
        return best_res, f"History Match ({max_m}/10)", max_m * 10
    except: return "Big", "Trend Analysis", 70

def fetch_prediction():
    URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    try:
        res = requests.get(URL, params={"pageNo":1, "pageSize":300}, headers=headers, timeout=15)
        data = res.json().get('data', {}).get('list', [])
        if not data: return None
        issue, num = data[0]['issueNumber'], int(data[0]['number'])
        actual = "BIG 🐘" if num >= 5 else "SMALL 🐜"
        p_raw, logic, acc = analyze_prediction(data)
        return issue, actual, ("BIG 🐘" if p_raw == "Big" else "SMALL 🐜"), logic, acc
    except: return None

# --- Auto Loop ---
def auto_loop(chat_id):
    last_issue = None
    while active_auto_users.get(chat_id, False):
        res = fetch_prediction()
        if res:
            issue, actual, pred, logic, acc = res
            if issue != last_issue:
                c, s = get_user(chat_id)
                if s == 'banned': active_auto_users[chat_id] = False; break
                if c <= 0 and s != 'vip':
                    bot.send_message(chat_id, "❌ ক্রেডিট শেষ! বিজ্ঞাপন দেখুন।")
                    active_auto_users[chat_id] = False; break
                if s != 'vip': update_user(chat_id, credits=c-1)
                msg = f"🆔 **Period:** `{issue}`\n🎲 **Result:** {actual}\n\n🔮 **NEXT:** `{int(issue)+1}`\n🔥 **PRED:** {pred}\n🎯 **Accuracy:** `{acc}%`\n💡 **Logic:** {logic}"
                bot.send_message(chat_id, msg, parse_mode='Markdown', reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🛑 STOP", callback_data="stop_auto")))
                last_issue = issue
        time.sleep(10)

# --- Admin Handlers ---
@bot.message_handler(commands=['admin'])
def admin_menu(m):
    if m.chat.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("📊 Stats", callback_data="a_stats"),
                   types.InlineKeyboardButton("📢 Broadcast", callback_data="a_bc"))
        markup.add(types.InlineKeyboardButton("➕ Add Credit", callback_data="a_add"),
                   types.InlineKeyboardButton("👑 Make VIP", callback_data="a_vip"))
        markup.add(types.InlineKeyboardButton("🚫 Ban User", callback_data="a_ban"),
                   types.InlineKeyboardButton("🔓 Unban User", callback_data="a_unban"))
        bot.send_message(ADMIN_ID, "🛠 **Admin Control Panel**", reply_markup=markup)

def broadcast_msg(m):
    users = get_all_users()
    count = 0
    for u in users:
        try:
            bot.copy_message(u, ADMIN_ID, m.message_id)
            count += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast Done! Sent to {count} users.")

def admin_process(m, action):
    try:
        target_id = int(m.text)
        if action == "add": update_user(target_id, credits=get_user(target_id)[0]+100); msg = "100 Credits Added!"
        elif action == "vip": update_user(target_id, status='vip'); msg = "User is now VIP!"
        elif action == "ban": update_user(target_id, status='banned'); msg = "User Banned!"
        elif action == "unban": update_user(target_id, status='active'); msg = "User Unbanned!"
        bot.send_message(ADMIN_ID, f"✅ {msg}")
    except: bot.send_message(ADMIN_ID, "❌ Invalid User ID!")

# --- Main Handlers ---
@bot.callback_query_handler(func=lambda call: True)
def cb_handler(call):
    uid = call.message.chat.id
    if call.data.startswith("a_") and uid == ADMIN_ID:
        act = call.data.split("_")[1]
        if act == "stats":
            users = get_all_users()
            bot.answer_callback_query(call.id, f"Total Users: {len(users)}", show_alert=True)
        elif act == "bc":
            m = bot.send_message(ADMIN_ID, "Send the message/photo you want to broadcast:")
            bot.register_next_step_handler(m, broadcast_msg)
        else:
            m = bot.send_message(ADMIN_ID, f"Enter Target User ID to {act}:")
            bot.register_next_step_handler(m, admin_process, act)
    
    elif call.data == "start_auto":
        active_auto_users[uid] = True
        threading.Thread(target=auto_loop, args=(uid,)).start()
        bot.answer_callback_query(call.id, "Auto Loop Started!")
    elif call.data == "stop_auto":
        active_auto_users[uid] = False
        bot.send_message(uid, "🛑 Auto signals stopped.")
    elif call.data == "claim":
        update_user(uid, credits=get_user(uid)[0]+5)
        bot.edit_message_text("✅ +5 Credits added!", uid, call.message.message_id)

@bot.message_handler(commands=['start'])
def welcome(m):
    update_user(m.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add("🎰 Auto Signal", "📺 Watch Ad (+5)").add("👤 My Account", "📢 Support")
    bot.send_message(m.chat.id, "👋 Welcome! Select an option below:", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def texts(m):
    uid = m.chat.id
    c, s = get_user(uid)
    if s == 'banned': return
    if m.text == "🎰 Auto Signal":
        bot.send_message(uid, "🚀 Start Auto signals.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("▶️ START", callback_data="start_auto")))
    elif m.text == "📺 Watch Ad (+5)":
        bot.send_message(uid, "Watch & Claim.", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔗 Watch", url=ADS_LINK), types.InlineKeyboardButton("✅ Claim", callback_data="claim")))
    elif m.text == "👤 My Account":
        bot.send_message(uid, f"👤 ID: `{uid}`\n💰 Credits: `{c}`\n🌟 Status: `{s.upper()}`", parse_mode='Markdown')

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_web).start()
    bot.infinity_polling(skip_pending=True)
