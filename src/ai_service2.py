import os
import json
import requests
import re
from typing import Dict, Any
from dotenv import load_dotenv
from db_client2 import search_movies, search_by_keywords, search_by_year, search_by_director, search_by_country, search_by_actor

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
        Пользователь пишет на русском языке. Твоя задача - извлечь жанры, годы, ключевые слова, режиссеров, актеров и страны из запроса.

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

        5. Извлекай информацию о режиссерах, актерах и странах:
           - "фильмы Квентина Тарантино" → director: "Квентин Тарантино"
           - "с Леонардо ДиКаприо" → actor: "Леонардо ДиКаприо"
           - "французское кино" → country: "Франция"
           - "американские комедии" → country: "США", genres: ["комедия"]

        Верни ответ в формате JSON:
        {
            "genres": ["список жанров из запроса"],
            "keywords": "ключевые слова для поиска в описании",
            "min_year": минимальный год (если есть),
            "max_year": максимальный год (если есть),
            "director": "имя режиссера (если есть)",
            "actor": "имя актера (если есть)", 
            "country": "страна (если есть)"
        }

        Примеры:
        - "Хочу посмотреть фильмы 2021 года" → {"genres": [], "keywords": "фильмы", "min_year": 2021, "max_year": 2021}
        - "Комедии 2020 года" → {"genres": ["комедия"], "keywords": "комедии", "min_year": 2020, "max_year": 2020}
        - "Старые советские комедии" → {"genres": ["комедия"], "keywords": "советские комедии", "min_year": 1950, "max_year": 2000, "country": "СССР"}
        - "Фильмы Квентина Тарантино" → {"genres": [], "keywords": "фильмы", "director": "Квентин Тарантино"}
        - "С Леонардо ДиКаприо" → {"genres": [], "keywords": "", "actor": "Леонардо ДиКаприо"}
        - "Французские драмы" → {"genres": ["драма"], "keywords": "драмы", "country": "Франция"}
        - "Американские комедии 2000-х" → {"genres": ["комедия"], "keywords": "комедии", "min_year": 2000, "max_year": 2009, "country": "США"}
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
                analysis["user_intent"] = self._determine_user_intent(analysis)
                analysis["mood"] = ""
                
                return analysis
            else:
                print(f"❌ Ошибка OpenRouter: {response.status_code}")
                return self._fallback_analysis(user_message)
                
        except Exception as e:
            print(f"❌ Ошибка в analyze_user_request: {e}")
            return self._fallback_analysis(user_message)
    
    def _determine_user_intent(self, analysis: Dict[str, Any]) -> str:
        """Определяет намерение пользователя на основе анализа"""
        intent_parts = []
        
        if analysis.get("genres"):
            intent_parts.append(f"поиск {', '.join(analysis['genres'])}")
        if analysis.get("director"):
            intent_parts.append(f"режиссера {analysis['director']}")
        if analysis.get("actor"):
            intent_parts.append(f"актера {analysis['actor']}")
        if analysis.get("country"):
            intent_parts.append(f"страны {analysis['country']}")
        if analysis.get("min_year") and analysis.get("max_year"):
            if analysis["min_year"] == analysis["max_year"]:
                intent_parts.append(f"{analysis['min_year']} года")
            else:
                intent_parts.append(f"с {analysis['min_year']} по {analysis['max_year']} год")
        
        return " ".join(intent_parts) if intent_parts else "поиск фильма"
    
    def _fallback_analysis(self, user_message: str) -> Dict[str, Any]:
        """Резервный анализ если AI не работает"""
        user_lower = user_message.lower()
        analysis = {
            "genres": [],
            "mood": "",
            "keywords": user_message,
            "min_year": None,
            "max_year": None,
            "director": None,
            "actor": None,
            "country": None,
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
        
        country_keywords = {
            "Россия": ["русск", "россий", "россия", "отечествен", "советск"],
            "США": ["американ", "сша", "голливуд", "usa"],
            "Франция": ["француз", "франция"],
            "Великобритания": ["британ", "англий", "великобритан", "лондон"],
            "Корея": ["корей", "корея", "южная корея"],
            "Япония": ["япон", "япония"],
            "Китай": ["китай", "китайск"],
            "Германия": ["герман", "немец", "германия"],
            "Италия": ["итальян", "италия"],
            "Испания": ["испан", "испания"],
            "Индия": ["индий", "индия", "болливуд"]
        }
        
        # Анализ жанров
        for genre, keywords in genre_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                analysis["genres"].append(genre)
        
        # Анализ стран
        for country, keywords in country_keywords.items():
            if any(keyword in user_lower for keyword in keywords):
                analysis["country"] = country
                break
        
        # Анализ режиссеров и актеров (простой паттерн)
        director_patterns = [
            r'(?:фильмы|кино)\s+([А-Я][а-я]+\s+[А-Я][а-я]+)',
            r'режисс[её]ра?\s+([А-Я][а-я]+\s+[А-Я][а-я]+)',
            r'от\s+([А-Я][а-я]+\s+[А-Я][а-я]+)'
        ]
        
        for pattern in director_patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                analysis["director"] = match.group(1)
                break
        
        # Анализ актеров
        actor_patterns = [
            r'с\s+([А-Я][а-я]+\s+[А-Я][а-я]+)',
            r'акт[её]ра?\s+([А-Я][а-я]+\s+[А-Я][а-я]+)',
            r'в\s+ролях?\s+([А-Я][а-я]+\s+[А-Я][а-я]+)'
        ]
        
        for pattern in actor_patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                analysis["actor"] = match.group(1)
                break

        # УЛУЧШЕННЫЙ АНАЛИЗ ГОДА
        current_year = 2024
        
        # 1. Поиск конкретных годов
        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        years_found = re.findall(year_pattern, user_message)
        
        if years_found:
            years = [int(year) for year in years_found]
            if len(years) == 1:
                analysis["min_year"] = years[0]
                analysis["max_year"] = years[0]
                print(f"📅 Найден конкретный год: {years[0]}")
            elif len(years) == 2:
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
        
        analysis["user_intent"] = self._determine_user_intent(analysis)
        return analysis
    
    def search_with_ai(self, user_message: str) -> Dict[str, Any]:
        """
        Полный цикл: анализ запроса + поиск в БД с расширенными критериями
        """
        print(f"\n🎯 Пользователь запросил: '{user_message}'")
        
        # 1. Анализируем запрос
        analysis = self.analyze_user_request(user_message)
        print(f"📊 AI анализ: {analysis}")
        
        movies = []
        
        # 2. ПРИОРИТЕТ 1: Поиск по режиссеру
        if analysis.get("director"):
            print(f"🎬 Ищем фильмы режиссера: {analysis['director']}")
            director_filters = {"director": analysis["director"], "limit": 6}
            
            # Добавляем фильтры по году если есть
            if analysis["min_year"]:
                director_filters["min_year"] = analysis["min_year"]
            if analysis["max_year"]:
                director_filters["max_year"] = analysis["max_year"]
                
            movies = search_by_director(director_filters)
        
        # 3. ПРИОРИТЕТ 2: Поиск по актеру
        if not movies and analysis.get("actor"):
            print(f"🎭 Ищем фильмы с актером: {analysis['actor']}")
            actor_filters = {"actor": analysis["actor"], "limit": 6}
            
            if analysis["min_year"]:
                actor_filters["min_year"] = analysis["min_year"]
            if analysis["max_year"]:
                actor_filters["max_year"] = analysis["max_year"]
                
            movies = search_by_actor(actor_filters)
        
        # 4. ПРИОРИТЕТ 3: Поиск по стране
        if not movies and analysis.get("country"):
            print(f"🌍 Ищем фильмы страны: {analysis['country']}")
            country_filters = {"country": analysis["country"], "limit": 6}
            
            if analysis["min_year"]:
                country_filters["min_year"] = analysis["min_year"]
            if analysis["max_year"]:
                country_filters["max_year"] = analysis["max_year"]
            if analysis["genres"]:
                country_filters["genre"] = analysis["genres"][0]
                
            movies = search_by_country(country_filters)
        
        # 5. ПРИОРИТЕТ 4: Поиск по конкретному году
        if not movies and analysis["min_year"] and analysis["max_year"] and analysis["min_year"] == analysis["max_year"]:
            print(f"📅 Ищем фильмы {analysis['min_year']} года")
            movies = search_by_year({
                "year": analysis["min_year"],
                "limit": 8
            })
        
        # 6. ПРИОРИТЕТ 5: Поиск по жанрам с фильтрами
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
        
        # 7. ПРИОРИТЕТ 6: Поиск по ключевым словам
        if not movies and analysis["keywords"]:
            print(f"🔍 Ищем по ключевым словам: {analysis['keywords']}")
            keyword_filters = {
                "keywords": analysis["keywords"], 
                "limit": 6
            }
            if analysis["min_year"]:
                keyword_filters["min_year"] = analysis["min_year"]
            if analysis["max_year"]:
                keyword_filters["max_year"] = analysis["max_year"]
                
            keyword_movies = search_by_keywords(keyword_filters)
            movies.extend(keyword_movies)
        
        # 8. Форматируем ответ
        response_text = self._format_simple_response(user_message, movies, analysis)
        
        return {
            "analysis": analysis,
            "movies": movies,
            "response": response_text
        }
    
    def _format_simple_response(self, user_message: str, movies: list, analysis: dict) -> str:
        """Простое форматирование ответа с расширенной информацией"""
        
        if not movies:
            error_msg = f"😔 Не нашел подходящих фильмов по запросу \"{user_message}\"\n\n"
            
            # Детализируем причину
            details = []
            if analysis.get("director"):
                details.append(f"режиссера {analysis['director']}")
            if analysis.get("actor"):
                details.append(f"актера {analysis['actor']}")
            if analysis.get("country"):
                details.append(f"страны {analysis['country']}")
            if analysis.get("genres"):
                details.append(f"жанра {', '.join(analysis['genres'])}")
            if analysis.get("min_year") and analysis.get("max_year"):
                if analysis["min_year"] == analysis["max_year"]:
                    details.append(f"{analysis['min_year']} года")
                else:
                    details.append(f"с {analysis['min_year']} по {analysis['max_year']} год")
            
            if details:
                error_msg += f"По критериям: {', '.join(details)}\n\n"
            
            error_msg += "Попробуйте изменить запрос:\n"
            error_msg += "• Указать другой жанр или год\n"
            error_msg += "• Искать по другому режиссеру или актеру\n"
            error_msg += "• Расширить временной период\n"
            
            return error_msg
        
        # Форматируем успешный ответ
        response = f"🎬 *Результаты поиска:* \"{user_message}\"\n\n"
        
        # Добавляем информацию о критериях поиска
        criteria = []
        if analysis.get("director"):
            criteria.append(f"🎬 *Режиссер:* {analysis['director']}")
        if analysis.get("actor"):
            criteria.append(f"🎭 *Актер:* {analysis['actor']}")
        if analysis.get("country"):
            criteria.append(f"🌍 *Страна:* {analysis['country']}")
        if analysis.get("genres"):
            criteria.append(f"🎭 *Жанр:* {', '.join(analysis['genres'])}")
        if analysis.get("min_year") and analysis.get("max_year"):
            if analysis["min_year"] == analysis["max_year"]:
                criteria.append(f"📅 *Год:* {analysis['min_year']}")
            else:
                criteria.append(f"📅 *Годы:* {analysis['min_year']}-{analysis['max_year']}")
        
        if criteria:
            response += "*Критерии поиска:*\n" + "\n".join(criteria) + "\n\n"
        
        for i, movie in enumerate(movies, 1):
            response += f"*{i}. {movie['title']}*"
            if movie.get('year') and movie['year'] <= 2024:
                response += f" ({movie['year']})"
            response += "\n"
            
            # Добавляем ссылку на фильм
            if movie.get('url'):
                response += f"   ▶️ [Смотреть онлайн]({movie['url']})\n"
            
            # Дополнительная информация
            if movie.get('genres'):
                response += f"   🎭 {movie['genres']}\n"
            if movie.get('directors'):
                response += f"   🎬 Режиссер: {movie['directors']}\n"
            if movie.get('actors'):
                actors = movie['actors']
                if len(actors) > 50:
                    actors = actors[:50] + "..."
                response += f"   👥 Актеры: {actors}\n"
            if movie.get('description'):
                desc = movie['description']
                if len(desc) > 100:
                    desc = desc[:100] + "..."
                response += f"   📖 {desc}\n"
            response += "\n"
        
        response += "💡 *Для поиска других фильмов просто напишите новый запрос!*"
        
        return response