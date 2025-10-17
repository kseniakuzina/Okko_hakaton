import os
import json
import requests
import re
from typing import Dict, Any
from dotenv import load_dotenv
from db_client import search_movies, search_by_keywords, search_by_year

# Загружаем переменные из .env
load_dotenv()

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        
    def analyze_user_request(self, user_message: str) -> Dict[str, Any]:
        """
        Анализирует сообщение пользователя через OpenRouter
        """
        system_prompt = """Ты - ассистент для анализа запросов о фильмах. 
        Пользователь пишет на русском языке. Твоя задача - извлечь жанры, годы и ключевые слова из запроса.

        ВАЖНО: 
        1. Если пользователь указывает конкретный год (например, "2021", "2020 год", "фильмы 2021"), 
           то нужно установить min_year и max_year в этот год.
        
        2. Если пользователь использует слова указывающие на период:
           - "старые", "ретро", "советские", "90-х", "80-х" → min_year: 1950, max_year: 2000
           - "новые", "свежие", "последние", "современные", "недавние" → min_year: 2020, max_year: 2024
           - "2000-е", "двухтысячные" → min_year: 2000, max_year: 2009
           - "2010-е" → min_year: 2010, max_year: 2019
           - "нестарые", "средние" → min_year: 2001, max_year: 2019
        
        3. Если пользователь указывает диапазон годов:
           - "фильмы 2010-2015" → min_year: 2010, max_year: 2015
           - "с 2018 по 2020" → min_year: 2018, max_year: 2020
        4. если пользователь не указал вообще ничего про год или время то в max_year запиши текущий 2025 год чтобы не предлагались невыпущенные фильмы

        Верни ответ в формате JSON:
        {
            "genres": ["список жанров из запроса"],
            "keywords": "ключевые слова для поиска в описании",
            "min_year": минимальный год (если есть),
            "max_year": максимальный год (если есть)
        }

        Примеры:
        - "Хочу посмотреть фильмы 2021 года" → {"genres": [], "keywords": "фильмы", "min_year": 2021, "max_year": 2021}
        - "Комедии 2020 года" → {"genres": ["комедия"], "keywords": "комедии", "min_year": 2020, "max_year": 2020}
        - "Старые советские комедии" → {"genres": ["комедия"], "keywords": "советские комедии", "min_year": 1950, "max_year": 2000}
        - "Новые драмы" → {"genres": ["драма"], "keywords": "драмы", "min_year": 2020, "max_year": 2024}
        - "Фильмы 2000-х годов" → {"genres": [], "keywords": "фильмы", "min_year": 2000, "max_year": 2009}
        - "Боевики 2015-2020" → {"genres": ["боевик"], "keywords": "боевики", "min_year": 2015, "max_year": 2020}
        - "Нестарые триллеры" → {"genres": ["триллер"], "keywords": "триллеры", "min_year": 2001, "max_year": 2019}
        - "Современная фантастика" → {"genres": ["фантастика"], "keywords": "фантастика", "min_year": 2020, "max_year": 2024}
        """

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.0-flash-thinking-exp:free",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 500
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"✅ AI анализ успешен: {content}")
                
                analysis = json.loads(content)
                analysis["user_intent"] = f"поиск {', '.join(analysis.get('genres', []))}"
                analysis["mood"] = ""
                
                return analysis
            else:
                print(f"❌ Ошибка OpenRouter: {response.status_code}")
                return self._fallback_analysis(user_message)
                
        except Exception as e:
            print(f"❌ Ошибка в analyze_user_request: {e}")
            return self._fallback_analysis(user_message)
    
    def _fallback_analysis(self, user_message: str) -> Dict[str, Any]:
        """Резервный анализ если AI не работает"""
        user_lower = user_message.lower()
        analysis = {
            "genres": [],
            "mood": "",
            "keywords": user_message,
            "min_year": None,
            "max_year": None,
            "user_intent": "поиск фильма"
        }
        
        # Улучшенный анализ по ключевым словам
        genre_keywords = {
            "комедия": ["комедия", "смех", "юмор", "весел", "приключен", "смешн", "веселое", "комедии"],
            "драма": ["драма", "грустн", "печал", "эмоци", "чувств", "трогательн", "грустное", "драмы"],
            "боевик": ["боевик", "экшн", "action", "стрельба", "погон", "битва", "экшен", "боевики"],
            "фантастика": ["фантастика", "космос", "будущ", "научн", "sci-fi", "фэнтези"],
            "ужасы": ["ужас", "хоррор", "страш", "мистик", "жутк", "ужасы"],
            "мелодрама": ["мелодрама", "роман", "любов", "отношен", "чувств", "романтик", "мелодрамы"],
            "триллер": ["триллер", "напряжен", "саспенс", "детектив", "триллеры"],
            "приключения": ["приключен", "путешеств", "экспедиц", "исследова", "приключения"]
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                analysis["genres"].append(genre)
        
        # УЛУЧШЕННЫЙ АНАЛИЗ ГОДА - все возможные варианты
        current_year = 2024
        
        # 1. Поиск конкретных годов
        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        years_found = re.findall(year_pattern, user_message)
        
        if years_found:
            years = [int(year) for year in years_found]
            if len(years) == 1:
                # Один год
                analysis["min_year"] = years[0]
                analysis["max_year"] = years[0]
                print(f"📅 Найден конкретный год: {years[0]}")
            elif len(years) == 2:
                # Диапазон годов
                analysis["min_year"] = min(years)
                analysis["max_year"] = max(years)
                print(f"📅 Найден диапазон годов: {min(years)}-{max(years)}")
        
        # 2. Поиск периодов по ключевым словам (если конкретные годы не найдены)
        elif not analysis["min_year"]:
            if any(word in user_lower for word in ["старый", "ретро", "советск", "90-х", "80-х", "старую", "старая", "классик", "советские"]):
                analysis["min_year"] = 1950
                analysis["max_year"] = 2000
                print("📅 Распознан период: старые фильмы (1950-2000)")
            
            elif any(word in user_lower for word in ["новый", "свежий", "последний", "2023", "2024", "современный", "недавний", "актуальный"]):
                analysis["min_year"] = 2020
                analysis["max_year"] = current_year
                print("📅 Распознан период: новые фильмы (2020-2024)")
            
            elif any(word in user_lower for word in ["2000-х", "двухтысяч", "2000-е", "нулевые"]):
                analysis["min_year"] = 2000
                analysis["max_year"] = 2009
                print("📅 Распознан период: 2000-е годы")
            
            elif any(word in user_lower for word in ["2010-х", "десятые", "2010-е"]):
                analysis["min_year"] = 2010
                analysis["max_year"] = 2019
                print("📅 Распознан период: 2010-е годы")
            
            elif any(word in user_lower for word in ["нестарый", "средний", "не очень старый", "не древний"]):
                analysis["min_year"] = 2001
                analysis["max_year"] = 2019
                print("📅 Распознан период: нестарые фильмы (2001-2019)")
            
            # Поиск диапазонов типа "2010-2015"
            range_pattern = r'(\d{4})-(\d{4})'
            range_match = re.search(range_pattern, user_message)
            if range_match:
                start_year = int(range_match.group(1))
                end_year = int(range_match.group(2))
                analysis["min_year"] = start_year
                analysis["max_year"] = end_year
                print(f"📅 Найден диапазон: {start_year}-{end_year}")
                
        return analysis
    
    def search_with_ai(self, user_message: str) -> Dict[str, Any]:
        """
        Полный цикл: анализ запроса + поиск в БД
        """
        print(f"\n🎯 Пользователь запросил: '{user_message}'")
        
        # 1. Анализируем запрос
        analysis = self.analyze_user_request(user_message)
        print(f"📊 AI анализ: {analysis}")
        
        movies = []
        
        # 2. ПРИОРИТЕТ: Если запрос о конкретном годе - используем специальный поиск
        if analysis["min_year"] and analysis["max_year"] and analysis["min_year"] == analysis["max_year"]:
            print(f"🎯 Запрос о конкретном годе: {analysis['min_year']}")
            movies = search_by_year({
                "year": analysis["min_year"],
                "limit": 8
            })
        
        # 3. Если не нашли по году или это диапазон годов - ищем по жанрам с фильтрами
        if not movies and analysis["genres"]:
            filters = {
                "genre": analysis["genres"][0],
                "limit": 6
            }
            
            # Добавляем фильтры по году если есть
            if analysis["min_year"]:
                filters["min_year"] = analysis["min_year"]
            if analysis["max_year"]:
                filters["max_year"] = analysis["max_year"]
                
            movies = search_movies(filters)
        
        # 4. Если по жанрам ничего не нашли, ищем по ключевым словам
        if not movies and analysis["keywords"]:
            print(f"🔍 Ищем по ключевым словам: {analysis['keywords']}")
            keyword_filters = {
                "keywords": analysis["keywords"], 
                "limit": 6
            }
            # Добавляем фильтры по году если есть
            if analysis["min_year"]:
                keyword_filters["min_year"] = analysis["min_year"]
            if analysis["max_year"]:
                keyword_filters["max_year"] = analysis["max_year"]
                
            keyword_movies = search_by_keywords(keyword_filters)
            movies.extend(keyword_movies)
        
        # 5. Форматируем ответ
        response_text = self._format_simple_response(user_message, movies, analysis)
        
        return {
            "analysis": analysis,
            "movies": movies,
            "response": response_text
        }
    
    def _format_simple_response(self, user_message: str, movies: list, analysis: dict) -> str:
        """Простое форматирование ответа с ссылками на фильмы"""
        
        if not movies:
            error_msg = f"😔 Не нашел подходящих фильмов по запросу \"{user_message}\"\n\n"
            
            if analysis.get("min_year") and analysis.get("max_year"):
                if analysis["min_year"] == analysis["max_year"]:
                    error_msg += f"В базе нет фильмов {analysis['min_year']} года.\n"
                else:
                    error_msg += f"В базе нет фильмов с {analysis['min_year']} по {analysis['max_year']} год.\n"
            
            if analysis.get("genres"):
                error_msg += f"Попробуйте другие жанры или годы.\n"
            else:
                error_msg += "Попробуйте указать жанр (комедия, драма, боевик) или год.\n"
                
            error_msg += "\nПримеры запросов:\n• \"Комедии 2020 года\"\n• \"Новые боевики\"\n• \"Старые драмы\"\n• \"Фильмы 2000-х\""
            
            return error_msg
        
        # Форматируем успешный ответ
        if analysis.get("min_year") and analysis.get("max_year"):
            if analysis["min_year"] == analysis["max_year"]:
                year_info = f" за {analysis['min_year']} год"
            else:
                year_info = f" с {analysis['min_year']} по {analysis['max_year']} год"
        else:
            year_info = ""
            
        response = f"🎬 Вот что я нашел для вас по запросу \"{user_message}\"{year_info}:\n\n"
        
        for i, movie in enumerate(movies, 1):
            response += f"{i}. **{movie['title']}**"
            if movie.get('year') and movie['year'] <= 2024:  # Показываем только реальные года
                response += f" ({movie['year']})"
            response += "\n"
            
            # Добавляем ссылку на фильм, если она есть в базе
            if movie.get('url'):
                response += f"   🔗 [Смотреть фильм]({movie['url']})\n"
            
            if movie.get('genres'):
                response += f"   🎭 {movie['genres']}\n"
            if movie.get('description'):
                desc = movie['description']
                if len(desc) > 100:
                    desc = desc[:100] + "..."
                response += f"   📖 {desc}\n"
            response += "\n"
        
        response += "🎉 Приятного просмотра! Если хотите другие фильмы - просто спросите!"
        
        return response

# Тестирование
if __name__ == "__main__":
    ai = AIService()
    
    test_queries = [
        "Хочу посмотреть фильмы 2021 года",
        "Комедии 2020 года",
        "Старые советские комедии",
        "Новые драмы", 
        "Фильмы 2000-х годов",
        "Боевики 2015-2020",
        "Нестарые триллеры",
        "Современная фантастика",
        "Ужасы 90-х",
        "Драмы 2010-х"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🧪 Тестируем: '{query}'")
        result = ai.search_with_ai(query)
        print(f"💬 Ответ:\n{result['response']}")
        print(f"📊 Найдено фильмов: {len(result['movies'])}")