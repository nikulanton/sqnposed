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
                     (message.chat.id, message.from_user.username, str(userrole)))
        bdconnect.commit()
        bot.send_message(message.chat.id, 'Вы успешно зарегистрированы')

@bot.message_handler(commands=['list'])
def list_of_quests(message):
    curs = bdconnect.cursor()
    curs.execute('SELECT quest_id,quest_title,quest_exp,quest_money FROM quests;')
    quests = curs.fetchall()
    allquests = "Список доступных квестов:\n"
    for quest in quests:
        allquests = allquests + 'Квест номер {0} - {1} (Опыт: {2}, Монеты: {3})\n'.format(quest[0],quest[1],quest[2],quest[3])
    bdconnect.commit()
    bot.send_message(message.chat.id, allquests)

@bot.message_handler(commands=['addquest'])
def addquest(message):
    curs = bdconnect.cursor()
    curs.execute('SELECT role FROM users WHERE user_id=%s', (int(message.chat.id),))
    role = curs.fetchall()
    if role[0][0]=='admin':
        status = 'addquest'
        curs.execute('UPDATE users set usermode=%s WHERE user_id = %s;', (status,int(message.chat.id),))
        bdconnect.commit()
        bot.send_message(message.chat.id, 'Введите данные о квесте в формате название квеста;количество опыта;количество денег;ID локации')
    else:
        bot.send_message(message.chat.id, 'Вы не являетесь администратором')

@bot.message_handler(commands=['done'])
def done_quests(message):
    curs = bdconnect.cursor()
    curs.execute('WITH first as (SELECT quest_progress.quest_id, quest_title, user_id FROM quest_progress JOIN quests ON (quests.quest_id=quest_progress.quest_id)), second as (SELECT * FROM first WHERE user_id=%s) SELECT * FROM second',
                 (int(message.chat.id),))
    done = curs.fetchall()
    if not done:
        bot.send_message(message.chat.id, 'Вы еще не выполняли квестов. Самое время начать')
    else:
        for each in done:
            result = result + 'Квест номер {0} - {1}\n'.format(each[0],each[1])
        bot.send_message(message.chat.id,'TEST')
        bot.send_message(message.chat.id, 'Вы уже выполнили следующие квесты:\n{0}'.format(result))

@bot.message_handler(commands=['addtask'])
def addtask(message):
    curs = bdconnect.cursor()
    curs.execute('SELECT role FROM users WHERE user_id=%s', (int(message.chat.id),))
    role = curs.fetchall()
    if role[0][0]=='admin':
        status = 'addtask'
        curs.execute('UPDATE users set usermode=%s WHERE user_id = %s;', (status,int(message.chat.id),))
        bdconnect.commit()
        bot.send_message(message.chat.id, 'Введите данные о задании в формате порядковый номер задания в квесте;номер квеста;заголовок задания;текст задания;правильный ответ')
    else:
        bot.send_message(message.chat.id,'Вы не являетесь администратором')

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
def stats(message):
    curs = bdconnect.cursor()
    curs.execute('WITH vse AS (SELECT * FROM quest_progress JOIN quests ON (quest_progress.quest_id=quests.quest_id)), nado AS (SELECT quest_exp,quest_money FROM vse WHERE user_id=%s) SELECT sum(quest_exp),sum(quest_money) FROM nado', (int(message.chat.id),))
    exp = curs.fetchall()
    bot.send_message(message.chat.id, 'Количество опыта: {0}\nКоличество монет: {1}'.format(exp[0][0],exp[0][1]))

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
        textcursor.execute('INSERT INTO quests (quest_title,quest_exp,quest_money,quest_location) VALUES (%s,%s,%s,%s)',
                           (quest_parts[0], int(quest_parts[1]), int(quest_parts[2]), quest_parts[3],))
        bdconnect.commit()
        bot.send_message(message.chat.id, 'Квест добавлен если вы нигде не ошиблись')
    elif usermode[0][0] == "addtask":
        task_parts = (message.text).split(';')
        textcursor.execute(
            'INSERT INTO tasks (task_id,task_quest,task_title,task_text,task_answer) VALUES (%s,%s,%s,%s,%s)',
            (int(task_parts[0]),int(task_parts[1]),task_parts[2],task_parts[3],task_parts[4],))
        bdconnect.commit()
        bot.send_message(message.chat.id, 'Задание добавлено если вы нигде не ошиблись!')
    elif usermode[0][0] == 'takequest':
        textcursor.execute('SELECT quest_id FROM quests WHERE quest_id=%s', (int(message.text),))
        quests = textcursor.fetchall()
        bdconnect.commit()
        if not quests:
            bot.send_message(message.chat.id, 'Такого квеста не существует! Введите номер квеста из спика команды /list')
        else:
            textcursor.execute('SELECT isdoing FROM quest_progress WHERE quest_id=%s AND user_id=%s',
                               (int(message.text), int(message.chat.id),))
            is_already_done = textcursor.fetchall()
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
                bot.send_message(message.chat.id, '{0}\n{1}'.format(first_task[0][2],first_task[0][1]))
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
                    bot.send_message(message.chat.id, 'УПС! Заданий-то больше нет. Квест выполнен! Поздравляем!')
                else:
                    textcursor.execute('UPDATE quest_progress SET current_task=%s WHERE quest_id=%s AND user_id=%s',
                                           (current_task_id[0][0]+1, current_task_id[0][1], int(message.chat.id),))
                    textcursor.execute('INSERT INTO task_progress (task_id,user_id,isdoing,quest_id) VALUES (%s,%s,FALSE,%s)',
                                        (current_task_id[0][0]+1, int(message.chat.id), current_task_id[0][1],))
                    bdconnect.commit()
                    textcursor.execute('SELECT task_id,task_text,task_title FROM tasks WHERE task_quest=%s AND task_id=%s ORDER BY task_id',
                                        (current_task_id[0][1],current_task_id[0][0]+1,))
                    next_task = textcursor.fetchall()
                    bot.send_message(message.chat.id, '{0}\n{1}'.format(next_task[0][2],next_task[0][1]))
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
