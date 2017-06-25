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

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)


@bot.message_handler(commands=['start'])
def first_visit(message):
    curs = conn.cursor()
    curs.execute('SELECT test_col FROM test_table;')
    test = curs.fetchall()
    bot.send_message(message.chat.id, str(test[0]))
    
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
