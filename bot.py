import config
import psycopg2
import telebot
import os
from flask import Flask, request

# Для работы с Telegram API используем Telebot
# Для работы с БД используем адаптер psycopg2

bot = telebot.TeleBot(config.token)
server = Flask(__name__)


@bot.message_handler(commands=['reg'])
# Регистрируем пользователя при первом входе
def first_visit(message):
    bot.send_message(message.chat.id, 'Приветики')
    conn.close()
    
@server.route('/' + config.token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://sqnposed.herokuapp.com/270200218:AAEkPc88mnM1dcc47z8xtHHu5UxVurUll1I")
    return "!", 200

server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))    
