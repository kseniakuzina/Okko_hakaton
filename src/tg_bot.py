import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_service import AIService

# Загружаем переменные
load_dotenv()

class SmartFilmBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.ai_service = AIService()
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        print("🚀 Умный бот Okko запущен и готов к работе!")
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("genres", self.genres_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        welcome_text = f"""
Привет, {user.first_name}! 🎬

Я - твой умный помощник по подбору фильмов в Okko! 

Я понимаю твои предпочтения и настроение, чтобы найти идеальные фильмы.

✨ *Что я умею:*
• Понимать жанры (комедия, драма, боевик, фантастика и др.)
• Учитывать год выпуска (старые, новые, современные)
• Искать по настроению (веселое, грустное, романтичное)

*Просто напиши что хочешь посмотреть:*
• "Комедия для поднятия настроения"
• "Грустная драма про любовь"  
• "Старый боевик 90-х"
• "Что-то романтическое на вечер"

Давай начнем! Что ты хочешь посмотреть? 😊
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
🎯 *Как со мной общаться*

*По жанрам:*
🎭 Комедия, Драма, Боевик, Фантастика
🔮 Ужасы, Триллер, Мелодрама, Приключения

*По году:*
📅 "Старый фильм", "Кино 90-х", "Современный", "Новинки"

*По настроению:*
😊 "Веселое кино", "Грустная история"
❤️ "Романтическое", "Что-то легкое"

*Примеры запросов:*
• "Хочу посмотреть комедию"
• "Грустная драма про отношения"
• "Старый боевик в стиле 90-х"
• "Романтическое кино на вечер"

Или просто опиши свое настроение! 🎥
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def genres_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает доступные жанры"""
        genres_text = """
🎭 *Доступные жанры:*

*Основные:*
• Комедия - для смеха и хорошего настроения
• Драма - глубокие эмоциональные истории  
• Боевик - экшен, приключения, адреналин
• Фантастика - космос, будущее, технологии

*Дополнительные:*
• Ужасы - страшные и мистические истории
• Триллер - напряженные детективы
• Мелодрама - романтические истории
• Приключения - путешествия и открытия

Выбери жанр и напиши, например: "Хочу комедию" 😊
        """
        await update.message.reply_text(genres_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        user = update.effective_user
        
        # Показываем что бот "думает"
        await update.message.reply_chat_action(action="typing")
        
        try:
            # Используем AI для анализа и поиска
            result = self.ai_service.search_with_ai(user_message)
            response = result["response"]
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            print(f"❌ Ошибка в боте: {e}")
            await update.message.reply_text(
                "⚠️ Упс! Произошла небольшая ошибка. Попробуй еще раз!\n\n"
                "Можешь написать что-то простое, например:\n"
                "• \"Комедия\"\n• \"Драма\"\n• \"Боевик\""
            )

    def run(self):
        self.application.run_polling()

if __name__ == '__main__':
    bot = SmartFilmBot()
    bot.run()