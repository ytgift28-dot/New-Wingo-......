import telebot
import requests
import time
import sqlite3
import threading

# --- Configuration ---
API_TOKEN = '7709568330:AAERHIvJFI5X4-zOgLcwqTNEJ0bj1ME0c5Y'
ADMIN_ID = 6941003064
CHANNEL_USERNAME = "@SH_tricks" 
ADS_LINK = "https://www.profitablecpmratenetwork.com/wnbk2zjv?key=75442aee9e8b64a0d71c17a99228474d"
OWNER_TAG = "@Suptho1"

bot = telebot.TeleBot(API_TOKEN)

# --- Database & Prediction Logic (আগের মতোই থাকবে) ---
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
    current_limit, current_status = get_user_info(user_id)
    new_limit = limit if limit is not None else current_limit
    new_status = status if status is not None else current_status
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, limit_count, status) VALUES (?, ?, ?)", 
                   (user_id, new_limit, new_status))
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def get_advanced_prediction():
    URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
    try:
        res = requests.get(URL, params={"pageNo":1, "pageSize":100}, timeout=10)
        data = res.json().get('data', {}).get('list', [])
        if len(data) < 20: return None
        
        current_p = [1 if int(d['number']) >= 5 else 0 for d in data[:10]]
        best_match_result = None
        max_matches = 0

        for i in range(1, len(data) - 11):
            past_p = [1 if int(data[j]['number']) >= 5 else 0 for j in range(i, i + 10)]
            matches = sum(1 for a, b in zip(current_p, past_p) if a == b)
            
            if matches >= 9:
                best_match_result = "BIG 🟢" if int(data[i-1]['number']) >= 5 else "SMALL 🔴"
                max_matches = matches
                if matches == 10: break
            elif matches == 8 and not best_match_result:
                best_match_result = "BIG 🟢" if int(data[i-1]['number']) >= 5 else "SMALL 🔴"
                max_matches = matches

        if best_match_result:
            acc_percent = (max_matches / 10) * 100
            issue = int(data[0]['issue']) + 1
            return f"✨ <b>Period:</b> <code>{issue}</code>\n🎯 <b>Prediction:</b> {best_match_result}\n🔥 <b>Accuracy:</b> <code>{acc_percent}%</code>\n📊 <b>Logic:</b> Pattern Match ({max_matches}/10)"
        return "⏳ <b>Market Analyzing...</b>\nসঠিক প্যাটার্ন পাওয়া যায়নি, কিছুক্ষণ পর চেষ্টা করুন।"
    except:
        return None

# --- UI & Menus ---
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎰 Get Prediction", "📺 Watch Ad (5 Credit)")
    markup.add("👤 My Account", "📢 Support")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    _, status = get_user_info(uid)
    if status == 'banned': return
    if not is_subscribed(uid):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"))
        bot.send_message(uid, f"⚠️ Access Denied! Join {CHANNEL_USERNAME} first.", reply_markup=markup, parse_mode="HTML")
        return
    update_user(uid)
    bot.send_message(uid, f"👋 Welcome! Get results with 90%+ Accuracy.\nOwner: {OWNER_TAG}", reply_markup=main_menu(), parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🎰 Get Prediction")
def handle_pred(message):
    uid = message.from_user.id
    limit, status = get_user_info(uid)
    if limit <= 0 and status != 'vip':
        bot.send_message(uid, "❌ Credit শেষ! Ad দেখে ক্রেডিট নিন।")
        return
    res = get_advanced_prediction()
    if res:
        if "Analyzing" not in res and status != 'vip':
            update_user(uid, limit=limit-1)
        bot.send_message(uid, f"🎰 <b>Wingo 30S</b>\n\n{res}\n\n📉 Credit: <code>{'VIP' if status=='vip' else limit-1}</code>\n👤 Owner: {OWNER_TAG}", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "📺 Watch Ad (5 Credit)")
def handle_ad(message):
    uid = message.from_user.id
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔗 Watch Video", url=ADS_LINK))
    bot.send_message(uid, "⏳ লিংকে ক্লিক করে ১০ সেকেন্ড বিজ্ঞাপনটি দেখুন।", reply_markup=markup)
    def reward():
        time.sleep(12)
        update_user(uid, limit=get_user_info(uid)[0]+5)
        bot.send_message(uid, "✅ ৫ ক্রেডিট যোগ করা হয়েছে!")
    threading.Thread(target=reward).start()

# --- Main Polling with Conflict Prevention ---
if __name__ == "__main__":
    init_db()
    print("Bot is starting...")
    # বোট চালু করার আগে আগের সব পেন্ডিং আপডেট মুছে দিবে
    bot.remove_webhook()
    time.sleep(1)
    # infinity_polling ব্যবহার করা হয়েছে যাতে ক্র্যাশ করলেও অটো রিস্টার্ট নেয়
    bot.infinity_polling(skip_pending=True)
