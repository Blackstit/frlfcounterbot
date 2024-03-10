import mysql.connector
from mysql.connector import Error
from telebot import types
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telebot
import random
from datetime import datetime
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
MYSQL_HOST = os.getenv("MYSQLHOST")
MYSQL_USER = os.getenv("MYSQLUSER")
MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD")
MYSQL_DATABASE = os.getenv("MYSQLDATABASE")
MYSQL_PORT = os.getenv("MYSQLPORT")

try:
    mydb = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=MYSQL_PORT
    )
    cursor = mydb.cursor()
    print("Connected to MySQL database")
except Error as e:
    print("Error connecting to MySQL database:", e)

# Создание таблицы user_stats, если она не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS user_stats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    username VARCHAR(255),
                    message_count INT DEFAULT 0,
                    last_message_date DATETIME
                  )''')


def message_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время

    # Проверка, существует ли уже запись о пользователе в базе данных
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        # Если запись о пользователе существует, обновляем количество сообщений и дату последнего сообщения
        cursor.execute("UPDATE user_stats SET message_count = message_count + 1, last_message_date = %s WHERE user_id = %s",
                       (message_date, user_id,))
    else:
        # Если запись о пользователе отсутствует, удаляем сообщение пользователя
        context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

        # Отправляем сообщение о регистрации и приглашение зарегистрироваться
        invite_message = f"@{username}, салют!\n\nЧтобы писать сообщения в чате, тебе сначала нужно зарегистрироваться в нашем боте. Это не займет у тебя больше минуты."
        keyboard = [[InlineKeyboardButton("Зарегистрироваться", url="t.me/Cyndycate_invaterbot?start=yjkqU3t1U8")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=chat_id, text=invite_message, reply_markup=reply_markup)
        return

    # Получаем текущее количество сообщений пользователя
    cursor.execute("SELECT message_count FROM user_stats WHERE user_id = %s", (user_id,))
    message_count = cursor.fetchone()[0]

    # Если количество сообщений кратно 10, начисляем 1 очко репутации
    if message_count % 10 == 0:
        # Получаем текущее количество очков репутации пользователя
        cursor.execute("SELECT reputation FROM users WHERE id = %s", (user_id,))
        reputation = cursor.fetchone()[0]

        # Увеличиваем репутацию на 1 и обновляем запись в базе данных
        new_reputation = reputation + 1
        cursor.execute("UPDATE users SET reputation = %s WHERE id = %s", (new_reputation, user_id))

    # Применяем изменения к базе данных
    mydb.commit()


# Функция обработки команды /me
def me(update, context):
    # Получаем идентификатор пользователя, отправившего сообщение
    user_id = update.message.from_user.id

    # Выполняем запрос к базе данных
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        referrals_count = user_data[5]
        referral_code = user_data[6]
        username = user_data[1] if user_data[1] else "Нет"
        first_name = user_data[2] if user_data[2] else "Нет"
        registration_date = user_data[4]
        referrer_id = user_data[7]
        reputation = user_data[8]

        # Получаем дату регистрации пользователя
        registration_date = user_data[4]
        registration_datetime = datetime.strptime(registration_date, "%Y-%m-%d %H:%M:%S")

        # Вычисляем разницу в днях между текущей датой и датой регистрации
        days_since_registration = (datetime.now() - registration_datetime).days

        # Получаем информацию о пригласившем пользователе
        referrer_info = ""
        referrer_username = "-"
        if referrer_id:
            cursor.execute("SELECT first_name, username FROM users WHERE id = %s", (referrer_id,))
            referrer_data = cursor.fetchone()
            if referrer_data:
                referrer_name = referrer_data[0]
                referrer_username = referrer_data[1]
                referrer_info = f"Вас пригласил: {referrer_name} (@{referrer_username})\n"
            else:
                referrer_info = "Вас пригласил: -\n"
                referrer_username = "-"

        # Получаем количество сообщений пользователя из таблицы user_stats
        cursor.execute("SELECT message_count FROM user_stats WHERE user_id = %s", (user_id,))
        message_count_result = cursor.fetchone()
        message_count = message_count_result[0] if message_count_result else 0

        # Получаем дату последней активности пользователя из таблицы user_stats
        cursor.execute("SELECT last_message_date FROM user_stats WHERE user_id = %s ORDER BY last_message_date DESC LIMIT 1", (user_id,))
        last_activity_date_result = cursor.fetchone()
        
        if last_activity_date_result:
            last_activity_date = last_activity_date_result[0]  # Получаем дату из результата запроса
        
            # Преобразуем дату в строку в нужном формате
            last_activity_formatted = last_activity_date.strftime("%d.%m.%Y %H:%M:%S")
        else:
            last_activity_formatted = "Нет данных"

        # Формируем сообщение профиля с учетом количества сообщений, репутации и информации о пригласившем пользователе
        profile_message = f"Имя пользователя: @{username}\nДней в боте: {days_since_registration}\nПоследняя активность: {last_activity_formatted}\nРеферралы: {referrals_count}\nКоличество сообщений: {message_count}\nБаланс: {reputation}\n\n{referrer_info}"

        # Отправляем сообщение с профилем пользователя, используя реплай на сообщение, которое вызвало команду /me
        context.bot.send_message(chat_id=update.message.chat_id, text=profile_message, reply_to_message_id=update.message.message_id)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Вы еще не зарегистрированы")


# Токен вашего бота
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Создаем объект updater и передаем ему токен вашего бота
updater = Updater(token=TOKEN, use_context=True)

# Получаем из него диспетчер сообщений
dispatcher = updater.dispatcher

# Регистрируем обработчик сообщений для конкретного чата
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), message_handler))

# Регистрируем обработчик команды /me
me_handler = CommandHandler('me', me)
dispatcher.add_handler(me_handler)

# Запускаем бота
updater.start_polling()
updater.idle()
