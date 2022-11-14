print("OpenHavroniya\n      by Andrey Daniluk and TideSoft!\nLoading...")
print("Import modules...")
import os, os.path, sys, random, sqlite3, configparser, threading, time, telebot, string
from datetime import timedelta
from telebot import types
from uptime import uptime
os.system("title OpenHavroniya Telegram server")
print("Connect to database...")
conn = sqlite3.connect('db.sqlite', check_same_thread=False)
cursor = conn.cursor()
lock = threading.Lock()
cursor.execute("CREATE TABLE IF NOT EXISTS openhavroniya (inttxt, outtxt)")
cursor.execute("CREATE TABLE IF NOT EXISTS openhavroniya_photo (inttxt, outtxt, photo)")
cursor.execute("CREATE TABLE IF NOT EXISTS openhavroniya_block_users (userid, reason, block_date, first_name, last_name, by_admin)")
cursor.execute("CREATE TABLE IF NOT EXISTS openhavroniya_block_chats (chat_id, reason, chat_name, block_date, by_admin)")
cursor.execute("CREATE TABLE IF NOT EXISTS openhavroniya_admins (userid)")
conn.commit()
cursor.execute("SELECT * FROM openhavroniya_admins")
if cursor.fetchall() == []:
    print("Error: Admin list are empty. Please, enter your user id")
    finish = False
    while finish == False:
        adminid = input("User id> ")
        try:
            adminid_int = int(adminid)
        except:
            print("Error: The user id must only consist of digits without a negative sign")
        else:
            if adminid_int > 0:
                if "." in adminid:
                    print("Error: The user id must only consist of digits without a negative sign")
                else:
                    finish = True
            else:
                print("Error: The user id must only consist of digits without a negative sign")
    cursor.execute(f"INSERT INTO openhavroniya_admins (userid) VALUES ('{adminid}')")
    conn.commit()
print("Preparing no_photo.png...")
if not os.path.exists("no_photo.png"):
    print("ERROR: File no_photo.png not found. Please download it from repository, or paste your photo with name \"no_photo.png\"")
    exit()
else:
    no_photo = open("no_photo.png", "rb").read()
print("Inzialite variables...")
errors_count = 0
new_replys = 0
messages_get = 0
photo_new_replys = 0
sends_replys = 0
sends_photos = 0
deleted_replys = 0
replys_visited = 0
bannedusertext = "Увы, но вы были забанены. Причина бана: {reason}\n\nЕсли есть вопросы, задавайте в t.me/andrey_daniluk"
print("Inzialite functions")
def dbexec(command, save=True, additional_parameters=None):
    try:
        lock.acquire(True)
        if additional_parameters == None:
            cursor.execute(command)
        else:
            cursor.execute(command, additional_parameters)
    finally:
        lock.release()
    if save == True:
        conn.commit()
    return cursor.fetchall()

class bm:
    memory = {}

    def get(button_code):
        try:
            text_from_code = bm.memory[button_code]
        except:
            return None
        else:
            return text_from_code
        
    def new(memory_text):
        pas = False
        while pas == False:
            letters_and_digits = string.ascii_letters + string.digits
            rand_string = ''.join(random.sample(letters_and_digits, 40))
            try:
                bm.memory[rand_string]
            except:
                pas = True
        bm.memory[rand_string] = memory_text
        return rand_string

    def delete(button_code):
        try:
            del bm.memory[button_code]
        except:
            return 0;
        return 0;

print("Inzialite libs to work...")
start_time = time.time()
config = configparser.ConfigParser()
if not os.path.exists("./photo-memory/"):
    os.makedirs("./photo-memory/")
if not os.path.exists("config.ini"):
    print("Error: Config not found. Let`s to create it!")
    intk = input("Your TG token: ")
    with open("config.ini", "w") as wicicnf:
        wicicnf.write("[tg]\ntoken = " + intk)
config.read("config.ini")
bot = telebot.TeleBot(config.get("tg", "token"), parse_mode=None)


print("Inzialite telebot commands, and try to start bot")


