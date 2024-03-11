import os
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения
MONGO_HOST = os.getenv("MONGOHOST")
MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
MONGO_PORT = os.getenv("MONGOPORT")

# Подключение к MongoDB
client = MongoClient(MONGO_HOST, username=MONGO_USER, password=MONGO_PASSWORD, port=int(MONGO_PORT))
db = client["telegram_bot_db"]  # Имя вашей базы данных

# Получение коллекций
user_stats_collection = db["user_stats"]

# Функция для обработки сообщений пользователя
def message_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время

    try:
        # Проверка, существует ли уже запись о пользователе в базе данных
        user_data = user_stats_collection.find_one({"user_id": user_id})

        if user_data:
            # Если запись о пользователе существует, обновляем количество сообщений и дату последнего сообщения
            user_stats_collection.update_one({"user_id": user_id}, {"$inc": {"message_count": 1}, "$set": {"last_message_date": message_date}})
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
        message_count = user_stats_collection.find_one({"user_id": user_id})["message_count"]

        # Если количество сообщений кратно 10, начисляем 1 очко репутации
        if message_count % 10 == 0:
            # Увеличиваем репутацию на 1
            user_stats_collection.update_one({"user_id": user_id}, {"$inc": {"reputation": 1}})

    except Exception as e:
        print("Error handling message:", e)

# Функция для обработки команды /me
def me(update, context):
    try:
        # Получаем идентификатор пользователя, отправившего сообщение
        user_id = update.message.from_user.id

        # Ищем данные пользователя в коллекции
        user_data = user_stats_collection.find_one({"user_id": user_id})

        if user_data:
            referrals_count = user_data.get("referrals_count", "Нет")
            username = user_data.get("username", "Нет")
            message_count = user_data.get("message_count", 0)
            last_activity_date = user_data.get("last_message_date", "Нет данных")
            reputation = user_data.get("reputation", 0)

            # Получаем текущую дату и время
            current_datetime = datetime.now()

            # Вычисляем разницу в днях между текущей датой и датой регистрации
            days_since_registration = (current_datetime - user_data["registration_date"]).days

            # Формируем сообщение профиля с учетом количества сообщений, репутации и информации о пригласившем пользователе
            profile_message = f"Имя пользователя: @{username}\nДней в боте: {days_since_registration}\nПоследняя активность: {last_activity_date}\nРеферралы: {referrals_count}\nКоличество сообщений: {message_count}\nБаланс: {reputation}\n\n"

            # Создаем инлайн клавиатуру с кнопкой "Открыть бот"
            keyboard = [[InlineKeyboardButton("Открыть бот 🤖", url="t.me/Cyndycate_invaterbot?start=yjkqU3t1U8")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем сообщение с профилем пользователя, используя реплай на сообщение, которое вызвало команду /me
            context.bot.send_message(chat_id=update.message.chat_id, text=profile_message, reply_to_message_id=update.message.message_id, reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Вы еще не зарегистрированы")

    except Exception as e:
        print("Error handling /me command:", e)

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
