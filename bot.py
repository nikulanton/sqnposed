import config
import psycopg2
import telebot
import os
from flask import Flask, request


bot = telebot.TeleBot(config.token)
server = Flask(__name__)


@bot.message_handler(commands=['start'])
def first_visit(message):
    bot.send_message(message.chat.id, 'Hello')
    
@server.route('/', methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://sqnposed.herokuapp.com/' + config.token)
    return "!", 200

server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))    
