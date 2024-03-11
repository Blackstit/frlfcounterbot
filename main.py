import pymongo
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения для подключения к MongoDB
MONGO_URL = os.getenv("MONGO_URL")
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Подключение к MongoDB
client = pymongo.MongoClient(MONGO_URL)
db = client['test']  # Замените 'your_database_name' на имя вашей базы данных

# Проверяем, существует ли коллекция, и создаем ее, если она отсутствует
if 'users_stats' not in db.list_collection_names():
    db.create_collection('users_stats')
users_stats_collection = db['users_stats']  # Коллекция для статистики пользователей

users_collection = db['users'] # Коллекция для  пользователей


import pymongo
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения для подключения к MongoDB
MONGO_URL = os.getenv("MONGO_URL")
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def message_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время

    try:
        # Проверяем, существует ли запись о пользователе в коллекции users
        user_data = users_collection.find_one({'id': user_id})

        if user_data:
            # Пользователь зарегистрирован в боте
            # Проверяем, существует ли запись о пользователе в коллекции users_stats
            user_stats_data = users_stats_collection.find_one({'user_id': user_id})

            if not user_stats_data:
                # Если записи о пользователе нет, создаем новую запись
                new_user_stats_data = {
                    'user_id': user_id,
                    'username': username,  # Сохраняем имя пользователя
                    'message_count': 1,
                    'last_message_date': message_date
                }
                users_stats_collection.insert_one(new_user_stats_data)
            else:
                # Если запись о пользователе уже существует, обновляем количество сообщений и дату последнего сообщения
                users_stats_collection.update_one(
                    {'user_id': user_id},
                    {'$inc': {'message_count': 1}, '$set': {'last_message_date': message_date}}
                )
        else:
            # Пользователь не зарегистрирован в боте
            # Удаляем сообщение пользователя
            context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

            # Отправляем сообщение о регистрации и приглашение зарегистрироваться
            invite_message = f"@{username}, салют!\n\nЧтобы писать сообщения в чате, тебе сначала нужно зарегистрироваться в нашем боте. Это не займет у тебя больше минуты."
            keyboard = [[InlineKeyboardButton("Зарегистрироваться", url="t.me/Cyndycate_invaterbot?start=yjkqU3t1U8")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id=chat_id, text=invite_message, reply_markup=reply_markup)
    except Exception as e:
        print("Error handling message:", e)


    except Exception as e:
        print("Error handling message:", e)


def me(update, context):
    try:
        # Получаем идентификатор пользователя, отправившего сообщение
        user_id = update.message.from_user.id

        # Получаем данные пользователя из коллекции users
        user_data = users_collection.find_one({'id': user_id})

        if user_data:
            # Получаем данные о пользователе из коллекции users_stats
            user_stats_data = users_stats_collection.find_one({'user_id': user_id})

            # Если данные о пользователе есть в users_stats, используем их
            if user_stats_data:
                username = user_stats_data.get('username', 'Нет')
                message_count = user_stats_data.get('message_count', 0)
                last_activity_date = user_stats_data.get('last_message_date', 'Нет данных')
                reputation = user_data.get('reputation', 0)

                # Формируем сообщение профиля с учетом количества сообщений, репутации и информации о пригласившем пользователе
                profile_message = f"Имя пользователя: @{username}\nКоличество сообщений: {message_count}\nБаланс: {reputation}\nПоследняя активность: {last_activity_date}"

                # Создаем инлайн клавиатуру с кнопкой "Открыть бот"
                keyboard = [[InlineKeyboardButton("Открыть бот 🤖", url="t.me/Cyndycate_invaterbot?start=yjkqU3t1U8")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Отправляем сообщение с профилем пользователя, используя реплай на сообщение, которое вызвало команду /me
                context.bot.send_message(chat_id=update.message.chat_id, text=profile_message, reply_to_message_id=update.message.message_id, reply_markup=reply_markup)
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Данные пользователя отсутствуют", reply_to_message_id=update.message.message_id)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Вы еще не зарегистрированы", reply_to_message_id=update.message.message_id)

    except Exception as e:
        print("Error handling /me command:", e)

# Функция обработки команды /top
def top(update, context):
    try:
        # Получаем топ-10 пользователей по количеству репутации
        top_users = users_collection.find().sort("reputation", pymongo.DESCENDING).limit(10)

        if top_users:
            # Формируем сообщение с топ-10 пользователями
            top_message = "Топ 10 холдеров $FRFL:\n\n"
            for index, user in enumerate(top_users, start=1):
                username = user.get('username', 'Нет')
                reputation = user.get('reputation', 0)
                top_message += f"{index}. @{username} - {reputation} $FRFL\n"

            # Отправляем сообщение с топ-10 пользователями
            context.bot.send_message(chat_id=update.message.chat_id, text=top_message)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Пока нет пользователей с репутацией")
    except Exception as e:
        print("Error handling /top command:", e)

# Функция обработки команды /rain
def rain(update, context):
    try:
        # Получаем ID пользователя, отправившего команду
        sender_user_id = update.message.from_user.id

        # Получаем количество токенов, которое отправляется
        if len(context.args) == 1:
            try:
                tokens_to_give = int(context.args[0])
                if tokens_to_give <= 0:
                    context.bot.send_message(chat_id=update.message.chat_id, text="Количество токенов должно быть больше нуля.")
                    return
            except ValueError:
                context.bot.send_message(chat_id=update.message.chat_id, text="Некорректное количество токенов.")
                return
        else:
            # Устанавливаем значение по умолчанию, если пользователь не указал количество токенов
            tokens_to_give = 10

        # Получаем баланс отправителя из коллекции users
        sender_data = users_collection.find_one({'id': sender_user_id})
        if sender_data:
            sender_balance = sender_data.get('reputation', 0)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Вы не зарегистрированы.")
            return

        # Проверяем, достаточно ли у пользователя баланса для раздачи токенов
        if sender_balance >= tokens_to_give:
            # Получаем список всех пользователей, кроме отправителя
            all_users = list(users_collection.find({"id": {"$ne": sender_user_id}}))

            # Считаем количество получателей
            num_recipients = len(all_users)

            # Проверяем, что есть хотя бы один получатель
            if num_recipients > 0:
                # Рассчитываем количество токенов для каждого получателя
                tokens_per_recipient = tokens_to_give / num_recipients

                # Начисляем токены каждому получателю
                for user in all_users:
                    recipient_id = user['id']
                    # Начисляем токены пользователю
                    users_collection.update_one({"id": recipient_id}, {"$inc": {"reputation": tokens_per_recipient}})

                # Списываем токены у отправителя
                users_collection.update_one({"id": sender_user_id}, {"$inc": {"reputation": -tokens_to_give}})

                # Получаем имена пользователей-получателей
                recipient_usernames = [f"@{user['username']}" for user in all_users]

                # Формируем сообщение об успешной раздаче
                recipients_message = ', '.join(recipient_usernames)
                message_text = f"Раздача токенов завершена. @{sender_data['username']} раздал {tokens_to_give} токенов между {num_recipients} пользователями: {recipients_message}."

                # Отправляем сообщение
                context.bot.send_message(chat_id=update.message.chat_id, text=message_text)
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Недостаточно пользователей для раздачи.")
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Недостаточно токенов на балансе.")
    except Exception as e:
        print("Error handling /rain command:", e)




# Создаем объект updater и передаем ему токен вашего бота
updater = Updater(token=TOKEN, use_context=True)

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

# Регистрируем обработчик команды /rain
rain_handler = CommandHandler('rain', rain)
dispatcher.add_handler(rain_handler)

# Запускаем бота
updater.start_polling()
updater.idle()
