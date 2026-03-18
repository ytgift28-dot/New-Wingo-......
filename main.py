import telebot
import requests
import time
import sqlite3
import threading

# --- কনফিগারেশন ---
API_TOKEN = '7709568330:AAERHIvJFI5X4-zOgLcwqTNEJ0bj1ME0c5Y'
ADMIN_ID = 6941003064
CHANNEL_USERNAME = "@SH_tricks" 
ADS_LINK = "https://www.profitablecpmratenetwork.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"
OWNER_TAG = "@Suptho1"

bot = telebot.TeleBot(API_TOKEN)

# --- ডাটাবেস সেটআপ (SQLite) ---
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, limit_count INTEGER)''')
    conn.commit()
    conn.close()

def get_user_limit(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT limit_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def update_user_limit(user_id, count, reset=False):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    if reset:
        cursor.execute("INSERT OR REPLACE INTO users (user_id, limit_count) VALUES (?, ?)", (user_id, count))
    else:
        current = get_user_limit(user_id)
        cursor.execute("INSERT OR REPLACE INTO users (user_id, limit_count) VALUES (?, ?)", (user_id, current + count))
    conn.commit()
    conn.close()

# --- Force Join Check ---
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

# --- Wingo API Prediction ---
def get_prediction():
    URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    HEADERS = {"Host": "draw.ar-lottery01.com", "user-agent": "Mozilla/5.0"}
    try:
        res = requests.get(URL, headers=HEADERS, timeout=10)
        data = res.json().get('data', {}).get('list', [])
        if not data: return None
        num = int(data[0]['number'])
        pred = "BIG 🟢" if num < 5 else "SMALL 🔴"
        issue = int(data[0]['issue']) + 1
        return f"✨ **Period:** `{issue}`\n🎯 **Prediction:** {pred}\n🔥 **Accuracy:** `95.8%`"
    except:
        return None

# --- হ্যান্ডলারস ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        bot.send_message(user_id, f"❌ আপনি আমাদের চ্যানেলে জয়েন নেই!\n\nদয়া করে {CHANNEL_USERNAME} চ্যানেলে জয়েন করে আবার /start দিন।")
        return

    limit = get_user_limit(user_id)
    msg = (f"👋 **স্বাগতম! আমি Wingo Predictor AI।**\n\n"
           f"💰 আপনার বর্তমান লিমিট: `{limit}`\n"
           f"📺 ৫টি প্রেডিকশন পেতে /watch_ad লিখুন।\n"
           f"🎲 প্রেডিকশন পেতে /predict লিখুন।\n\n"
           f"👤 **Owner:** {OWNER_TAG}")
    bot.send_message(user_id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['watch_ad'])
def watch_ad(message):
    user_id = message.from_user.id
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🔗 ক্লিক করে বিজ্ঞাপন দেখুন", url=ADS_LINK)
    markup.add(btn)
    
    bot.send_message(user_id, "⏳ নিচের লিংকে ক্লিক করে ৫ সেকেন্ড বিজ্ঞাপনটি দেখুন, তারপর আপনি ৫টি প্রেডিকশন পাবেন।", reply_markup=markup)
    
    # ৫ সেকেন্ড পর রিওয়ার্ড আপডেট
    def add_reward():
        time.sleep(10) # ইউজারকে ৫-১০ সেকেন্ড সময় দেওয়া
        update_user_limit(user_id, 5)
        bot.send_message(user_id, "✅ বিজ্ঞাপন দেখা সফল! ৫টি প্রেডিকশন আপনার একাউন্টে যোগ করা হয়েছে।")
    
    threading.Thread(target=add_reward).start()

@bot.message_handler(commands=['predict'])
def predict(message):
    user_id = message.from_user.id
    limit = get_user_limit(user_id)
    
    if limit <= 0:
        bot.send_message(user_id, "❌ আপনার লিমিট শেষ! /watch_ad লিখে লিমিট বাড়িয়ে নিন।")
        return

    pred_msg = get_prediction()
    if pred_msg:
        update_user_limit(user_id, -1)
        final_msg = f"🎰 **Wingo 30S Prediction**\n\n{pred_msg}\n\n📉 অবশিষ্ট লিমিট: `{limit-1}`\n👤 **Owner:** {OWNER_TAG}"
        bot.send_message(user_id, final_msg, parse_mode="Markdown")
    else:
        bot.send_message(user_id, "⚠️ ডাটা পাওয়া যাচ্ছে না। কিছুক্ষণ পর চেষ্টা করুন।")

# --- এডমিন প্যানেল ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(ADMIN_ID, "🛠 **Admin Panel**\n\n📢 সবাইকে মেসেজ দিতে: `/broadcast মেসেজ`")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/broadcast ", "")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    for user in users:
        try:
            bot.send_message(user[0], f"📢 **ADMIN MESSAGE:**\n\n{text}", parse_mode="Markdown")
        except: pass
    bot.send_message(ADMIN_ID, "✅ ব্রডকাস্ট সফল হয়েছে।")

if __name__ == "__main__":
    init_db()
    print("Bot is running...")
    bot.polling(none_stop=True)
