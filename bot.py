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
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы в системе')
        bdconnect.close()
    else:
        # Если нет, добавляем в базу
        curs.execute('INSERT INTO users (user_id,nickname,team) VALUES (%s,%s,NULL);',
                     (message.chat.id, message.from_user.username))
        bdconnect.commit()
        bot.send_message(message.chat.id, 'Вы успешно зарегистрированы')

@bot.message_handler(content_types=['text'])
def some_text_reaction(message):
    bot.send_message(message.chat.id, 'К сожалению, мы еще не умеем отвечать на то что ты отправил')

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
