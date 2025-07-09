import telebot
import json
import os

BOT_TOKEN = '8186601135:AAFy2WbGO7mzCJHrEV9jYoOOFHxunh3DbOc'
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 5091776192
ADMINS = [ADMIN_ID]
KINOLAR_FILE = 'kinolar.json'
USERS_FILE = 'users.json'
CHANNELS_FILE = 'channels.json'

foydalanuvchilar = set()
kutilayotganlar = {}

# Majburiy kanallar ro‘yxati
DEFAULT_CHANNELS = [
    {"username": "@Daqiqauzb24", "name": "Daqiqauzb24"},
    {"username": "@TarjimaKinoPlusbot", "name": "TarjimaKinoPlusbot"}
]

# Kanallar faylini yaratish (agar mavjud bo‘lmasa)
def tekshir_va_yarat_channel_file():
    if not os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, 'w') as f:
            json.dump({"channels": DEFAULT_CHANNELS}, f, indent=4)

tekshir_va_yarat_channel_file()

# Kinolarni yuklash/saqlash
def yukla_kinolar():
    if os.path.exists(KINOLAR_FILE):
        with open(KINOLAR_FILE, 'r') as f:
            return json.load(f)
    return {}

def saqla_kinolar(kinolar):
    with open(KINOLAR_FILE, 'w') as f:
        json.dump(kinolar, f, indent=2)

KINOLAR = yukla_kinolar()

# Obuna tekshiruv
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

    bot.send_message(message.chat.id, "🎬 Kino kodini kiriting (masalan: 1, 2, 3):")

@bot.message_handler(func=lambda m: m.text.isdigit())
def kino_ber(message):
    user_id = message.from_user.id
    kod = message.text.strip()
    foydalanuvchilar.add(user_id)

    if not obuna_tekshir(user_id):
        with open(CHANNELS_FILE, "r") as f:
            channels = json.load(f)["channels"]
        matn = "🔒 Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo‘ling:\n\n"
        matn += "\n".join([f"👉 {ch['name']} ({ch['username']})" for ch in channels])
        matn += "\n\n✅ Obunadan so‘ng qayta /start buyrug‘ini bering."
        bot.send_message(message.chat.id, matn)
        return

    if kod in KINOLAR:
        kino = KINOLAR[kod]
        bot.send_video(message.chat.id, kino["file_id"], caption=f"🎬 {kino['nomi']}\n📅 {kino['yili']}")
    else:
        bot.send_message(message.chat.id, "❌ Bunday koddagi kino topilmadi.")

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
        bot.send_message(message.chat.id, f"✅ Kino saqlandi! ID: {yangi_id}")
        del kutilayotganlar[message.from_user.id]

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

@bot.message_handler(commands=['stats'])
def show_stats(message):
    try:
        total_kinolar = len(KINOLAR)
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        total_users = len(users)
        text = f"📊 Statistika:\n👥 Foydalanuvchilar: {total_users}\n🎞 Kinolar: {total_kinolar}"
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, f"Xatolik: {e}")

@bot.message_handler(commands=['addchannel'])
def add_channel(message):
    if message.chat.id not in ADMINS:
        return
    try:
        _, username, name = message.text.split(' ', 2)
        with open(CHANNELS_FILE, "r") as f:
            data = json.load(f)
        data["channels"].append({"username": username, "name": name})
        with open(CHANNELS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        bot.reply_to(message, f"✅ Kanal qo‘shildi: {name} ({username})")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}\nFoydalanish: /addchannel @username Nomi")

@bot.message_handler(commands=['delchannel'])
def delete_channel(message):
    if message.chat.id not in ADMINS:
        return
    try:
        _, username = message.text.split()
        with open(CHANNELS_FILE, "r") as f:
            data = json.load(f)
        data["channels"] = [ch for ch in data["channels"] if ch["username"] != username]
        with open(CHANNELS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        bot.reply_to(message, f"🗑 O‘chirildi: {username}")
    except Exception as e:
        bot.reply_to(message, f"Xatolik: {e}\nFoydalanish: /delchannel @username")

@bot.message_handler(commands=['channels'])
def show_channels(message):
    if message.chat.id not in ADMINS:
        return
    with open(CHANNELS_FILE, "r") as f:
        chs = json.load(f)["channels"]
    msg = "📢 Obuna kanallari:\n"
    for ch in chs:
        msg += f"🔹 {ch['name']} - {ch['username']}\n"
    bot.reply_to(message, msg)

print("✅ Bot ishga tushdi...")
bot.polling(none_stop=True)