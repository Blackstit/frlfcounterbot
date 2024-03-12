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

def message_handler(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время

    # Получаем данные пользователя из коллекции users
    user_data = users_collection.find_one({"_id": str(user_id)})
    if user_data:
        message_cost = user_data.get('message_cost', 0.5)  # Значение по умолчанию 0.5, если не задано
        balance = user_data.get('balance', 0)
        new_balance = balance + message_cost

        # Обновляем баланс пользователя в коллекции
        users_collection.update_one({"_id": str(user_id)}, {"$set": {"balance": new_balance}})

        # Пользователь зарегистрирован в боте, обновляем статистику сообщений
        users_stats_collection.update_one(
            {'user_id': str(user_id)},
            {'$inc': {'message_count': 1}, '$set': {'last_message_date': message_date}},
            upsert=True
        )
    else:
        # Если пользователь не зарегистрирован в боте, отправляем приглашение к регистрации
        invite_message = f"@{username}, салют!\n\nЧтобы писать сообщения в чате, тебе сначала нужно зарегистрироваться в нашем боте. Это не займет у тебя больше минуты."
        context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        context.bot.send_message(chat_id=chat_id, text=invite_message, reply_markup=markups.registration_markup)


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
