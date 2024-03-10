import os
import mysql.connector
from telegram.ext import Updater, MessageHandler, CommandHandler
from telegram import Update
from datetime import datetime

# Получение значений из переменных окружения
MYSQL_HOST = os.getenv('MYSQLHOST')
MYSQL_USER = os.getenv('MYSQLUSER')
MYSQL_PASSWORD = os.getenv('MYSQLPASSWORD')
MYSQL_DATABASE = os.getenv('MYSQLDATABASE')
MYSQL_PORT = int(os.getenv('MYSQLPORT'))  # Преобразование в целое число

# Подключение к базе данных MySQL
mydb = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE,
    port=MYSQL_PORT
)

# Создание объекта cursor для выполнения SQL-запросов
cur = mydb.cursor()

# Функция обработки сообщений
def message_handler(update: Update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время

    # Проверка, существует ли уже запись о пользователе в базе данных
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()

    if user_data:
        # Если запись о пользователе существует, обновляем количество сообщений и дату последнего сообщения
        cur.execute("UPDATE user_stats SET message_count = message_count + 1, last_message_date = %s WHERE user_id = %s", (message_date, user_id,))
    else:
        # Если запись о пользователе отсутствует, отправляем приглашение зарегистрироваться
        invite_message = f"@{username}, чтобы писать сообщения в чате, тебе сначала нужно зарегистрироваться в нашем боте."
        context.bot.send_message(chat_id=chat_id, text=invite_message)

        return

    # Получаем текущее количество сообщений пользователя
    cur.execute("SELECT message_count FROM user_stats WHERE user_id = %s", (user_id,))
    message_count = cur.fetchone()[0]

    # Если количество сообщений кратно 10, начисляем 1 очко репутации
    if message_count % 10 == 0:
        # Получаем текущее количество очков репутации пользователя
        cur.execute("SELECT reputation FROM users WHERE id = %s", (user_id,))
        reputation = cur.fetchone()[0]
        
        # Увеличиваем репутацию на 1 и обновляем запись в базе данных
        new_reputation = reputation + 1
        cur.execute("UPDATE users SET reputation = %s WHERE id = %s", (new_reputation, user_id))

    # Применяем изменения к базе данных
    mydb.commit()


# Функция обработки команды /me
def me(update: Update, context):
    # Получаем идентификатор пользователя, отправившего сообщение
    user_id = update.message.from_user.id

    user_data = cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()

    if user_data:
        # ваша логика обработки профиля пользователя
        pass
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Вы еще не зарегистрированы")

    # Применяем изменения к базе данных
    mydb.commit()


# Функция обработки команды /top
def top(update: Update, context):
    # ваша логика получения топ-10 пользователей
    pass


# Функция обработки команды /give
def give(update: Update, context):
    # ваша логика передачи токенов пользователям
    pass


# Токен вашего бота
TOKEN = '6908271386:AAGps8jBks7fxN84EmK7H4OzHRipK4PhJHU'

# Создаем объект updater и передаем ему токен вашего бота
updater = Updater(TOKEN, use_context=True)

# Получаем из него диспетчер сообщений
dispatcher = updater.dispatcher

# Регистрируем обработчик сообщений для конкретного чата
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), message_handler))

# Регистрируем обработчик команды /me
me_handler = CommandHandler('me', me)
dispatcher.add_handler(me_handler)

# Регистрируем обработчик команды /top
top_handler = CommandHandler('top', top)
dispatcher.add_handler(top_handler)

# Регистрируем обработчик команды /give
give_handler = CommandHandler('give', give)
dispatcher.add_handler(give_handler)

# Запускаем бота
updater.start_polling()
updater.idle()
