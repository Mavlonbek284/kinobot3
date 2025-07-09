import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Token va admin ID
BOT_TOKEN = '8186601135:AAFy2WbGO7mzCJHrEV9jYoOOFHxunh3DbOc'
bot = telebot.TeleBot(BOT_TOKEN)
ADMIN_ID = 5091776192
ADMINS = [ADMIN_ID]

# Fayl nomlari
KINOLAR_FILE = 'kinolar.json'
USERS_FILE = 'users.json'
CHANNELS_FILE = 'channels.json'

# Foydalanuvchilar va admin holati
foydalanuvchilar = set()
kutilayotganlar = {}

# Kanal ro‘yxati
DEFAULT_CHANNELS = [
    {"username": "@Daqiqauzb24", "name": "Daqiqauzb24"},
    {"username": "@TarjimaKinoPlusbot", "name": "TarjimaKinoPlusbot"}
]

# Kanallar fayli mavjud bo‘lmasa, yaratiladi
if not os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, 'w') as f:
        json.dump({"channels": DEFAULT_CHANNELS}, f, indent=4)

# Kinolarni yuklash va saqlash
def yukla_kinolar():
    return json.load(open(KINOLAR_FILE)) if os.path.exists(KINOLAR_FILE) else {}

def saqla_kinolar(k):
    json.dump(k, open(KINOLAR_FILE, 'w'), indent=2)

KINOLAR = yukla_kinolar()

# Obuna tekshirish funksiyasi
def obuna_tekshir(user_id):
    if user_id in ADMINS:
        return True
    with open(CHANNELS_FILE, 'r') as f:
        channels = json.load(f)["channels"]
    for ch in channels:
        try:
            status = bot.get_chat_member(ch["username"], user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# Obuna qilish uchun tugmalar
def send_obuna_ilang(chat_id):
    with open(CHANNELS_FILE, 'r') as f:
        channels = json.load(f)["channels"]
    kb = InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        kb.add(InlineKeyboardButton("+Obuna bo‘ling", url=f"https://t.me/{ch['username'].lstrip('@')}"))
    kb.add(InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subs"))
    bot.send_message(chat_id, "🔒 Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo‘ling:", reply_markup=kb)

# /start komandasi
@bot.message_handler(commands=['start'])
def boshlash(message):
    user_id = str(message.chat.id)
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    except:
        users = {}

    if user_id not in users:
        users[user_id] = {"name": message.from_user.first_name}
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)

    if not obuna_tekshir(message.chat.id):
        send_obuna_ilang(message.chat.id)
    else:
        bot.send_message(message.chat.id, "🎬 Kino kodini kiriting (masalan: 1, 2, 3):")

# Obuna tekshirish tugmasi
@bot.callback_query_handler(func=lambda c: c.data == "check_subs")
def obuna_callback(c):
    uid = c.from_user.id
    cid = c.message.chat.id
    if obuna_tekshir(uid):
        bot.answer_callback_query(c.id, "✅ Obuna tasdiqlandi!")
        bot.send_message(cid, "🎬 Endi kino kodini kiriting:")
    else:
        bot.answer_callback_query(c.id, "❌ Obuna hali aniqlanmadi.")
        send_obuna_ilang(cid)

# Kino ko‘rsatish
@bot.message_handler(func=lambda m: m.text and m.text.isdigit())
def kino_ber(message):
    user_id = message.from_user.id
    kod = message.text.strip()
    foydalanuvchilar.add(user_id)

    if not obuna_tekshir(user_id):
        send_obuna_ilang(message.chat.id)
        return

    if kod in KINOLAR:
        kino = KINOLAR[kod]
        bot.send_video(message.chat.id, kino["file_id"], caption=f"🎬 {kino['nomi']}\n📅 {kino['yili']}")
    else:
        bot.send_message(message.chat.id, "❌ Bunday koddagi kino topilmadi.")

# Admin video yuboradi
@bot.message_handler(content_types=['video'])
def admin_video_qabul(message):
    if message.from_user.id == ADMIN_ID:
        file_id = message.video.file_id
        kutilayotganlar[message.from_user.id] = {"file_id": file_id}
        bot.send_message(message.chat.id, "📌 Kino nomini kiriting:")
    else:
        bot.reply_to(message, "❌ Siz admin emassiz.")

# Admin nom va yil kiritadi
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.from_user.id in kutilayotganlar)
def admin_nom_yil(message):
    state = kutilayotganlar.get(message.from_user.id)
    if 'nomi' not in state:
        state['nomi'] = message.text
        bot.send_message(message.chat.id, "📅 Kino yilini kiriting:")
    elif 'yili' not in state:
        state['yili'] = message.text
        yangi_id = str(len(KINOLAR) + 1)
        KINOLAR[yangi_id] = {
            "file_id": state['file_id'],
            "nomi": state['nomi'],
            "yili": state['yili']
        }
        saqla_kinolar(KINOLAR)
        bot.send_message(message.chat.id, f"✅ Kino saqlandi! ID: {yangi_id}")
        del kutilayotganlar[message.from_user.id]

# Kino o‘chirish komandasi
@bot.message_handler(commands=['delete'])
def delete_kino(message):
    try:
        _, kino_id = message.text.split()
        if kino_id in KINOLAR:
            del KINOLAR[kino_id]
            saqla_kinolar(KINOLAR)
            bot.reply_to(message, f"Kino ID {kino_id} o‘chirildi.")
        else:
            bot.reply_to(message, f"Kino ID {kino_id} topilmadi.")
    except Exception as e:
        bot.reply_to(message, f"Xatolik: {e}\nTo‘g‘ri format: /delete 1")

# Kino tahrirlash komandasi
@bot.message_handler(commands=['edit'])
def edit_kino(message):
    try:
        cmd = message.text.split(' ', 1)[1]
        kino_id, yangi_nomi, yangi_yili = map(str.strip, cmd.split('|'))
        if kino_id in KINOLAR:
            KINOLAR[kino_id]["nomi"] = yangi_nomi
            KINOLAR[kino_id]["yili"] = yangi_yili
            saqla_kinolar(KINOLAR)
            bot.reply_to(message, f"Kino ID {kino_id} tahrirlandi ✅\n📝 {yangi_nomi} ({yangi_yili})")
        else:
            bot.reply_to(message, f"Kino ID {kino_id} topilmadi.")
    except Exception as e:
        bot.reply_to(message, f"Xatolik: {e}\nTo‘g‘ri format:\n/edit 1 | Yangi nom | 2025")

# Statistika
@bot.message_handler(commands=['stats'])
def show_stats(message):
    try:
        total_kinolar = len(KINOLAR)
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        total_users = len(users)
        bot.send_message(message.chat.id, f"📊 Statistika:\n👤 Foydalanuvchilar: {total_users}\n🎥 Kinolar: {total_kinolar}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

# Ishga tushirish
print("✅ Bot ishlayapti...")
bot.polling(none_stop=True)