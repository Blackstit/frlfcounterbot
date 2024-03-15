import pymongo
import os
import markups
import user_commands
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from database import connect_to_database
from telegram.ext.dispatcher import run_async

# Получение коллекций базы данных
chats_stats_collection, users_collection, commands_collection = connect_to_database()

# Получаем токен
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def welcome_message(update: Update, context: CallbackContext):
    new_chat_members = update.message.new_chat_members
    chat_title = update.message.chat.title  # Получаем название чата
    chat_id = update.message.chat_id
    bot_user = context.bot.get_me()

    # Проверяем, существует ли уже статистика для этого чата
    chat_stats_data = chats_stats_collection.find_one({"chat_title": chat_title})

    if not chat_stats_data:
        # Создаем новую статистику чата, если ее нет
        chat_stats_data = {
            "chat_title": chat_title,
            "total_messages_count": 0,
            "users": {}
        }
        chats_stats_collection.insert_one(chat_stats_data)

    for new_member in new_chat_members:
        if not new_member.is_bot:
            # Проверяем, есть ли у пользователя запись в коллекции users_collection
            user_data = users_collection.find_one({"_id": str(new_member.id)})
            if user_data:
                # Пользователь уже зарегистрирован
                welcome_text = f"@{new_member.username}!\n\nДобро пожаловать в чат '{chat_title}'!"
                context.bot.send_message(chat_id=chat_id, text=welcome_text)
            else:
                # Пользователь не зарегистрирован, отправляем приглашение к регистрации
                invite_message = f"@{new_member.username}, салют!\n\nЧтобы писать сообщения в чате, сначала зарегистрируйся в нашем боте."
                context.bot.send_message(chat_id=chat_id, text=invite_message, reply_markup=markups.registration_markup)

def message_handler(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    message_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Текущая дата и время

    try:
        # Получаем данные пользователя из коллекции users
        user_data = users_collection.find_one({"_id": str(user_id)})
        if user_data:
            # Получаем актуальную стоимость сообщения из данных пользователя
            message_cost = user_data.get('message_cost', 0.5)
            # Разрешаем отправку сообщений
            balance = user_data.get('balance', 0)
            new_balance = balance + message_cost

            # Обновляем баланс пользователя в коллекции
            users_collection.update_one({"_id": str(user_id)}, {"$set": {"balance": new_balance}})

            # Обновляем статистику сообщений в коллекции chat_stats для данного чата
            chat_title = update.message.chat.title
            chats_stats_collection.update_one(
                {"chat_title": chat_title},
                {"$inc": {"total_messages_count": 1, f"users.{user_id}.message_count": 1},
                 "$set": {f"users.{user_id}.last_message_date": message_date}},
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
dispatcher.add_handler(CommandHandler("ref", user_commands.referral)) # Обработчик команды /ref

dispatcher.add_handler(CallbackQueryHandler(user_commands.send_to_friend, pattern="^send_to_friend$")) # Обработчик нажатия на кнопку "Отправить другу"
dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_message, run_async=True)) # Обработчик новых участников чата

# Запускаем бота
updater.start_polling()
updater.idle()
