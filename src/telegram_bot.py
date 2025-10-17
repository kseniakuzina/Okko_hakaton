import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from .db_client import search_movies_by_keywords, get_all_genres

# Загружаем переменные из .env файла
load_dotenv()

class SimpleFilmBot:
    def __init__(self):
        # Используем токен напрямую, если .env не загрузился
        self.token = os.getenv('TELEGRAM_BOT_TOKEN', "8415396611:AAGDvLAQiu4lVD-YGLgaEStZkDBqHzYJsJQ")
        
        print(f"✅ Используем токен: {self.token[:10]}...")
        
        # Получаем доступные жанры при запуске
        self.available_genres = get_all_genres()
        
        # Создаем приложение
        self.application = Application.builder().token(self.token).build()
        
        # Добавляем обработчики
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настраиваем обработчики команд и сообщений"""
        # Обработчик команды /start
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Обработчик команды /help
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Обработчик команды /genres
        self.application.add_handler(CommandHandler("genres", self.genres_command))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /start"""
        user = update.effective_user
        welcome_text = f"""
Привет, {user.first_name}! 🎬

Я - твой помощник по подбору фильмов в Okko. 
Я помогу тебе выбрать фильм по настроению, погоде и предпочтениям.

Просто напиши:
- Какое у тебя настроение?
- Какой жанр хочешь посмотреть?
- Или просто опиши, какой фильм ищешь!

Используй /genres чтобы посмотреть все доступные жанры
Используй /help для справки

Давай начнем! Как ты себя чувствуешь сегодня? 😊
        """
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /help"""
        help_text = """
🤖 Я умею:

🎯 Подбирать фильмы по настроению
🌤️ Учитывать погоду за окном  
🎭 Рекомендовать по любимым жанрам
💬 Общаться и уточнять предпочтения

📝 Просто напиши мне:
- "Хочу комедию" 
- "Посоветуй что-то грустное"
- "Фильм на вечер"
- "Боевик с крутыми спецэффектами"

Или используй команды:
/genres - посмотреть все жанры
/help - эта справка
        """
        await update.message.reply_text(help_text)
    
    async def genres_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает все доступные жанры"""
        if self.available_genres:
            genres_text = "🎭 Доступные жанры:\n\n" + "\n".join([f"• {genre}" for genre in self.available_genres])
            genres_text += "\n\nПросто напиши название жанра, и я подберу фильмы!"
        else:
            genres_text = "❌ Не удалось загрузить список жанров из базы данных"
        
        await update.message.reply_text(genres_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает обычные текстовые сообщения"""
        user_message = update.message.text
        user = update.effective_user
        
        # Показываем, что бот думает
        await update.message.reply_chat_action(action="typing")
        
        # Ищем фильмы по сообщению пользователя
        films = search_movies_by_keywords(user_message, limit=3)
        
        if films:
            # Формируем красивый ответ с найденными фильмами
            response = self.format_films_response(films, user.first_name, user_message)
        else:
            response = f"😔 {user.first_name}, не нашёл подходящих фильмов по запросу: '{user_message}'\n\nПопробуй:\n- Указать другой жанр\n- Использовать команду /genres\n- Просто написать о своём настроении"
        
        await update.message.reply_text(response)
    
    def format_films_response(self, films: list, user_name: str, user_message: str) -> str:
        """Форматирует ответ с фильмами"""
        response = f"🎉 {user_name}, вот что я нашёл для тебя!\n\n"
        
        for i, film in enumerate(films, 1):
            response += f"🎬 {film['title']}\n"
            if film.get('genres'):
                response += f"   🎭 Жанр: {film['genres']}\n"
            if film.get('release_date'):
                year = film['release_date'].year
                response += f"   📅 Год: {year}\n"
            if film.get('age_rating'):
                response += f"   🔞 Возраст: {film['age_rating']}+\n"
            if film.get('description') and len(film['description']) > 100:
                # Обрезаем длинное описание
                desc = film['description'][:100] + "..."
                response += f"   📖 {desc}\n"
            response += "\n"
        
        response += "Хочешь посмотреть что-то ещё? Просто напиши! 😊"
        return response

    def run(self):
        """Запускает бота"""
        print("Бот запущен...")
        self.application.run_polling()