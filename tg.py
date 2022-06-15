print("OpenHavroniya\n      by Andrey Daniluk and TideSoft!\nLoading...")
print("Import modules...")
import os, os.path, sys, random, sqlite3, configparser, threading, time
import telebot
os.system("title OpenHavroniya Telegram server")
print("Connect to database...")
conn = sqlite3.connect('db.sqlite', check_same_thread=False)
cursor = conn.cursor()
lock = threading.Lock()
cursor.execute("CREATE TABLE IF NOT EXISTS openhavroniya (inttxt, outtxt)")
cursor.execute("CREATE TABLE IF NOT EXISTS openhavroniya_photo (inttxt, outtxt, photo)")

print("Inzialite libs to work...")
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
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Привет, я - ОпенХаврония. Вы можете создавать/просматривать/удалять ответы бота на определёные фразы. Дополнительную помощь вы можете получить по команде /help')

@bot.message_handler(commands=["help"])
def help(message):
    bot.reply_to(message, "Простые примеры:\n\nСоздание ответа:\n/create-reply 300\nОтсоси у тракториста!\n\n Просмотр всех ответов на этот запрос: /reply 300\n\nУдаление ответа на входящее сообщение:\n/delete-reply 300\n Отсоси у тракториста!")

@bot.message_handler(content_types="photo")
def phrepl(message):
    if message.caption != None:
        if message.caption.startswith("/create-reply "):
            if "\n" in message.caption:
                wtext = message.caption.replace("/create-reply ", "").split("\n")[0].lower()
                wttext = message.caption.split("\n")[1]
            else:
                wtext = message.caption.replace("/create-reply ", "").split("\n")[0].lower()
                wttext = ""

            photoid = 'img-' + time.strftime("%Y%m%d%H%M%S") + '-' + str(random.randint(1,999)) + '.jpg'
            with open("./photo-memory/" + photoid, "wb") as out:
                out.write(bot.download_file(bot.get_file(message.photo[-1].file_id).file_path))
            try:
                lock.acquire(True)
                cursor.execute("INSERT INTO openhavroniya_photo (inttxt, outtxt, photo) VALUES ('" + wtext + "', '" + wttext +"', '" + photoid + "')")
            finally:
                lock.release()
            conn.commit()
            bot.reply_to(message, "Добавленно!")

@bot.message_handler(content_types="text")
def antxt(message):
    if message.text.startswith("/reply "):
        reqoutp = message.text.replace("/reply ", "").lower()
        outpt = ""
        try:
            lock.acquire(True)
            cursor.execute("SELECT outtxt FROM 'openhavroniya' WHERE inttxt='" + reqoutp +"'")
        finally:
            lock.release()
        
        outp = cursor.fetchall()
        for i in outp:
            ii = i[0]
            outpt = outpt + str(ii) + "\n"
        if str(outpt) != "":
            bot.reply_to(message, str("Ниже приведены варианты ответа на сообщение с текстом \"" + reqoutp + "\" (" + str(len(outp)) +"шт.):\n" + str(outpt)))
        else:
            bot.reply_to(message, "В базе ответов нет ответа на \"" + reqoutp +"\"")
    
    elif message.text.startswith("/create-reply "):
        if "\n" in message.text:
            wtext = message.text.replace("/create-reply ", "").split("\n")[0].lower()
            wttext = message.text.split("\n")[1]
            try:
                lock.acquire(True)
                cursor.execute("INSERT INTO openhavroniya (inttxt, outtxt) VALUES ('" + wtext + "', '" + wttext +"')")
            finally:
                lock.release()
            conn.commit()
            bot.reply_to(message, "Добавленно!")
        else:
            bot.reply_to(message, "Вы неверно ввели комманду. Воспользуйтесь командой /help.")
    elif message.text.startswith("/delete-reply "):
        if str(message.chat.id) in blockedlist:
            bot.reply_to(message, "Взаимодействие с ОпенХавронией в этом чате запрещено администрацией.")
            return 0;
        if "\n" in message.text:
            wtext = message.text.replace("/delete-reply ", "").split("\n")[0].lower()
            wttext = message.text.split("\n")[1]
            try:
                lock.acquire(True)
                cursor.execute("DELETE FROM openhavroniya WHERE inttxt='" + wtext + "' AND outtxt='" + wttext +"'")
            finally:
                lock.release()
            conn.commit()
            delout = cursor.fetchall()
            bot.reply_to(message, "Фраза удалена из БД")
    else:
        try:
            lock.acquire(True)
            cursor.execute("SELECT outtxt, photo FROM 'openhavroniya_photo' WHERE inttxt='" + message.text.lower() +"'")
        finally:
            lock.release()
        poutp = cursor.fetchall()

        try:
            lock.acquire(True)
            cursor.execute("SELECT outtxt FROM 'openhavroniya' WHERE inttxt='" + message.text.lower() +"'")
        finally:
            lock.release()
        outp = cursor.fetchall()
        if poutp != [] or outp != []:
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
                    bot.reply_to(message, outm)
                except:
                    None
            elif outp == []:
                messphfs = random.choice(poutp)
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
                        bot.reply_to(message, outm)
                    except:
                        None
                else:
                    messphfs = random.choice(poutp)
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
