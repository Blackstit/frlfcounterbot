import pymongo
import os
import markups
import user_commands
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from database import connect_to_database

# Получение коллекций базы данных
users_stats_collection, users_collection, commands_collection, tasks_collection = connect_to_database()

# Получаем токен
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def message_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время

    # Проверяем, существует ли запись о пользователе в коллекции users
    user_data = users_collection.find_one({'id': user_id})
    try:
        if user_data:
            # Пользователь зарегистрирован в боте
            users_stats_collection.update_one(
                {'user_id': user_id},
                {'$inc': {'message_count': 1}, '$set': {'last_message_date': message_date}},
                upsert=True
            )
        else:
            # Пользователь не зарегистрирован в боте
            invite_message = f"@{username}, салют!\n\nЧтобы писать сообщения в чате, тебе сначала нужно зарегистрироваться в нашем боте. Это не займет у тебя больше минуты."
            context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
            context.bot.send_message(chat_id=chat_id, text=invite_message, reply_markup=markups.registration_markup)
    except Exception as e:
        print("Error handling message:", e)


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
dispatcher.add_handler(CommandHandler("memberscount", members_count)) # Обработчик команды /memberscount

# Запускаем бота
updater.start_polling()
updater.idle()
