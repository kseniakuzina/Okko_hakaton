from src.telegram_bot import SimpleFilmBot
from src.db_client import test_db_connection, get_all_genres
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

if __name__ == '__main__':
    print("🚀 Запуск приложения...")
    
    # Проверяем загрузку .env
    print("🔧 Проверяем загрузку переменных окружения...")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        print(f"✅ Токен бота найден: {token[:10]}...")
    else:
        print("❌ Токен бота не найден!")
    
    print("\n🔍 Проверяем подключение к БД...")
    if test_db_connection():
        print("\n📚 Загружаем доступные жанры...")
        genres = get_all_genres()
        print(f"✅ Доступно жанров: {len(genres)}")
        
        print("\n🎬 Запускаем бота...")
        bot = SimpleFilmBot()
        bot.run()
    else:
        print("\n❌ Проблемы с подключением к БД.")
        print("Запускаем бота в режиме без БД...")
        bot = SimpleFilmBot()
        bot.run()