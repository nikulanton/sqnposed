import config
import psycopg2
import telebot


# Для работы с Telegram API используем Telebot
# Для работы с БД используем адаптер psycopg2

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=['reg'])
# Регистрируем пользователя при первом входе
def first_visit(message):
    bot.send_message(message.chat.id, 'Приветики')
    conn.close()
