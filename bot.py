import config
import psycopg2
import telebot


# Для работы с Telegram API используем Telebot
# Для работы с БД используем адаптер psycopg2

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=['reg'])
# Регистрируем пользователя при первом входе
def first_visit(message):
    # В дальнейшем одинаковая строка коннекта к БД
    conn = psycopg2.connect(host="ec2-107-22-162-158.compute-1.amazonaws.com",
                            user="jwmxuqiprgblvo",
                            password="3f0358afe49052171dd76a4166bab6709341705b3a5223b497f48066cb6f85e4",
                            dbname="da5f2k12t4ep54",
                            port=5432)
    curs = conn.cursor()
    # Создаем курсор, выполняем запрос на выборку id зарегистрированных пользователей
    curs.execute('SELECT test FROM mytable;')
    ids = curs.fetchall()
    bot.send_message(message.chat.id, ids[0][0])
    conn.close()

bot.polling()