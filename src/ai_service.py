import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from db_client import search_movies, search_by_keywords

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
        Пользователь пишет на русском языке. Твоя задача - извлечь жанры и годы из запроса.

        Верни ответ в формате JSON:
        {
            "genres": ["список жанров из запроса"],
            "keywords": "ключевые слова для поиска в описании",
            "min_year": минимальный год (если есть),
            "max_year": максимальный год (если есть)
        }

        Жанры которые есть в базе: комедия, драма, боевик, фантастика, ужасы, триллер, мелодрама, приключения, детектив, фэнтези, криминал, семейный

        Примеры:
        - "Хочу посмотреть старую комедию" -> {"genres": ["комедия"], "keywords": "комедия", "min_year": 1950, "max_year": 2000}
        - "Грустная драма про любовь" -> {"genres": ["драма", "мелодрама"], "keywords": "любовь", "min_year": null, "max_year": null}
        - "Что-то веселое на вечер" -> {"genres": ["комедия"], "keywords": "веселый", "min_year": null, "max_year": null}
        - "Современный боевик" -> {"genres": ["боевик"], "keywords": "боевик", "min_year": 2020, "max_year": 2024}
        """

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/llama-3.1-8b-instruct:free",  # РАБОТАЮЩАЯ МОДЕЛЬ
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
                # Добавляем поля для обратной совместимости
                analysis["user_intent"] = f"поиск {', '.join(analysis.get('genres', []))}"
                analysis["mood"] = ""
                
                return analysis
            else:
                print(f"❌ Ошибка OpenRouter: {response.status_code} - {response.text}")
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
            "комедия": ["комедия", "смех", "юмор", "весел", "приключен", "смешн", "веселое"],
            "драма": ["драма", "грустн", "печал", "эмоци", "чувств", "трогательн", "грустное"],
            "боевик": ["боевик", "экшн", "action", "стрельба", "погон", "битва", "экшен"],
            "фантастика": ["фантастика", "космос", "будущ", "научн", "sci-fi", "фэнтези"],
            "ужасы": ["ужас", "хоррор", "страш", "мистик", "жутк"],
            "мелодрама": ["мелодрама", "роман", "любов", "отношен", "чувств", "романтик"],
            "триллер": ["триллер", "напряжен", "саспенс", "детектив"],
            "приключения": ["приключен", "путешеств", "экспедиц", "исследова"]
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                analysis["genres"].append(genre)
        
        # Анализ года
        if any(word in user_lower for word in ["старый", "ретро", "советск", "90-х", "80-х", "старую", "старая"]):
            analysis["min_year"] = 1950
            analysis["max_year"] = 2000
        elif any(word in user_lower for word in ["новый", "свежий", "последний", "2020", "2023", "2024", "современный"]):
            analysis["min_year"] = 2020
            analysis["max_year"] = 2024
            
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
        
        # 2. Если нашли жанры - ищем по жанрам
        if analysis["genres"]:
            filters = {
                "genre": analysis["genres"][0],  # Берем первый жанр
                "limit": 4
            }
            
            # Добавляем фильтры по году если есть
            if analysis["min_year"]:
                filters["min_year"] = analysis["min_year"]
            if analysis["max_year"]:
                filters["max_year"] = analysis["max_year"]
                
            movies = search_movies(filters)
        
        # 3. Если по жанрам ничего не нашли, ищем по ключевым словам
        if not movies and analysis["keywords"]:
            print(f"🔍 Ищем по ключевым словам: {analysis['keywords']}")
            keyword_movies = search_by_keywords({
                "keywords": analysis["keywords"], 
                "limit": 4
            })
            movies.extend(keyword_movies)
        
        # 4. Форматируем ответ
        response_text = self._format_simple_response(user_message, movies, analysis)
        
        return {
            "analysis": analysis,
            "movies": movies,
            "response": response_text
        }
    
    def _format_simple_response(self, user_message: str, movies: list, analysis: dict) -> str:
        """Простое форматирование ответа"""
        
        if not movies:
            return "😔 Не нашел подходящих фильмов по вашему запросу. Попробуйте другой жанр или описание!"
        
        response = f"🎬 Вот что я нашел для вас по запросу \"{user_message}\":\n\n"
        
        for i, movie in enumerate(movies, 1):
            response += f"{i}. **{movie['title']}**"
            if movie.get('year'):
                response += f" ({movie['year']})"
            response += "\n"
            
            if movie.get('genres'):
                response += f"   🎭 {movie['genres']}\n"
            if movie.get('description'):
                response += f"   📖 {movie['description'][:100]}...\n"
            response += "\n"
        
        response += "🎉 Приятного просмотра! Если хотите другие фильмы - просто спросите!"
        
        return response

# Тестирование
if __name__ == "__main__":
    ai = AIService()
    
    test_queries = [
        "Хочу посмотреть комедию",
        "Грустная драма про любовь",
        "Старый боевик",
        "Что-то веселое на вечер"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"🧪 Тестируем: '{query}'")
        result = ai.search_with_ai(query)
        print(f"💬 Ответ:\n{result['response']}")