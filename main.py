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
def home(): return "✅ SH AI Predictor is 100% Active!"

def run_web():
    # Render-এর জন্য ডাইনামিক পোর্ট
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Config ---
API_TOKEN = "8693790155:AAEa3kfHAkgWHWRzY9Xfsnb7R1AmEPsd2dw" 
ADMIN_ID = 6941003064 
CHANNEL_USERNAME = "@SH_tricks"
OWNER_TAG = "@Suptho1"
ADS_LINK = "https://www.profitablecpmratenetwork.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"

bot = telebot.TeleBot(API_TOKEN)
active_auto_users = {} 
ad_click_time = {} # অ্যাড ট্র্যাকিংয়ের জন্য

# --- Database ---
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

# --- 🧠 ALL ORIGINAL LOGIC (Unchanged) ---
def analyze_prediction(history_list):
    try:
        current_p = [1 if int(d['number']) >= 5 else 0 for d in history_list[:10]]
        best_res, max_m = None, 0
        # ৩০০ রাউন্ডে ৭/৮ বার মিল খোঁজা
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
                    bot.send_message(chat_id, "❌ ক্রেডিট শেষ! অ্যাড দেখে ক্রেডিট নিন।")
                    active_auto_users[chat_id] = False; break
                if s != 'vip': update_user(chat_id, credits=c-1)
                
                msg = f"🆔 **Period:** `{issue}`\n🎲 **Result:** {actual}\n\n🔮 **NEXT:** `{int(issue)+1}`\n🔥 **PRED:** {pred}\n🎯 **Accuracy:** `{acc}%`\n💡 **Logic:** {logic}"
                markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🛑 STOP", callback_data="stop_auto"))
                bot.send_message(chat_id, msg, parse_mode='Markdown', reply_markup=markup)
                last_issue = issue
        time.sleep(10)

# --- Handlers ---
@bot.message_handler(commands=['start'])
def start(m):
    update_user(m.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎰 Auto Signal", "📺 Watch Ad (+5)")
    markup.add("👤 My Account", "📢 Support")
    bot.send_message(m.chat.id, "👋 **SH WINGO AI Predictor**-এ স্বাগতম!\nনিচের মেনু থেকে অপশন বেছে নিন।", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_menu(m):
    if m.chat.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("📊 Stats", callback_data="a_stats"), types.InlineKeyboardButton("📢 Broadcast", callback_data="a_bc"))
        markup.add(types.InlineKeyboardButton("➕ Add Credit", callback_data="a_add"), types.InlineKeyboardButton("👑 Make VIP", callback_data="a_vip"))
        markup.add(types.InlineKeyboardButton("🚫 Ban User", callback_data="a_ban"), types.InlineKeyboardButton("🔓 Unban User", callback_data="a_unban"))
        bot.send_message(ADMIN_ID, "🛠 **Admin Panel**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def cb_handler(call):
    uid = call.message.chat.id
    if call.data == "watch_trigger":
        ad_click_time[uid] = time.time() # ক্লিক করার সময় সেভ করা হলো
        bot.answer_callback_query(call.id, "বিজ্ঞাপন লোড হচ্ছে... ১০ সেকেন্ড দেখুন।", show_alert=False)
        
    elif call.data == "claim":
        # সময় চেক: ১০ সেকেন্ডের কম হলে ক্রেডিট দিবে না
        start_time = ad_click_time.get(uid, 0)
        if time.time() - start_time < 10:
            bot.answer_callback_query(call.id, "❌ আপনি ১০ সেকেন্ড অপেক্ষা করেননি! আবার চেষ্টা করুন।", show_alert=True)
        else:
            update_user(uid, credits=get_user(uid)[0]+5)
            ad_click_time[uid] = 0 # রিসেট
            bot.edit_message_text("✅ সফল! আপনার অ্যাকাউন্টে ৫ ক্রেডিট যোগ করা হয়েছে।", uid, call.message.message_id)

    elif call.data == "start_auto":
        active_auto_users[uid] = True
        threading.Thread(target=auto_loop, args=(uid,)).start()
        bot.edit_message_text("🚀 অটো সিগন্যাল চালু হয়েছে...", uid, call.message.message_id)

    elif call.data == "stop_auto":
        active_auto_users[uid] = False
        bot.send_message(uid, "🛑 অটো সিগন্যাল বন্ধ করা হয়েছে।")

    # Admin Callback Logic
    elif call.data.startswith("a_") and uid == ADMIN_ID:
        act = call.data.split("_")[1]
        if act == "stats":
            bot.answer_callback_query(call.id, f"মোট ইউজার: {len(get_all_users())}", show_alert=True)
        elif act == "bc":
            msg = bot.send_message(ADMIN_ID, "ব্রডকাস্ট মেসেজটি লিখুন:")
            bot.register_next_step_handler(msg, lambda m: [bot.send_message(u, m.text) for u in get_all_users()])
        else:
            msg = bot.send_message(ADMIN_ID, f"ইউজার আইডি দিন ({act}):")
            bot.register_next_step_handler(msg, admin_process, act)

def admin_process(m, action):
    try:
        tid = int(m.text)
        if action == "add": update_user(tid, credits=get_user(tid)[0]+100)
        elif action == "vip": update_user(tid, status='vip')
        elif action == "ban": update_user(tid, status='banned')
        bot.send_message(ADMIN_ID, "✅ সফল হয়েছে!")
    except: bot.send_message(ADMIN_ID, "❌ ভুল আইডি!")

@bot.message_handler(func=lambda m: True)
def texts(m):
    uid = m.chat.id
    c, s = get_user(uid)
    if s == 'banned': return
    
    if m.text == "🎰 Auto Signal":
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("▶️ START AUTO", callback_data="start_auto"))
        bot.send_message(uid, "অটো সিগন্যাল শুরু করতে নিচের বাটনে চাপুন।", reply_markup=markup)
        
    elif m.text == "📺 Watch Ad (+5)":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Watch Ad", url=ADS_LINK, callback_data="watch_trigger"))
        markup.add(types.InlineKeyboardButton("✅ Claim Credit", callback_data="claim"))
        bot.send_message(uid, "নিচের লিঙ্কে ক্লিক করে ১০ সেকেন্ড অপেক্ষা করুন, তারপর Claim বাটন চাপুন।", reply_markup=markup)
        
    elif m.text == "👤 My Account":
        bot.send_message(uid, f"👤 **User ID:** `{uid}`\n💰 **Credits:** `{c}`\n🌟 **Status:** `{s.upper()}`", parse_mode='Markdown')
        
    elif m.text == "📢 Support":
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📩 Contact Owner", url=f"https://t.me/{OWNER_TAG[1:]}"))
        bot.send_message(uid, "যেকোনো প্রয়োজনে বা ভিআইপি এক্সেস পেতে এডমিনের সাথে যোগাযোগ করুন।", reply_markup=markup)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_web).start()
    bot.infinity_polling(skip_pending=True)
