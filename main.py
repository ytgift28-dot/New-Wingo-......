import telebot
import requests
import time
import sqlite3
import threading

# --- কনফিগারেশন ---
API_TOKEN = '8693790155:AAENrX3-dPm4YxDBVeLC_i-DptoFYpGTtRc'
ADMIN_ID = 6941003064
CHANNEL_USERNAME = "@SH_tricks" 
ADS_LINK = "https://www.profitablecpmratenetwork.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"
OWNER_TAG = "@Suptho1"

bot = telebot.TeleBot(API_TOKEN)

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

# --- Force Join ---
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- Prediction Logic ---
def get_prediction():
    URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    try:
        res = requests.get(URL, params={"pageNo":1, "pageSize":50}, timeout=10)
        data = res.json().get('data', {}).get('list', [])
        if not data: return None
        
        current_p = [1 if int(d['number']) >= 5 else 0 for d in data[:10]]
        best_match = None
        m_count = 0

        for i in range(1, len(data) - 11):
            past_p = [1 if int(data[j]['number']) >= 5 else 0 for j in range(i, i + 10)]
            matches = sum(1 for a, b in zip(current_p, past_p) if a == b)
            if matches >= 9:
                best_match = "BIG 🟢" if int(data[i-1]['number']) >= 5 else "SMALL 🔴"
                m_count = matches
                break
        
        if best_match:
            issue = int(data[0]['issue']) + 1
            return f"✨ <b>Period:</b> <code>{issue}</code>\n🎯 <b>Prediction:</b> {best_match}\n🔥 <b>Accuracy:</b> <code>{m_count*10}%</code>"
        return "⏳ <b>Analyzing Market...</b>"
    except:
        return None

# --- Keyboards ---
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

# --- Handlers ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if not is_subscribed(uid):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"))
        bot.send_message(uid, "❌ <b>Join Our Channel!</b>", reply_markup=markup, parse_mode="HTML")
        return
    update_user(uid)
    bot.send_message(uid, "👋 Welcome!", reply_markup=main_menu(), parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "🛠 Admin Panel:", reply_markup=admin_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid = message.from_user.id
    limit, status = get_user_info(uid)
    if status == 'banned': return

    if message.text == "🎰 Get Prediction":
        if limit <= 0 and status != 'vip':
            bot.send_message(uid, "❌ No Credits!")
            return
        res = get_prediction()
        if res:
            if "Analyzing" not in res and status != 'vip': update_user(uid, limit=limit-1)
            bot.send_message(uid, f"🎰 <b>Result:</b>\n\n{res}\n\n👤 Owner: {OWNER_TAG}", parse_mode="HTML")

    elif message.text == "📺 Watch Ad (5 Credit)":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔗 Watch", url=ADS_LINK))
        markup.add(telebot.types.InlineKeyboardButton("✅ Claim", callback_data="claim"))
        bot.send_message(uid, "Click Watch, wait 10s, then Claim.", reply_markup=markup)

    elif message.text == "👤 My Account":
        bot.send_message(uid, f"💰 Credit: {limit}\n🌟 Status: {status.upper()}", parse_mode="HTML")

    elif message.text == "📢 Support":
        bot.send_message(uid, f"Contact: {OWNER_TAG}")

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    uid = call.from_user.id
    if call.data == "claim":
        update_user(uid, limit=get_user_info(uid)[0]+5)
        bot.answer_callback_query(call.id, "✅ Added!")
        bot.edit_message_text("✅ Reward Claimed!", chat_id=call.message.chat.id, message_id=call.message.message_id)
    elif call.data.startswith("a_") and uid == ADMIN_ID:
        act = call.data.split("_")[1]
        m = bot.send_message(ADMIN_ID, f"Send data for {act.upper()}:")
        bot.register_next_step_handler(m, admin_action, act)

def admin_action(message, act):
    try:
        if act == "add":
            target, amt = message.text.split()
            update_user(int(target), limit=get_user_info(int(target))[0]+int(amt))
            bot.send_message(ADMIN_ID, "✅ Added!")
        elif act == "bc":
            conn = sqlite3.connect('users.db')
            users = conn.execute("SELECT user_id FROM users").fetchall()
            for u in users:
                try: bot.send_message(u[0], f"📢 {message.text}", parse_mode="HTML")
                except: pass
            bot.send_message(ADMIN_ID, "✅ Sent!")
    except: bot.send_message(ADMIN_ID, "❌ Error!")

if __name__ == "__main__":
    init_db()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
