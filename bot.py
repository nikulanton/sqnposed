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
    bdconnect.close()
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
    bdconnect.close()

@bot.message_handler(commands=['list'])
def list_of_quests(message):
    list_cursor = bdconnect.cursor()
    list_cursor.execute('SELECT quest_title FROM quests;')
    quests = list_cursor.fetchall()
    allquests = "Список доступных квестов:\n"
    for quest in quests:
        allquests = allquests + str(quest[0]) + '\n'
    bdconnect.commit()
    bdconnect.close()
    bot.send_message(message.chat.id, allquests)

@bot.message_handler(commands=['addquest'])
def list_of_quests(message):
    add_cursor = bdconnect.cursor()
    add_cursor.execute('UPDATE users set usermode="addquest" WHERE user_id = %s;', (int(message.chat.id),))
    bdconnect.commit()
    bdconnect.close()
    bot.send_message(message.chat.id, 'Введите данные о квесте в формате название;количество опыта;количество денег;дата начала;дата окончания\n*Дата вводится в формате день/месяц/год')


@bot.message_handler(content_types=['text'])
def some_text_reaction(message):
    get_usermode = bdconnect.cursor()
    get_usermode.execute('SELECT  usermode FROM users WHERE user_id=%s', (int(message.chat.id),))
    usermode = get_usermode.fetchall()
    if usermode[0][0] == 'addquest':
        bot.send_message(message.chat.id, 'Вы в режиме добавления квеста')
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
