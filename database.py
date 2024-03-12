import pymongo
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение переменных окружения для подключения к MongoDB
MONGO_URL = os.getenv("MONGO_URL")

def connect_to_database():
    # Подключение к MongoDB и определение коллекций
    client = pymongo.MongoClient(MONGO_URL)
    db = client['test']

    users_stats_collection = db.get_collection('users_stats')  # Коллекция для статистики пользователей
    users_collection = db.get_collection('users')  # Коллекция для пользователей
    commands_collection = db.get_collection('commands')  # Коллекция для статистики пользователей
    tasks_collection = db.get_collection('completed_tasks')  # Коллекция для выполненных заданий

    return users_stats_collection, users_collection, commands_collection, tasks_collection