@bot.message_handler(commands=['admin'])
def adminpanel(message):
    bot.send_chat_action(message.chat.id, 'typing')
    adminslist = dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{message.from_user.id}'")
    if adminslist != []:

        adminscount = len(dbexec(f"SELECT userid FROM openhavroniya_admins"))
        blocked_user_count = len(dbexec(f"SELECT userid FROM openhavroniya_block_users"))
        blocked_chat_count = len(dbexec(f"SELECT chat_id FROM openhavroniya_block_chats"))

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton(text="⚙️ Настройки", callback_data=bm.new("settings")))
        keyboard.row(types.InlineKeyboardButton(text="💬 Заблокированые чаты", callback_data=bm.new("blocked_chats")))
        keyboard.row(types.InlineKeyboardButton(text="👤 Заблокированые пользователи", callback_data=bm.new("blocked_users")))
        bot.reply_to(message, f"👮‍♂️ Админ панель:\n\n👤 Заблокированые пользователи: {blocked_user_count}шт.\n💬 Заблокированые чаты: {blocked_chat_count}шт.\n👮‍♂️ Количество админов: {adminscount}шт.", reply_markup=keyboard)
    else:
        bot.reply_to(message, "🚫 Вы не являетесь админом бота, чтобы получить доступ к админ панели")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    calldatacode = call.data

    calldatatext = bm.get(calldatacode)

    if calldatatext == None:
        bot.answer_callback_query(callback_query_id=call.id, text='Код этой кнопки не найден в базе данных. Возможно вы пытаетесь на неё нажать после перезагрузки бота')
        return 0;
    call.data = calldatatext
    rmbc = True
    if call.message:
        bot.send_chat_action(call.message.chat.id, 'typing')
        adminslist = dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{call.from_user.id}'")
        if call.data == "f":
            rmbc = False
            bot.answer_callback_query(callback_query_id=call.id, text="🚫 К сожалению эта возможность в доработке. Если вы знаете Python, вы можете помочь сделать её.", show_alert=True)
        
        if call.data.startswith("images:list:"):
            query = call.data.split(":", maxsplit=2)[-1]
            photolist = dbexec("SELECT photo, outtxt FROM openhavroniya_photo WHERE inttxt=?", additional_parameters=[(query)])
            if photolist == []:
                bot.edit_message_media(chat_id=call.message.chat.id,message_id=call.message.message_id,media=types.InputMediaPhoto(no_photo))
                bot.bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=str(f"Найти фото по запросу \"{query}\" не удалось. Может быть его уже удалили, или вы написали что-то не так."), reply_markup=None)
            else:
                keyboard = types.InlineKeyboardMarkup()
                for photo in photolist:
                    keyboard.row(types.InlineKeyboardButton(str(photo[0]), callback_data=bm.new("show:image:"+photo[0]+":"+query)))
                bot.edit_message_media(chat_id=call.message.chat.id,message_id=call.message.message_id,media=types.InputMediaPhoto(no_photo))
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=str(f"Вот что найшла из фото по запросу \"{query}\":"), reply_markup=keyboard)

        if call.data.startswith("show:image:"):
            print(call.data)
            filenameandquery = call.data.split(":",maxsplit=2)[-1]
            print(filenameandquery)
            filename = filenameandquery.split(":",maxsplit=1)[0]
            print(filename)
            query = filenameandquery.split(":",maxsplit=1)[1]
            print(query)

            keyboard = types.InlineKeyboardMarkup()
            if dbexec(f"SELECT * FROM openhavroniya_photo WHERE photo='{filename}'") == []:
                keyboard.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data=bm.new("images:list:"+query)))
                bot.edit_message_media(chat_id=call.message.chat.id,message_id=call.message.message_id,media=types.InputMediaPhoto(no_photo))
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"🚫 Упс... Походу это фото уже удалено", reply_markup=keyboard)
            else:
                res_text = dbexec(f"SELECT outtxt FROM openhavroniya_photo WHERE photo='{filename}'")

                if res_text == []:
                    res_text = "К этой фотографии нет прикрепленого текста."
                else:
                    if res_text[0][0] == "" or res_text[0][0] == " ":
                        res_text = "К этой фотографии нет прикрепленого текста."
                    else:
                        res_text = "Прикреплёный текст: " + str(res_text[0][0])

                keyboard.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data=bm.new("images:list:"+query)))
                keyboard.row(types.InlineKeyboardButton(text="🚫 Удалить", callback_data=bm.new("delete:image:"+filename+":"+query)))
                bot.edit_message_media(chat_id=call.message.chat.id,message_id=call.message.message_id,media=types.InputMediaPhoto(open("photo-memory/"+filename,"rb").read()))
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"Запрос: {query}\n{res_text}", reply_markup=keyboard)

        if call.data.startswith("delete:image:"):
            filenameandquery = call.data.split(":",maxsplit=2)[-1]
            filename = filenameandquery.split(":",maxsplit=1)[0]
            query = filenameandquery.split(":",maxsplit=1)[1]
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(types.InlineKeyboardButton(text="◀️ Назад", callback_data=bm.new("images:list:"+query)))
            if dbexec(f"SELECT * FROM openhavroniya_photo WHERE photo='{filename}'") == []:
                bot.edit_message_media(chat_id=call.message.chat.id,message_id=call.message.message_id,media=types.InputMediaPhoto(no_photo))
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"🚫 Упс... Походу это фото уже удалено", reply_markup=keyboard)
            else:
                os.remove("photo-memory/"+filename)
                dbexec("DELETE FROM openhavroniya_photo WHERE photo=?", additional_parameters=[(filename)])
                bot.edit_message_media(chat_id=call.message.chat.id,message_id=call.message.message_id,media=types.InputMediaPhoto(no_photo))
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"🚫 Фото успешно было удалено", reply_markup=keyboard)


        if call.data == "main":
            if adminslist != []:
                adminscount = len(dbexec(f"SELECT userid FROM openhavroniya_admins"))
                blocked_user_count = len(dbexec(f"SELECT userid FROM openhavroniya_block_users"))
                blocked_chat_count = len(dbexec(f"SELECT chat_id FROM openhavroniya_block_chats"))
                
                keyboard = types.InlineKeyboardMarkup()
                keyboard.row(types.InlineKeyboardButton(text="⚙️ Настройки", callback_data=bm.new("settings")))
                keyboard.row(types.InlineKeyboardButton(text="💬 Заблокированые чаты", callback_data=bm.new("blocked_chats")))
                keyboard.row(types.InlineKeyboardButton(text="👤 Заблокированые пользователи", callback_data=bm.new("blocked_users")))
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"👮‍♂️ Админ панель:\n\n👤 Заблокированые пользователи: {blocked_user_count}шт.\n💬 Заблокированые чаты: {blocked_chat_count}шт.\n👮‍♂️ Количество админов: {adminscount}шт.", reply_markup=keyboard)
            else:
                rmbc = False
                bot.answer_callback_query(callback_query_id=call.id, text=f'🚫 Вы не являетесь админом бота, чтобы получить доступ к админ панели', show_alert=True)

        if call.data == "settings":
            if adminslist != []:
                keyboard = types.InlineKeyboardMarkup()
                keyboard.row(types.InlineKeyboardButton(text="⏪ Назад", callback_data=bm.new("main")))
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='⚙️ Настройки', reply_markup=keyboard)
            else:
                rmbc = False
                bot.answer_callback_query(callback_query_id=call.id, text=f'🚫 Вы не являетесь админом бота, чтобы получить доступ к админ панели', show_alert=True)

        if call.data.startswith("blocked-chat-"):
            if adminslist != []:
                bc = call.data.replace("blocked-chat-", "")
                keyboard = types.InlineKeyboardMarkup()
                if dbexec(f"SELECT * FROM openhavroniya_block_chats WHERE chat_id=\"{bc}\"") != []:
                    bci = dbexec(f"SELECT * FROM openhavroniya_block_chats WHERE chat_id=\"{bc}\"")[0]
                    keyboard.row(types.InlineKeyboardButton(text="⏪ Назад", callback_data=bm.new("blocked_chats")))
                    keyboard.row(types.InlineKeyboardButton(text="🚫 Разблокировать", callback_data=bm.new(f"chat_unblock_{bc}")))
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=str(f"💬 Информация о заблокированом чате {bc}:\n\n🆔 ID чата: {bc}\n🏷 Имя чата: {bci[2]}\n📋 Причина: {bci[1]}\n🕒 Время бана: {bci[3]}\n👮‍♂ Забанен админом: {bci[4]}"), reply_markup=keyboard)
                else:
                    keyboard.row(types.InlineKeyboardButton(text="⏪ Назад", callback_data=bm.new("blocked_chats")))
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💬 Чат с id {bc} не найден в базе данных. Возможно этот чат был удалён из заблокированых перед тем, как вы нажали сюда', reply_markup=keyboard)
            else:
                rmbc = False
                bot.answer_callback_query(callback_query_id=call.id, text=f'🚫 Вы не являетесь админом бота, чтобы получить доступ к админ панели', show_alert=True)

        if call.data == "blocked_chats":
            if adminslist != []:
                keyboard = types.InlineKeyboardMarkup()
                for chatlist in dbexec("SELECT * FROM openhavroniya_block_chats"):
                    keyboard.row(types.InlineKeyboardButton(text=f"{chatlist[0]} ({chatlist[2]})", callback_data=bm.new(f"blocked-chat-{chatlist[0]}")))
                keyboard.row(types.InlineKeyboardButton(text="⏪ Назад", callback_data=bm.new("main")))
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='💬 Заблокированые чаты', reply_markup=keyboard)
            else:
                rmbc = False
                bot.answer_callback_query(callback_query_id=call.id, text=f'🚫 Вы не являетесь админом бота, чтобы получить доступ к админ панели', show_alert=True)

        if call.data == "blocked_users":
            if adminslist != []:
                keyboard = types.InlineKeyboardMarkup()
                for userlist in dbexec("SELECT * FROM openhavroniya_block_users"):
                    keyboard.row(types.InlineKeyboardButton(text=f"{userlist[0]} ({userlist[3]} {userlist[4]})", callback_data=bm.new(f"blocked-user-{userlist[0]}")))
                keyboard.row(types.InlineKeyboardButton(text="⏪ Назад", callback_data=bm.new("main")))
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='👤 Заблокированые пользователи', reply_markup=keyboard)
            else:
                rmbc = False
                bot.answer_callback_query(callback_query_id=call.id, text=f'🚫 Вы не являетесь админом бота, чтобы получить доступ к админ панели', show_alert=True)

        if call.data.startswith("blocked-user-"):
            if adminslist != []:
                guid = call.data.replace("blocked-user-","")
                bui = dbexec(f"SELECT * FROM openhavroniya_block_users WHERE userid='{guid}'")[0]
                if bui != []:
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.row(types.InlineKeyboardButton(text="⏪ Назад", callback_data=bm.new("blocked_users")))
                    keyboard.row(types.InlineKeyboardButton(text="🚫 Разблокировать", callback_data=bm.new(f"user_unblock_{guid}")))
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'👤 Информация о юзере {guid} на момент бана:\n\n🏷 Имя: {bui[3]}\n🏷 Фамилия: {bui[4]}\n🕒 Время бана: {bui[2]}\n📋 Причина бана: {bui[1]}\n👮‍♂ Забанен админом: {bui[5]}', reply_markup=keyboard)
                else:
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.row(types.InlineKeyboardButton(text="⏪ Назад", callback_data=bm.new("blocked_users")))
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'👤 Пользователь с id {guid} не был найден в базе данных заблокированых пользователей', reply_markup=keyboard)
            else:
                rmbc = False
                bot.answer_callback_query(callback_query_id=call.id, text=f'🚫 Вы не являетесь админом бота, чтобы получить доступ к админ панели', show_alert=True)

        if call.data.startswith("user_unblock_"):
            if adminslist != []:
                guid = call.data.replace("user_unblock_","")
                dbexec(f"DELETE FROM openhavroniya_block_users WHERE userid='{guid}'")
                keyboard = types.InlineKeyboardMarkup()
                keyboard.row(types.InlineKeyboardButton(text="⏪ Назад", callback_data=bm.new("blocked_users")))
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'🚫 Пользователь разблокирован.', reply_markup=keyboard)
            else:
                rmbc = False
                bot.answer_callback_query(callback_query_id=call.id, text=f'🚫 Вы не являетесь админом бота, чтобы получить доступ к админ панели', show_alert=True)

        if call.data.startswith("chat_unblock_"):
            if adminslist != []:
                guid = call.data.replace("chat_unblock_","")
                dbexec(f"DELETE FROM openhavroniya_block_chats WHERE chat_id='{guid}'")
                keyboard = types.InlineKeyboardMarkup()
                keyboard.row(types.InlineKeyboardButton(text="⏪ Назад", callback_data=bm.new("blocked_chats")))
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'🚫 Чат разблокирован.', reply_markup=keyboard)
            else:
                rmbc = False
                bot.answer_callback_query(callback_query_id=call.id, text=f'🚫 Вы не являетесь админом бота, чтобы получить доступ к админ панели', show_alert=True)

        if rmbc == True:
            bm.delete(calldatacode)

