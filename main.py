import pymongo
import os
import markups
import user_commands
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from database import connect_to_database

# Получение коллекций базы данных
users_stats_collection, users_collection, commands_collection, tasks_collection = connect_to_database()

# Получаем токен
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def message_handler(message):
    user_id = str(message.chat.id)

    # Получаем данные пользователя из коллекции users
    user_data = users_collection.find_one({"_id": user_id})
    if user_data:
        message_cost = user_data.get('message_cost', 0.5)  # Значение по умолчанию 0.5, если не задано
        balance = user_data.get('balance', 0)
        new_balance = balance + message_cost

        # Обновляем баланс пользователя в коллекции
        users_collection.update_one({"_id": user_id}, {"$set": {"balance": new_balance}})

        # Получаем данные о пользователе из коллекции users_stats
        user_stats_data = users_stats_collection.find_one({'user_id': user_id})

        # Если данные о пользователе есть в users_stats, обновляем их
        if user_stats_data:
            # Обновляем количество отправленных сообщений и дату последнего сообщения
            message_count = user_stats_data.get('message_count', 0) + 1
            last_message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            users_stats_collection.update_one({"user_id": user_id}, {"$set": {"message_count": message_count, "last_message_date": last_message_date}})
        else:
            # Если данных о пользователе нет, создаем новую запись
            last_message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_stats = {"user_id": user_id, "username": message.chat.username, "message_count": 1, "last_message_date": last_message_date}
            users_stats_collection.insert_one(user_stats)
    else:
        # Если данных о пользователе нет, создаем новую запись с дефолтной стоимостью сообщения и балансом
        message_cost = 0.5
        balance = message_cost
        users_collection.insert_one({"_id": user_id, "balance": balance, "message_cost": message_cost})




# Создаем объект updater и передаем ему токен вашего бота
updater = Updater(token=TOKEN, use_context=True)

# Получаем из него диспетчер сообщений
dispatcher = updater.dispatcher

# Регистрируем обработчик сообщений для конкретного чата
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), message_handler))

dispatcher.add_handler(CommandHandler("me", user_commands.me)) # Обработчик команды /me
dispatcher.add_handler(CommandHandler("top", user_commands.top)) # Обработчик команды /top
dispatcher.add_handler(CommandHandler("rain", user_commands.rain)) # Обработчик команды /rain
dispatcher.add_handler(CommandHandler("help", user_commands.help_command)) # Обработчик команды /help
dispatcher.add_handler(CommandHandler("stats", user_commands.stats_command)) # Обработчик команды /stats
dispatcher.add_handler(CommandHandler("ref", user_commands.referral)) # Обработчик команды /ref

dispatcher.add_handler(CallbackQueryHandler(user_commands.send_to_friend, pattern="^send_to_friend$")) # Обработчик нажатия на кнопку "Отправить другу"

# Запускаем бота
updater.start_polling()
updater.idle()
