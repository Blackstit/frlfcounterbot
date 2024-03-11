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
commands_collection = db['commands']  # Коллекция для статистики пользователей
tasks_collection = db['completed_tasks'] # Коллекция для выполненных заданий


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
            keyboard = [[InlineKeyboardButton("Зарегистрироваться", url="t.me/FireFlyCCbot?start=sajydPfNp4")]]
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
                keyboard = [[InlineKeyboardButton("Открыть бот 🤖", url="t.me/FireFlyCCbot?start=sajydPfNp4")]]
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

def help_command(update, context):
    try:
        # Получаем ID пользователя, отправившего команду
        user_id = update.message.from_user.id

        # Формируем сообщение приветствия
        welcome_message = ("Привет, я бот FireFly Crypto!\n\n"
                           "Я создан для того, чтобы наше с вами сообщество развивалось, "
                           "пользователи богатели, а в чате был порядок.\n\n"
                           "Просто общайся в чате, не нарушай наши правила и за каждое твое сообщение "
                           "я буду тебе платить токенами $FRFL.\n\n"
                           "Вот основные команды, которые тебе стоит знать:\n\n")

        # Получаем список всех команд из коллекции commands
        commands = commands_collection.find({})

        # Формируем список команд и их описаний
        commands_list = []
        for command in commands:
            command_name = command.get('command_name', '')
            command_description = command.get('command_description', '')
            commands_list.append(f"{command_name}: {command_description}")

        # Собираем все команды в одну строку
        commands_text = "\n\n".join(commands_list)

        # Формируем итоговое сообщение
        final_message = welcome_message + commands_text

        # Отправляем сообщение
        context.bot.send_message(chat_id=update.message.chat_id, text=final_message, reply_to_message_id=update.message.message_id)

    except Exception as e:
        print("Error handling /help command:", e)

def stats_command(update, context):
    try:
        # Получаем количество пользователей в боте
        total_users_count = users_collection.count_documents({})

        # Получаем количество сообщений
        total_messages_count = users_stats_collection.aggregate([{"$group": {"_id": None, "total": {"$sum": "$message_count"}}}])
        total_messages_count = list(total_messages_count)[0]['total'] if total_messages_count else 0

        # Получаем суммарное количество токенов всех пользователей
        total_tokens_earned = sum(user.get('reputation', 0) for user in users_collection.find({}))

        # Получаем сумму всех выполненных заданий
        total_tasks_completed = tasks_collection.count_documents({})

        # Формируем текст статистики
        stats_message = (
            "Статистика FireFly Community\n\n"
            f"*Всего пользователей в боте*: {total_users_count}\n\n"
            f"*Отправлено сообщений*: {total_messages_count}\n\n"
            f"*Всего заработано*: {total_tokens_earned}\n\n"
            f"*Выполнено заданий*: {total_tasks_completed}"
        )

        # Отправляем сообщение с статистикой
        context.bot.send_message(chat_id=update.message.chat_id, text=stats_message, parse_mode="Markdown", reply_to_message_id=update.message.message_id)

    except Exception as e:
        print("Error handling /stats command:", e)


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

# Регистрируем обработчик команды /help
help_handler = CommandHandler('help', help_command)
dispatcher.add_handler(help_handler)

# Регистрируем обработчик команды /stats
stats_handler = CommandHandler('stats', stats_command)
dispatcher.add_handler(stats_handler)

# Запускаем бота
updater.start_polling()
updater.idle()
