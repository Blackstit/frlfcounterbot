from database import connect_to_database
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from datetime import datetime, timedelta
import markups
import pymongo

# Получение коллекций базы данных
chats_stats_collection, users_collection, commands_collection = connect_to_database()

# Функция обработки команды /me
def me(update, context):
    try:
        # Получаем идентификатор пользователя, отправившего сообщение
        user_id = str(update.message.from_user.id)

        # Получаем данные пользователя из коллекции users
        user_data = users_collection.find_one({'_id': user_id})

        if user_data:
            # Получаем данные о пользователе из коллекции chats_stats
            chat_title = update.message.chat.title
            chat_stats_data = chats_stats_collection.find_one({'chat_title': chat_title})
            
            if chat_stats_data and 'users' in chat_stats_data:
                user_stats_data = chat_stats_data['users'].get(user_id, {})
                message_count = user_stats_data.get('message_count', 0)
                last_activity_date = user_stats_data.get('last_message_date', 'Нет данных')
                
                # Определяем период последней активности
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                yesterday = today - timedelta(days=1)
                this_week_start = today - timedelta(days=today.weekday())
                this_month_start = today.replace(day=1)

                # Определяем период последней активности пользователя
                last_activity_date = datetime.strptime(last_activity_date, "%Y-%m-%d %H:%M:%S")
                if last_activity_date >= today:
                    last_activity = "Сегодня"
                elif last_activity_date >= yesterday:
                    last_activity = "Вчера"
                elif last_activity_date >= this_week_start:
                    last_activity = "На этой неделе"
                elif last_activity_date >= this_month_start:
                    last_activity = "В этом месяце"
                else:
                    last_activity = "Давно"

                # Получаем данные о пользователе
                first_name = user_data.get('first_name', 'Нет')
                role_name = user_data.get('roles', [{'role_name': 'Newbie'}])[0]['role_name']
                username = user_data.get('username', 'Нет')
                reputation = user_data.get('reputation', 0)
                message_cost = user_data.get('message_cost', 0.5)
                balance = user_data.get('balance', 0)

                # Формируем сообщение профиля
                profile_message = (
                    f"*Имя пользователя*: {first_name}\n"
                    f"*Username*: @{username}\n"
                    f"*Роль*: {role_name}\n"
                    f"*Репутация*: {reputation}\n"
                    f"*Стоимость сообщения*: {message_cost}\n"
                    f"*Количество сообщений*: {message_count}\n"
                    f"*Последняя активность*: {last_activity}\n"
                    f"*Баланс*: {balance}\n"
                )

                # Отправляем сообщение с профилем пользователя
                context.bot.send_message(chat_id=update.message.chat_id, text=profile_message, reply_to_message_id=update.message.message_id, parse_mode="Markdown", reply_markup=markups.profile_markup)
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Данные пользователя отсутствуют", reply_to_message_id=update.message.message_id)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Вы еще не зарегистрированы", reply_to_message_id=update.message.message_id)

    except Exception as e:
        print("Error handling /me command:", e)


# Функция обработки команды /top
# Выводит ТОП10 держателей монетки $FRFL
def top(update, context):
    try:
        # Получаем топ-10 пользователей по балансу $FRFL
        top_users = users_collection.find().sort("balance", pymongo.DESCENDING).limit(10)

        if top_users:
            # Формируем сообщение с топ-10 пользователями
            top_message = "Топ 10 держателей $FRFL:\n\n"
            for index, user in enumerate(top_users, start=1):
                username = user.get('username', 'Нет')
                balance = user.get('balance', 0)
                top_message += f"{index}. @{username} - {balance} $FRFL\n"

            # Отправляем сообщение с топ-10 пользователями
            context.bot.send_message(chat_id=update.message.chat_id, text=top_message)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Пока нет пользователей с балансом $FRFL")
    except Exception as e:
        print("Error handling /top command:", e)


