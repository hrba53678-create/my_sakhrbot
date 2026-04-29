import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    # هذا السطر هو الأهم للتشغيل على Render
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()


import os, telebot, sqlite3, requests, re, time, asyncio, edge_tts
from telebot import types

# --- 1. الإعدادات ---
API_TOKEN = '8612948095:AAGh5_Wl8Bb89Bv3j0xlHoEIYyyEj31CzdY' 
CH_ID = -1003982280092  
CH_LINK = 'https://t.me/+TWfwB6wfdNw5YWVk'
bot = telebot.TeleBot(API_TOKEN)
VOICE = "ar-EG-SalmaNeural"

# قاعدة البيانات
conn = sqlite3.connect('users_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, points INTEGER, referrals INTEGER, invited_by INTEGER)''')
conn.commit()

POINTS_FOR_MINING = 20 

# --- 2. دالة جلب الأرقام ---
def fetch_numbers():
    try:
        # مواقع توفر أرقام وهمية للتفعيل
        url = "https://receive-smss.com/"
        res = requests.get(url, timeout=10).text
        nums = re.findall(r'\+\d{10,15}', res)
        return list(set(nums))[:10] # جلب أول 10 أرقام فريدة
    except:
        return ["+12025550123", "+447700900123"] # أرقام احتياطية في حال تعطل الموقع

# --- 3. دالة تحويل الصوت ---
async def create_voice(text, filename):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)

# --- 4. الوظائف المساعدة ---
def get_user(user_id):
    cursor.execute("SELECT points, referrals, invited_by FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT INTO users VALUES (?, 0, 0, NULL)", (user_id,))
        conn.commit()
        return (0, 0, None)
    return res

def check_sub(user_id):
    try:
        status = bot.get_chat_member(CH_ID, user_id).status
        return status in ['member', 'creator', 'administrator']
    except: return False

def main_menu(user_id):
    points, _, _ = get_user(user_id)
    mine_status = "✅" if points >= POINTS_FOR_MINING else "🔒"
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton(f"📸 تلغيم صورة {mine_status}"),
        types.KeyboardButton("📱 جلب أرقام وهمية"),
        types.KeyboardButton("🎙️ تحويل نص لصوت"),
        types.KeyboardButton("👤 إحصائياتي"),
        types.KeyboardButton("🔗 رابط الدعوة")
    )
    return markup

# --- 5. معالجة الرسائل ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not check_sub(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("انضم للقناة أولاً 📢", url=CH_LINK))
        bot.send_message(message.chat.id, "⚠️ اشترك بالقناة لتفعيل البوت!", reply_markup=markup)
        return

    # الترحيب بالقيادة
    bot.send_message(message.chat.id, "أهلاً بالقيادة أبو حرب! 🦅 البوت تحت أمرك.", reply_markup=main_menu(user_id))

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    if not check_sub(user_id): return

    p, r, _ = get_user(user_id)

    if message.text == "📱 جلب أرقام وهمية":
        bot.send_message(message.chat.id, "📡 جاري سحب أرقام جديدة...")
        nums = fetch_numbers()
        bot.send_message(message.chat.id, "✅ الأرقام المتاحة حالياً:\n\n" + "\n".join([f"`{n}`" for n in nums]), parse_mode="Markdown")

    elif message.text == "🎙️ تحويل نص لصوت":
        msg = bot.send_message(message.chat.id, "أرسل النص الذي تريد تحويله لبصمة صوتية:")
        bot.register_next_step_handler(msg, process_voice)

    elif "تلغيم صورة" in message.text:
        if p < POINTS_FOR_MINING:
            bot.send_message(message.chat.id, f"🔒 الميزة تتطلب {POINTS_FOR_MINING} نقطة. لديك {p}.")
        else:
            bot.send_message(message.chat.id, "🛠️ أرسل رابط التتبع للبدء.")

    elif message.text == "👤 إحصائياتي":
        bot.send_message(message.chat.id, f"📊 إحصائياتك:\n💰 النقاط: {p}\n👥 الإحالات: {r}")

    elif message.text == "🔗 رابط الدعوة":
        link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        bot.send_message(message.chat.id, f"🎁 رابط دعوتك:\n`{link}`", parse_mode="Markdown")

def process_voice(message):
    text = message.text
    if not text: return
    file_path = f"voice_{message.from_user.id}.mp3"
    bot.send_message(message.chat.id, "⏳ جاري توليد الصوت...")
    asyncio.run(create_voice(text, file_path))
    with open(file_path, "rb") as audio:
        bot.send_voice(message.chat.id, audio, caption="✅ تم التحويل بواسطة بوت القيادة")
    os.remove(file_path)

if __name__ == "__main__":
    print("🚀 البوت يعمل الآن بكامل الميزات يا قيادة!")
    bot.polling(none_stop=True)

keep_alive()
