import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем переменные из .env файла
load_dotenv()

class SimpleFilmBot:
    def __init__(self):
        # Получаем токен из переменных окружения
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("Токен бота не найден! Проверьте файл .env")
        
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

Давай начнем! Как ты себя чувствуешь сегодня? 😊
        """
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /help"""
        help_text = """
Я умею:
🎯 Подбирать фильмы по настроению
🌤️ Учитывать погоду за окном  
🎭 Рекомендовать по любимым жанрам
💬 Общаться и уточнять предпочтения

Просто напиши мне о своем настроении или какие фильмы тебе нравятся!
        """
        await update.message.reply_text(help_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает обычные текстовые сообщения"""
        user_message = update.message.text
        user = update.effective_user
        
        # Простой анализ сообщения пользователя
        response = self.generate_simple_response(user_message, user.first_name)
        
        await update.message.reply_text(response)
    
    def generate_simple_response(self, message: str, user_name: str) -> str:
        """Генерирует простой ответ на основе ключевых слов"""
        message_lower = message.lower()
        
        # Простые правила для ответов
        if any(word in message_lower for word in ['привет', 'hello', 'hi', 'здаров']):
            return f"Привет, {user_name}! Рад тебя видеть! Какой фильм хочешь посмотреть сегодня? 🎥"
        
        elif any(word in message_lower for word in ['комедия', 'смех', 'веселы', 'юмор']):
            return "Отлично! Комедии - это то, что нужно для поднятия настроения! 🎭\nПопробуй посмотреть 'Иван Васильевич меняет профессию' или 'Одни из нас'"
        
        elif any(word in message_lower for word in ['грустн', 'печал', 'тоск', 'дожд']):
            return "Понимаю... Иногда нужно погрустить. Может быть, драма или мелодрама? 🌧️\nКак насчёт 'Довода' или 'Начала'?"
        
        elif any(word in message_lower for word in ['устал', 'утомил', 'упадок сил']):
            return "Похоже, тебе нужно что-то вдохновляющее! 🚀\nРекомендую посмотреть мотивационное кино или приключенческий фильм!"
        
        elif any(word in message_lower for word in ['экшн', 'боевик', 'action', 'стрельба']):
            return "Экшн - отличный выбор! 💥\nДля тебя есть подборка лучших боевиков этого года!"
        
        elif any(word in message_lower for word in ['фантастика', 'научный', 'космос', 'будущ']):
            return "Фантастика открывает новые миры! 🪐\nУ нас есть отличные научно-фантастические фильмы и сериалы!"
        
        else:
            return f"Интересно, {user_name}! Расскажи подробнее:\n- Какое у тебя настроение?\n- Какой жанр предпочитаешь?\n- Есть любимые фильмы или актёры?\n\nЯ помогу найти идеальный фильм для тебя! 😊"

    def run(self):
        """Запускает бота"""
        print("Бот запущен...")
        self.application.run_polling()

# Точка входа
if __name__ == '__main__':
    bot = SimpleFilmBot()
    bot.run()