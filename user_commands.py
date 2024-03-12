from database import connect_to_database
import markups
import pymongo

# Получение коллекций базы данных
users_stats_collection, users_collection, commands_collection, tasks_collection = connect_to_database()

#  Функция обработки команды /me
# Команда выводит основную информацию о пользователе в чат
# Имя пользователя
# Колличество сообщений
# Баланс
# Дата последней активности
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

                # Отправляем сообщение с профилем пользователя, используя реплай на сообщение, которое вызвало команду /me
                context.bot.send_message(chat_id=update.message.chat_id, text=profile_message, reply_to_message_id=update.message.message_id, reply_markup=markups.profile_markup)
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

# Выводит основную статистику по чату и по боту
        # Всего пользователей в боте
        # Отправлено сообщений
        # Всего заработано
        # Выполнено заданий

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

        # Получаекм количество участников в чате
        chat_id = update.effective_chat.id
        members_count = context.bot.get_chat_members_count(chat_id)

        # Формируем текст статистики
        stats_message = (
            "Статистика FireFly Community\n\n"
            f"*Количество пользователей в боте*: {total_users_count}\n\n"
            f"*Количество участников в чате*: {members_count}\n\n"
            f"*Отправлено сообщений*: {total_messages_count}\n\n"
            f"*Всего заработано*: {total_tokens_earned}\n\n"
            f"*Выполнено заданий*: {total_tasks_completed}"
        )

        # Отправляем сообщение с статистикой
        context.bot.send_message(chat_id=update.message.chat_id, text=stats_message, parse_mode="Markdown", reply_to_message_id=update.message.message_id)

    except Exception as e:
        print("Error handling /stats command:", e)


# Обработчик команды /ref
def referral(update, context):
    # Получаем идентификатор пользователя, отправившего команду
    user_id = update.message.from_user.id

    # Получаем данные пользователя из коллекции users
    user_data = users_collection.find_one({'id': user_id})

    if user_data:
        # Формируем реферальную ссылку
        referral_link = f"t.me/FireFlyCCbot?start={user_data['referral_code']}"

        # Формируем текст сообщения
        reply_text = (
            "Приглашайте друзей по своей рефферальной ссылке и зарабатывайте до 10% токенов $FRFL "
            "с каждого приведенного вами пользователя!\n\n"
            f"*Ваша реферальная ссылка*: {referral_link}"
        )

        # Отправляем сообщение с инлайн-клавиатурой
        context.bot.send_message(chat_id=update.message.chat_id, text=reply_text, reply_markup=markups.ref_reply_markup, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Вы еще не зарегистрированы", reply_to_message_id=update.message.message_id)

# Обработчик для обработки нажатия на кнопку "Отправить другу"
def send_to_friend(update, context):
    query = update.callback_query
    # Отправляем сообщение с текстом, переданным в инлайн-запросе
    context.bot.send_message(chat_id=query.message.chat_id, text=query.inline_message_id)
    