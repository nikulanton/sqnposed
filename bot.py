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
    curs = bdconnect.cursor()
    curs.execute('SELECT quest_title FROM quests;')
    quests = curs.fetchall()
    allquests = "Список доступных квестов:\n"
    for quest in quests:
        allquests = allquests + str(quest[0]) + '\n'
    bdconnect.commit()
    bot.send_message(message.chat.id, allquests)

@bot.message_handler(commands=['addquest'])
def addquest(message):
    curs = bdconnect.cursor()
    status = 'addquest'
    curs.execute('UPDATE users set usermode=%s WHERE user_id = %s;', (status,int(message.chat.id),))
    bdconnect.commit()
    bot.send_message(message.chat.id, 'Введите данные о квесте в формате название;количество опыта;количество денег;дата начала;дата окончания\n*Дата вводится в формате месяц/день/год')

@bot.message_handler(commands=['esc'])
def escape(message):
    curs = bdconnect.cursor()
    curs.execute('UPDATE users set usermode=NULL WHERE user_id = %s;', (int(message.chat.id),))
    bdconnect.commit()
    bot.send_message(message.chat.id, 'Предыдущая команда прервана. Выберите другую')

@bot.message_handler(commands=['answer'])
def answer(message):
    curs = bdconnect.cursor()
    status = 'tellinganswer'
    curs.execute('UPDATE users set usermode=%s WHERE user_id = %s;', (status, int(message.chat.id),))
    bot.send_message(message.chat.id, 'Введите найденный  код')

@bot.message_handler(commands=['stats'])
def answer(message):
    curs = bdconnect.cursor()
    curs.execute('WITH vse AS (SELECT * FROM quest_progress JOIN quests ON (quest_progress.quest_id=quests.quest_id)), nado AS (SELECT quest_exp FROM vse WHERE user_id=%s) SELECT sum(quest_exp) FROM nado')
    exp = curs.fetchall()
    bot.send_message(message.chat.id, exp[0])

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
        textcursor.execute('SELECT quest_id FROM quests WHERE quest_id=%s', (int(message.text),))
        quests = textcursor.fetchall()
        bdconnect.commit()
        if not quests:
            bot.send_message(message.chat.id, 'Такого квеста не существует! Введите номер квеста из спика команды /list')
        else:
            bot.send_message(message.chat.id, 'Вошли в ELSE')
            textcursor.execute('SELECT isdoing FROM quest_progress WHERE quest_id=%s AND user_id=%s',
                               (int(message.text), int(message.chat.id),))
            is_already_done = textcursor.fetchall()
            bot.send_message(message.chat.id, 'Вошли в ELSE')
            if not is_already_done:
                textcursor.execute('INSERT INTO quest_progress (quest_id,user_id,isdoing,current_task) VALUES (%s,%s,FALSE,1)',
                                   (int(message.text),int(message.chat.id),))
                textcursor.execute('INSERT INTO task_progress (task_id,user_id,isdoing,quest_id) VALUES (1,%s,FALSE,%s)',
                                    (int(message.chat.id), int(message.text), ))
                textcursor.execute('UPDATE users set usermode=NULL WHERE user_id = %s;', (int(message.chat.id),))
                bdconnect.commit()
                textcursor.execute('SELECT task_id,task_text,task_title FROM tasks WHERE task_quest=%s ORDER BY task_id', (int(message.text),))
                first_task = textcursor.fetchall()
                bot.send_message(message.chat.id, 'Вы успешно взяли квест. Отправляем первое задание...')
                bot.send_message(message.chat.id, first_task[0][1])
            else:
                bot.send_message(message.chat.id, 'Вы уже выполняли этот квест, выберите другой!')
    elif usermode[0][0] == 'tellinganswer':
        textcursor.execute('SELECT current_task,quest_id FROM quest_progress WHERE user_id=%s AND isdoing=FALSE', (int(message.chat.id),))
        current_task_id = textcursor.fetchall()
        if not current_task_id:
            bot.send_message(message.chat.id, 'Сначала возьмите на выполнение квест')
        else:
            textcursor.execute('SELECT task_answer FROM tasks WHERE task_id=%s AND task_quest=%s',
                     (current_task_id[0][0], current_task_id[0][1],))
            istrueanswer = textcursor.fetchall()
            if istrueanswer[0][0] == message.text:
                textcursor.execute('UPDATE task_progress SET isdoing=TRUE WHERE task_id=%s AND user_id=%s AND quest_id=%s',
                         (int(current_task_id[0][0]),int(message.chat.id), int(current_task_id[0][1]),))
                bdconnect.commit()
                bot.send_message(message.chat.id, 'Задание успешно выполнено, поздравляем! Отправляем следующее...')
                textcursor.execute('SELECT max(task_id) FROM tasks WHERE task_quest=%s', (current_task_id[0][1],))
                max_taskid = textcursor.fetchall()
                maxid = max_taskid[0]
                textcursor.execute('SELECT current_task FROM quest_progress WHERE user_id=%s AND isdoing=FALSE',
                    (int(message.chat.id),))
                nowtask = textcursor.fetchall()
                if nowtask[0]==maxid:
                    textcursor.execute('UPDATE quest_progress SET isdoing=TRUE WHERE user_id=%s AND quest_id=%s',(int(message.chat.id),current_task_id[0][1],))
                    bdconnect.commit()
                    bot.send_message(message.chat.id, 'Квест выполнен! Поздраляем!')
                else:
                    textcursor.execute('UPDATE quest_progress SET current_task=%s WHERE quest_id=%s AND user_id=%s',
                                           (current_task_id[0][0]+1, current_task_id[0][1], int(message.chat.id),))
                    textcursor.execute('INSERT INTO task_progress (task_id,user_id,isdoing,quest_id) VALUES (%s,%s,FALSE,%s)',
                                        (current_task_id[0][0]+1, int(message.chat.id), current_task_id[0][1],))
                    bdconnect.commit()
                    textcursor.execute('SELECT task_id,task_text,task_title FROM tasks WHERE task_quest=%s AND task_id=%s ORDER BY task_id',
                                        (current_task_id[0][1],current_task_id[0][0]+1,))
                    next_task = textcursor.fetchall()
                    bot.send_message(message.chat.id, next_task[0][1])
            else:
                bot.send_message(message.chat.id, 'Ответ не верный! Попробуйте другой!')
    else:
        bot.send_message(message.chat.id, 'Тут ничего неет :(')


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
