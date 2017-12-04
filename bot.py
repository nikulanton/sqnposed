import config
import psycopg2
import telebot
import os
from flask import Flask, request
import urllib


bot = telebot.TeleBot(config.token)
server = Flask(__name__)
urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])

bdconnect = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

@bot.message_handler(commands=['start'])
def first_visit(message):
    bot.send_message(message.chat.id, 'Привет! Отправь команду /reg чтобы зарегистрироваться и начать играть')

@bot.message_handler(commands=['test'])
def first_visit(message):
    curs = bdconnect.cursor()
    curs.execute('INSERT INTO users (user_id) VALUES (%s);',
                     (message.chat.id))
    bdconnect.commit()
    bot.send_message(message.chat.id, 'Смотри БД')    

@bot.message_handler(commands=['reg'])
def user_register(message):
    curs = bdconnect.cursor()
    curs.execute('SELECT user_id FROM users;')
    ids = curs.fetchall()
    for myid in ids:
        if myid[0] == int(message.chat.id):
            id_flag = bool(True)
            break
        else:
            id_flag = bool(False)
    #         Проверяем есть ли пользователь в базе
    if id_flag == True:
        # Если да, то выдаем это сообщение
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы в системе!')
    else:
        # Если нет, добавляем в базу
        userrole = 'user'
        curs.execute('INSERT INTO users (user_id,nickname,team,role,usermode) VALUES (%s,%s,NULL,%s,NULL);',
                     (message.chat.id, message.from_user.username, userrole))
        bdconnect.commit()
        bot.send_message(message.chat.id, 'Вы успешно зарегистрированы')

@bot.message_handler(commands=['list'])
def list_of_quests(message):
    list_cursor = bdconnect.cursor()
    list_cursor.execute('SELECT quest_title FROM quests;')
    quests = list_cursor.fetchall()
    allquests = "Список доступных квестов:\n"
    for quest in quests:
        allquests = allquests + str(quest[0]) + '\n'
    bdconnect.commit()
    bot.send_message(message.chat.id, allquests)

@bot.message_handler(commands=['addquest'])
def addquest(message):
    add_cursor = bdconnect.cursor()
    status = 'addquest'
    add_cursor.execute('UPDATE users set usermode=%s WHERE user_id = %s;', (status,int(message.chat.id),))
    bdconnect.commit()
    bot.send_message(message.chat.id, 'Введите данные о квесте в формате название;количество опыта;количество денег;дата начала;дата окончания\n*Дата вводится в формате месяц/день/год')

@bot.message_handler(commands=['esc'])
def escape(message):
    esc_cursor = bdconnect.cursor()
    esc_cursor.execute('UPDATE users set usermode=NULL WHERE user_id = %s;', (int(message.chat.id),))
    bdconnect.commit()
    bot.send_message(message.chat.id, 'Предыдущая команда прервана. Выберите другую')

@bot.message_handler(commands=['takequest'])
def takequest(message):
    curs = bdconnect.cursor()
    curs.execute('SELECT quest_id FROM quest_progress WHERE user_id=%s AND isdoing=FALSE', (str(message.chat.id),))
    validation = curs.fetchall()
    if not validation:
        flag = True
    else:
        flag=False
    if flag==True:
        status = 'takequest'
        curs.execute('UPDATE users set usermode=%s WHERE user_id = %s;', (status, int(message.chat.id),))
        bdconnect.commit()
        bot.send_message(message.chat.id, 'Выберите ID квеста который вы хотите взять')
    else:
        bot.send_message(message.chat.id, 'Сначала выполните предыдущий квест!')

@bot.message_handler(content_types=['text'])
def some_text_reaction(message):
    textcursor = bdconnect.cursor()
    textcursor.execute('SELECT usermode FROM users WHERE user_id=%s', (int(message.chat.id),))
    usermode = textcursor.fetchall()
    if usermode[0][0] == 'addquest':
        quest_parts = (message.text).split(';')
        textcursor.execute('INSERT INTO quests (quest_title,quest_exp,quest_money,quest_start,quest_end,quest_available) VALUES (%s,%s,%s,%s,%s,TRUE)', (quest_parts[0], int(quest_parts[1]), int(quest_parts[2]), quest_parts[3], quest_parts[4], ))
        bdconnect.commit()
        bot.send_message(message.chat.id, 'Квест добавлен если вы нигде не ошиблись')
    elif usermode[0][0] == 'takequest':
        textcursor.execute('SELECT quest_id FROM quests')
        quests = textcursor.fetchall()
        if not quests:
            bot.send_message(message.chat.id, 'Такого квеста не существует!')
        else:
            textcursor.execute('INSERT INTO quest_progress (quest_id,user_id,isdoing) VALUES (%s,%s,FALSE)', (int(message.text),int(message.chat.id),))
            bdconnect.commit()
            bot.send_message(message.chat.id, 'Вы успешно взяли квест')
    else:
        bot.send_message(message.chat.id, 'Тут ничего нет :(')

@server.route('/bot', methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://sqnposed.herokuapp.com/bot')
    return "!", 200

server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))    
