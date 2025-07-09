import telebot
import json
import os

BOT_TOKEN = '8186601135:AAFy2WbGO7mzCJHrEV9jYoOOFHxunh3DbOc'
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 5091776192
KANALLAR = ['@Daqiqauzb24', '@TarjimaKinoPlusbot']

foydalanuvchilar = set()
kutilayotganlar = {}
KINOLAR_FILE = 'kinolar.json'

def yukla_kinolar():
    if os.path.exists(KINOLAR_FILE):
        with open(KINOLAR_FILE, 'r') as f:
            return json.load(f)
    return {}

def saqla_kinolar(kinolar):
    with open(KINOLAR_FILE, 'w') as f:
        json.dump(kinolar, f, indent=2)

KINOLAR = yukla_kinolar()

def obuna_tekshir(user_id):
    if user_id == ADMIN_ID:
        return True
    for kanal in KANALLAR:
        try:
            member = bot.get_chat_member(kanal, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

@bot.message_handler(commands=['start'])
def boshlash(message):
    foydalanuvchilar.add(message.from_user.id)
    bot.send_message(message.chat.id, "🎬 Kino kodini kiriting (masalan: 1, 2, 3):")

@bot.message_handler(func=lambda m: m.text.isdigit())
def kino_ber(message):
    user_id = message.from_user.id
    kod = message.text.strip()

    foydalanuvchilar.add(user_id)

    if not obuna_tekshir(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        for kanal in KANALLAR:
            markup.add(telebot.types.InlineKeyboardButton("➕ Obuna bo‘lish", url=f"https://t.me/{kanal.strip('@')}"))
        markup.add(telebot.types.InlineKeyboardButton("✅ Tekshirish", callback_data='check_sub'))
        bot.send_message(message.chat.id, "📛 Iltimos, quyidagi kanallarga obuna bo‘ling:", reply_markup=markup)
        return

    if kod in KINOLAR:
        kino = KINOLAR[kod]
        bot.send_video(message.chat.id, kino["file_id"], caption=f"🎬 {kino['nomi']}\n📅 {kino['yili']}")
    else:
        bot.send_message(message.chat.id, "❌ Bunday koddagi kino topilmadi.")

@bot.callback_query_handler(func=lambda call: call.data == 'check_sub')
def tekshir_callback(call):
    user_id = call.from_user.id
    if obuna_tekshir(user_id):
        bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi.")
        bot.send_message(call.message.chat.id, "✅ Endi kino kodini kiriting:")
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo‘lmagansiz.")

@bot.message_handler(content_types=['video'])
def admin_video_qabul(message):
    if message.from_user.id == ADMIN_ID:
        file_id = message.video.file_id
        kutilayotganlar[message.from_user.id] = {"file_id": file_id}
        bot.send_message(message.chat.id, "📌 Kino nomini kiriting:")
    else:
        bot.reply_to(message, "❌ Siz admin emassiz.")

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
        bot.send_message(message.chat.id, f"✅ Kino saqlandi!\nID: {yangi_id}\n🎬 {state['nomi']} ({state['yili']})")
        del kutilayotganlar[message.from_user.id]

@bot.message_handler(commands=['stat'])
def statistika(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"📊 Foydalanuvchilar soni: {len(foydalanuvchilar)}")
    else:
        bot.send_message(message.chat.id, "❌ Bu buyruq faqat admin uchun.")

bot.polling()