@bot.message_handler(commands=['chatinfo'])
def sysinfo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    bot.reply_to(message,f"""
📔 Информация о сервере ОпенХавронии:

🆔 ID чата: {message.chat.id}
💬 Количество сообщений в этом чате: {message.id}шт.
""")

@bot.message_handler(commands=['setadmin'])
def setadmin(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    if dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{message.from_user.id}'") != []:
        if message.reply_to_message != None:
            if dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{message.reply_to_message.from_user.id}'") == []:
                dbexec(f"INSERT INTO openhavroniya_admins (userid) VALUES ('{message.reply_to_message.from_user.id}')") 
                bot.reply_to(message, "Этот пользователь добавлен в список администраторов!")
            else:
                bot.reply_to(message, "Этот пользователь и так в списке администраторов")
        else:
            userid = message.text.split(maxsplit=1)[1]
            try:
                int(userid)
            except:
                bot.reply_to(message, "Неверный формат ид пользователя")
            else:
                if dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{userid}'") == []:
                    dbexec(f"INSERT INTO openhavroniya_admins (userid) VALUES ('{userid}')") 
                    bot.reply_to(message, "Этот пользователь добавлен в список администраторов!")
                else:
                    bot.reply_to(message, "Этот пользователь и так в списке администраторов")
    else:
        bot.reply_to(message, "Недостаточно прав, чтобы установить этого человека админом")

@bot.message_handler(commands=['userunban'])
def removeadmin(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    if dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{message.from_user.id}'") != []:
        if message.reply_to_message != None:
            if dbexec(f"SELECT userid FROM openhavroniya_block_users WHERE userid='{message.reply_to_message.from_user.id}'") != []:
                dbexec(f"DELETE FROM openhavroniya_block_users WHERE userid='{message.reply_to_message.from_user.id}'")
                bot.reply_to(message, "Этот пользователь был разбанен успешно.")
            else:
                bot.reply_to(message, "Этот пользователь и не был в бане.")
        else:
            bot.reply_to(message, "Укажите на сообщение пользователя, которого нужно разбанить")
    else:
        bot.reply_to(message, "Недостаточно прав, чтобы разбанить пользователя")

@bot.message_handler(commands=['chatban'])
def chatban(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    if dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{message.from_user.id}'") != []:
        mt = message.text.split("\n", maxsplit=1)
        if "\n" in message.text:
            reason = mt[1]
        else:
            reason = "Не указано"
        if mt[0] == "/chatban":
            chat_name = message.chat.title
            chat_id = str(message.chat.id)
        else:
            chat_name = "Не доступно"
            chat_id = mt[0].split(maxsplit=1)[1]
        if dbexec(f"SELECT chat_id FROM openhavroniya_block_chats WHERE chat_id='{chat_id}'") != []:
            bot.reply_to(message, "Этот чат и так забанен")
            return 0;
        blockdate = time.strftime("%d/%m/%y %H:%M:%S")
        dbexec(f"INSERT INTO openhavroniya_block_chats (chat_id, reason, chat_name, block_date, by_admin) VALUES (\"{chat_id}\", ?,\"{chat_name}\",\"{blockdate}\",\"{message.from_user.id}\")", additional_parameters=[(reason)])
        bot.reply_to(message, "Чат забанен")
    else:
        bot.reply_to(message, "Недостаточно прав, чтобы забанить этот чат.")

@bot.message_handler(commands=['userban'])
def removeadmin(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    if dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{message.from_user.id}'") != []:
        if message.reply_to_message != None:
            if dbexec(f"SELECT userid FROM openhavroniya_block_users WHERE userid='{message.reply_to_message.from_user.id}'") == []:
                if " " in message.text:
                    reason = message.text.split(maxsplit=1)[1]
                else:
                    reason = "Не указано"
                if message.reply_to_message.from_user.first_name != None:
                    first_name = message.reply_to_message.from_user.first_name
                else:
                    first_name = "Не указано"
                if message.reply_to_message.from_user.last_name != None:
                    last_name = message.reply_to_message.from_user.last_name
                else:
                    last_name = "Не указано"
                blockdate = time.strftime("%d/%m/%y %H:%M:%S")
                dbexec(f"INSERT INTO openhavroniya_block_users (userid, reason, block_date, first_name, last_name, by_admin) VALUES ('{message.reply_to_message.from_user.id}', ?, '{blockdate}', ?, ?,'{message.from_user.id}')", additional_parameters=[(reason),(first_name),(last_name)])
                bot.reply_to(message, "Этот пользователь был забанен успешно.")
            else:
                bot.reply_to(message, "Этот пользователь и так забанен.")
        else:
            bot.reply_to(message, "Укажите на сообщение пользователя, которого нужно забанить")
    else:
        bot.reply_to(message, "Недостаточно прав, чтобы забанить этого пользователя.")

@bot.message_handler(commands=['removeadmin'])
def removeadmin(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    if dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{message.from_user.id}'") != []:
        if message.reply_to_message != None:
            if dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{message.reply_to_message.from_user.id}'") != []:
                dbexec(f"DELETE FROM openhavroniya_admins WHERE userid='{message.reply_to_message.from_user.id}'") 
                bot.reply_to(message, "Этот пользователь убран из списка администраторов")
            else:
                bot.reply_to(message, "Этого пользователя и так нет в списке администраторов")
        else:
            userid = message.text.split(maxsplit=1)[1]
            try:
                int(userid)
            except:
                bot.reply_to(message, "Неверный формат ид пользователя")
            else:
                if dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{userid}'") != []:
                    dbexec(f"DELETE FROM openhavroniya_admins WHERE userid='{userid}'") 
                    bot.reply_to(message, "Этот пользователь убран из списка администраторов")
                else:
                    bot.reply_to(message, "Этого пользователя и так нет в списке администраторов")
    else:
        bot.reply_to(message, "Недостаточно прав, чтобы удалить этого человека из администраторов")

@bot.message_handler(commands=['info'])
def sysinfo(message):
    if dbexec(f"SELECT userid FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'") != []:
        reason = dbexec(f"SELECT reason FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'")
        bot.reply_to(message, bannedusertext.replace("{reason}", reason[0][0]))
        return 0;
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    bot_upt = timedelta(seconds=round(time.time() - start_time, 0))
    serv_upt = timedelta(seconds=round(uptime(), 0))
    bot.reply_to(message,f"""
📔 Информация о сервере ОпенХавронии:

🕒 Время работы бота: {bot_upt}
🕘 Время работы сервера: {serv_upt}

📊 Статистика за сегодня:
⚠️ Ошибок при выполнении кода: {errors_count}шт.
➕ Созданных ответов: {new_replys}шт.
❌ Удалёных ответов: {deleted_replys}шт.
💬 Обработано сообщений: {messages_get}шт.
👀 Просмотренных ответов: {replys_visited}шт.
➕ Созданных ответов с фото: {photo_new_replys}шт.
💬 Отправленых ответов: {sends_replys}шт.
🖼 Отправленых фото: {sends_photos}шт.
        """)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    bot.reply_to(message, 'Привет, я - ОпенХаврония. Вы можете создавать/просматривать/удалять ответы бота на определёные фразы. Дополнительную помощь вы можете получить по команде /help')

@bot.message_handler(commands=["db"])
def help(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    adminslist = dbexec(f"SELECT userid FROM openhavroniya_admins WHERE userid='{message.from_user.id}'")
    if adminslist != []:
        if not " " in message.text:
            bot.reply_to(message, "Команда введена неверно.\nПример: /db SELECT * FROM openhavroniya")
        else:
            command = message.text.split(maxsplit=1)[1]
            try:
                bot.reply_to(message, "Вывод: " + str(dbexec(command)))
            except Exception as e:
                bot.reply_to(message, "Ошибка: " + str(e))
    else:
        bot.reply_to(message, "Недостаточно прав, чтобы получить доступ к базе данных.")

@bot.message_handler(commands=["photo-reply"])
def phr(message):
    if not " " in message.text:
        bot.reply_to(message, "Требуется аргумент к этой команде, чтобы вывести список фото по аргументу.")
    else:
        query = message.text.split(maxsplit=1)[1].lower()
        photolist = dbexec("SELECT photo, outtxt FROM openhavroniya_photo WHERE inttxt=?", additional_parameters=[(query)])
        if photolist == []:
            bot.reply_to(message, f"Найти фото по запросу \"{query}\" не удалось. Может быть его уже удалили, или вы написали что-то не так.")
        else:
            keyboard = types.InlineKeyboardMarkup()
            for photo in photolist:
                keyboard.row(types.InlineKeyboardButton(str(photo[0]), callback_data=bm.new("show:image:"+photo[0]+":"+query)))
            bot.send_photo(message.chat.id, no_photo, reply_to_message_id=message.message_id, caption=str(f"Вот что найшла из фото по запросу \"{query}\":"), reply_markup=keyboard)

@bot.message_handler(commands=["help"])
def help(message):
    bot.send_chat_action(message.chat.id, 'typing')
    global messages_get
    messages_get += 1
    bot.reply_to(message, "Простые примеры:\n\nСоздание ответа:\n/create-reply 300\nОтсоси у тракториста!\n\n Просмотр всех ответов на этот запрос: /reply 300\n\nУдаление ответа на входящее сообщение:\n/delete-reply 300\n Отсоси у тракториста!")

@bot.message_handler(content_types="photo")
def phrepl(message):
    global messages_get
    global photo_new_replys
    messages_get += 1
    if message.caption != None:
        if message.caption.startswith("/create-reply "):
            if dbexec(f"SELECT userid FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'") == []:
                bot.send_chat_action(message.chat.id, 'typing')
                if "\n" in message.caption:
                    wtext = message.caption.replace("/create-reply ", "").split("\n")[0].lower()
                    wttext = message.caption.split("\n")[1]
                else:
                    wtext = message.caption.replace("/create-reply ", "").split("\n")[0].lower()
                    wttext = ""

                photoid = 'img-' + time.strftime("%Y%m%d%H%M%S") + '-' + str(random.randint(1,999)) + '.jpg'
                with open("./photo-memory/" + photoid, "wb") as out:
                    out.write(bot.download_file(bot.get_file(message.photo[-1].file_id).file_path))
                dbexec("INSERT INTO openhavroniya_photo (inttxt, outtxt, photo) VALUES (?, ?, ?)", additional_parameters=[(wtext),(wttext),(photoid)])
                photo_new_replys += 1
                bot.reply_to(message, "Добавленно!")
            else:
                reason = dbexec(f"SELECT reason FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'")
                bot.reply_to(message, bannedusertext.replace("{reason}", reason[0][0]))
                return 0;

@bot.message_handler(content_types="text")
def antxt(message):
    global errors_count
    global new_replys
    global messages_get
    global photo_new_replys
    global sends_replys
    global sends_photos
    global deleted_replys
    global replys_visited
    messages_get += 1
    if message.text.startswith("/reply "):
        bot.send_chat_action(message.chat.id, 'typing')
        if dbexec(f"SELECT userid FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'") == []:
            replys_visited += 1
            reqoutp = message.text.replace("/reply ", "").lower()
            outpt = ""
            outp = dbexec("SELECT outtxt FROM 'openhavroniya' WHERE inttxt=?", additional_parameters=[(reqoutp)])
            for i in outp:
                ii = i[0]
                outpt = outpt + str(ii) + "\n"
            if str(outpt) != "":
                bot.reply_to(message, str("Ниже приведены варианты ответа на сообщение с текстом \"" + reqoutp + "\" (" + str(len(outp)) +"шт.):\n" + str(outpt)))
            else:
                bot.reply_to(message, "В базе ответов нет ответа на \"" + reqoutp +"\"")
        else:
            reason = dbexec(f"SELECT reason FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'")
            bot.reply_to(message, bannedusertext.replace("{reason}", reason[0][0]))
            return 0;
    
    elif message.text.startswith("/create-reply "):
        bot.send_chat_action(message.chat.id, 'typing')
        if dbexec(f"SELECT userid FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'") == []:
            if "\n" in message.text:
                wtext = message.text.replace("/create-reply ", "").split("\n")[0].lower().strip()
                wttext = message.text.split("\n")[1]
                dbexec("INSERT INTO openhavroniya (inttxt, outtxt) VALUES (?, ?)", additional_parameters=[(wtext),(wttext)])
                bot.reply_to(message, "Добавленно!")
                new_replys += 1
            else:
                bot.reply_to(message, "Вы неверно ввели комманду. Воспользуйтесь командой /help.")
        else:
            reason = dbexec(f"SELECT reason FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'")
            bot.reply_to(message, bannedusertext.replace("{reason}", reason[0][0]))
            return 0;

    elif message.text.startswith("/delete-reply "):
        bot.send_chat_action(message.chat.id, 'typing')
        if dbexec(f"SELECT userid FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'") == []:
            deleted_replys += 1
            if "\n" in message.text:
                wtext = message.text.replace("/delete-reply ", "").split("\n")[0].lower().strip()
                wttext = message.text.split("\n")[1]
                delout = dbexec("DELETE FROM openhavroniya WHERE inttxt=? AND outtxt=?", additional_parameters=[(wtext),(wttext)])
                bot.reply_to(message, "Фраза удалена из БД")
        else:
            reason = dbexec(f"SELECT reason FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'")
            bot.reply_to(message, bannedusertext.replace("{reason}", reason[0][0]))
            return 0;
    else:
        if dbexec(f"SELECT userid FROM openhavroniya_block_users WHERE userid='{message.from_user.id}'") == []:
            poutp = dbexec("SELECT outtxt, photo FROM openhavroniya_photo WHERE inttxt=?", additional_parameters=[(message.text.lower())])
            outp = dbexec("SELECT outtxt FROM openhavroniya WHERE inttxt=?", additional_parameters=[(message.text.lower())])
            if poutp != [] or outp != []:
                bot.send_chat_action(message.chat.id, 'typing')
                if poutp == []:
                    outpp = []
                    for i in outp:
                        outpp.append(i[0])
                    try:
                        outm = random.choice(outpp)
                        outm = outm.replace("<first_name>", message.from_user.first_name)
                        outm = outm.replace("<user_id>",str(message.from_user.id))
                        if message.from_user.last_name == None:
                            outm = outm.replace("<last_name>", "")
                        else:
                            outm = outm.replace("<last_name>",message.from_user.last_name)
                        outm = outm.replace("<chat_id>", str(message.chat.id))
                        if message.from_user.username == None:
                            outm = outm.replace("<nickname>","")
                        else:
                            outm = outm.replace("<nickname>", message.from_user.username)
                        sends_replys += 1
                        bot.reply_to(message, outm)
                    except:
                        None
                elif outp == []:
                    messphfs = random.choice(poutp)
                    sends_photos += 1
                    if messphfs[0] == "":
                        with open("./photo-memory/" + messphfs[1], 'rb') as file:
                            bot.send_photo(message.chat.id, file, reply_to_message_id=message.message_id)
                    else:
                        with open("./photo-memory/" + messphfs[1], 'rb') as file:
                            bot.send_photo(message.chat.id, file, reply_to_message_id=message.message_id, caption=str(messphfs[0]))
                else:
                    if random.randint(1, 2) == 1:
                        outpp = []
                        for i in outp:
                            outpp.append(i[0])
                        try:
                            outm = random.choice(outpp)
                            outm = outm.replace("<first_name>", message.from_user.first_name)
                            outm = outm.replace("<user_id>",str(message.from_user.id))
                            if message.from_user.last_name == None:
                                outm = outm.replace("<last_name>", "")
                            else:
                                outm = outm.replace("<last_name>",message.from_user.last_name)
                            outm = outm.replace("<chat_id>", str(message.chat.id))
                            if message.from_user.username == None:
                                outm = outm.replace("<nickname>","")
                            else:
                                outm = outm.replace("<nickname>", message.from_user.username)
                            sends_replys += 1
                            bot.reply_to(message, outm)
                        except:
                            None
                    else:
                        messphfs = random.choice(poutp)
                        sends_photos += 1
                        if messphfs[0] == "":
                            with open("./photo-memory/" + messphfs[1], 'rb') as file:
                                bot.send_photo(message.chat.id, file, reply_to_message_id=message.message_id)
                        else:
                            with open("./photo-memory/" + messphfs[1], 'rb') as file:
                                bot.send_photo(message.chat.id, file, reply_to_message_id=message.message_id, caption=str(messphfs[0]))
while True:
    try:
        bot.infinity_polling()
    except Exception as e:
        print("error: " + str(e))