# Функция обработки команды /rain
# Команда позволяет устроить некий розыгрышь среди 1-5 случайными пользователями чата, которые прошли регистрацию в основном боте
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
            tokens_to_give = 5

        # Получаем информацию о пользователе, отправившем команду
        sender_data = users_collection.find_one({'_id': str(sender_user_id)})
        if sender_data:
            sender_balance = sender_data.get('balance', 0)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Вы не зарегистрированы.")
            return

        # Проверяем, достаточно ли у пользователя баланса для раздачи токенов
        if sender_balance >= tokens_to_give:
            # Получаем список всех пользователей, кроме отправителя
            all_users = list(users_collection.find({"_id": {"$ne": str(sender_user_id)}}))

            # Считаем количество получателей
            num_recipients = len(all_users)

            # Проверяем, что есть хотя бы один получатель
            if num_recipients > 0:
                # Рассчитываем количество токенов для каждого получателя
                tokens_per_recipient = tokens_to_give / num_recipients

                # Начисляем токены каждому получателю
                for user in all_users:
                    recipient_id = user['_id']
                    # Начисляем токены пользователю
                    users_collection.update_one({"_id": recipient_id}, {"$inc": {"balance": tokens_per_recipient}})

                # Списываем токены у отправителя
                users_collection.update_one({"_id": str(sender_user_id)}, {"$inc": {"balance": -tokens_to_give}})

                # Получаем имена пользователей-получателей
                recipient_usernames = [f"@{user['username']}" for user in all_users]

                # Формируем сообщение об успешной раздаче
                recipients_message = ', '.join(recipient_usernames)
                message_text = f"Раздача токенов завершена. @{sender_data['username']} раздал {tokens_to_give} токенов между {num_recipients} пользователями: {recipients_message}."

                # Отправляем сообщение
                context.bot.send_message(chat_id=update.message.chat_id, text=message_text, reply_markup=markups.rain_markup)
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Недостаточно пользователей для раздачи.")
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Недостаточно токенов на балансе.")
    except Exception as e:
        print("Error handling /rain command:", e)

# Выводит основную информацию о боте и список доступных команд
def help_command(update, context):
    try:
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

# Выводит основную статистику по чату и по боту
def stats_command(update, context):
    try:
        # Получаем количество пользователей в боте
        total_users_count = users_collection.count_documents({})

        # Получаем суммарное количество токенов всех пользователей
        total_tokens_earned = sum(user.get('balance', 0) for user in users_collection.find({}))

        # Получаем количество участников в чате
        chat_id = update.effective_chat.id
        members_count = context.bot.get_chat_members_count(chat_id)

        # Формируем текст статистики
        stats_message = (
            "Статистика FireFly Community\n\n"
            f"*Количество пользователей в боте*: {total_users_count}\n\n"
            f"*Количество участников в чате*: {members_count}\n\n"
            f"*Всего заработано*: {total_tokens_earned} $FRFL"
        )

        # Отправляем сообщение с статистикой
        context.bot.send_message(chat_id=update.message.chat_id, text=stats_message, parse_mode="Markdown", reply_to_message_id=update.message.message_id)

    except Exception as e:
        print("Error handling /stats command:", e)


# Обработчик команды /ref
def referral(update, context):
    try:
        # Получаем идентификатор пользователя, отправившего команду
        user_id = update.message.from_user.id

        # Получаем данные пользователя из коллекции users
        user_data = users_collection.find_one({'_id': str(user_id)})

        if user_data:
            # Формируем реферальную ссылку
            referral_link = user_data['referral_link']

            # Формируем текст сообщения для отправки в чате
            reply_text_chat = (
                "Приглашайте друзей по своей рефферальной ссылке и зарабатывайте до 10% токенов $FRFL "
                "с каждого приведенного вами пользователя!\n\n"
                f"*Ваша реферальная ссылка*: {referral_link}"
            )

            # Формируем текст сообщения для отправки другу
            reply_text_friend = (
                "Привет! Я приглашаю тебя присоединиться к боту FireFly Crypto. "
                "С ним ты можешь зарабатывать токены $FRFL и получать до 10% с каждого пользователя, "
                f"приглашенного тобой. Вот моя реферальная ссылка для регистрации: {referral_link}"
            )

            # Формируем инлайн-клавиатуру для отправки в чате
            keyboard = [[InlineKeyboardButton("Отправить другу", switch_inline_query=reply_text_friend)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправляем сообщение с инлайн-клавиатурой в чат
            context.bot.send_message(chat_id=update.message.chat_id, text=reply_text_chat, reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Вы еще не зарегистрированы", reply_to_message_id=update.message.message_id)
    except Exception as e:
        print("Error handling /ref command:", e)

# Обработчик для обработки нажатия на кнопку "Отправить другу"
def send_to_friend(update, context):
    try:
        query = update.callback_query
        # Отправляем сообщение с текстом, переданным в инлайн-запросе
        context.bot.send_message(chat_id=query.message.chat_id, text=query.inline_message_id)
    except Exception as e:
        print("Error handling send_to_friend callback:", e)
