import user_commands
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Клавиатура для приглашения на регистрацию
registration_keyboard = [[InlineKeyboardButton("Зарегистрироваться", url="t.me/FireFlyCCbot?start=sajydPfNp4")]]
registration_markup = InlineKeyboardMarkup(registration_keyboard)


# Создаем инлайн клавиатуру для /me 
profile_keyboard = [[InlineKeyboardButton("Открыть бот 🤖", url="t.me/FireFlyCCbot?start=sajydPfNp4")]]
profile_markup = InlineKeyboardMarkup(profile_keyboard)

# Создаем инлайн клавиатуру для /rain (Клавиатура со справкой на telegra.ph)
rain_keyboard = [[InlineKeyboardButton("Что это?", url="https://telegra.ph/Vy-popali-pod-dozhd-03-12")]]
rain_markup = InlineKeyboardMarkup(rain_keyboard)

# Формируем инлайн-клавиатуру
ref_keyboard = [[InlineKeyboardButton("Отправить другу", switch_inline_query=user_commands.reply_text)]]
ref_reply_markup = InlineKeyboardMarkup(ref_keyboard )