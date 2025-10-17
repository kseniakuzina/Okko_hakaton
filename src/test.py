import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_service2 import AIService
from db_client2 import search_movies, search_by_director, search_by_actor, search_by_country, search_by_year, search_by_keywords

def test_ai_analysis():
    """Тестируем анализ запросов AI"""
    print("🧪 ТЕСТИРУЕМ AI АНАЛИЗ ЗАПРОСОВ")
    print("=" * 60)
    
    ai = AIService()
    
    test_queries = [
        "Хочу посмотреть комедии 2020 года",
        "Фильмы Квентина Тарантино",
        "С Леонардо ДиКаприо",
        "Русские комедии",
        "Старые советские фильмы",
        "Новые американские боевики",
        "Драмы 2010-х годов",
        "Французские романтические фильмы",
        "Фильмы с Джонни Деппом 2000-х",
        "Что-то веселое и легкое"
    ]
    
    for query in test_queries:
        print(f"\n🎯 Запрос: '{query}'")
        analysis = ai.analyze_user_request(query)
        print(f"📊 Анализ: {analysis}")
        print(f"🎯 Намерение: {analysis.get('user_intent', 'N/A')}")

def test_database_search():
    """Тестируем поиск в базе данных"""
    print("\n\n🧪 ТЕСТИРУЕМ ПОИСК В БАЗЕ ДАННЫХ")
    print("=" * 60)
    
    # Тест поиска по жанрам
    print("\n1. 🔍 ПОИСК ПО ЖАНРАМ:")
    genres_test = [
        {"genre": "комедия", "limit": 3},
        {"genre": "драма", "limit": 3},
        {"genre": "боевик", "limit": 3}
    ]
    
    for test in genres_test:
        print(f"\n   Жанр: {test['genre']}")
        movies = search_movies(test)
        for i, movie in enumerate(movies, 1):
            print(f"   {i}. {movie['title']} ({movie.get('year', 'N/A')}) - {movie.get('genres', 'N/A')}")
    
    # Тест поиска по режиссерам
    print("\n2. 🎬 ПОИСК ПО РЕЖИССЕРАМ:")
    directors_test = [
        {"director": "Тодд Филлипс", "limit": 3},
        {"director": "Квентин", "limit": 3},
        {"director": "Нолан", "limit": 3}
    ]
    
    for test in directors_test:
        print(f"\n   Режиссер: {test['director']}")
        movies = search_by_director(test)
        for i, movie in enumerate(movies, 1):
            print(f"   {i}. {movie['title']} - {movie.get('directors', 'N/A')}")
    
    # Тест поиска по актерам
    print("\n3. 🌟 ПОИСК ПО АКТЕРАМ:")
    actors_test = [
        {"actor": "Леонардо", "limit": 3},
        {"actor": "Джонни Депп", "limit": 3},
        {"actor": "Райан Гослинг", "limit": 3}
    ]
    
    for test in actors_test:
        print(f"\n   Актер: {test['actor']}")
        movies = search_by_actor(test)
        for i, movie in enumerate(movies, 1):
            print(f"   {i}. {movie['title']} - {movie.get('actors', 'N/A')}")
    
    # Тест поиска по странам
    print("\n4. 🌍 ПОИСК ПО СТРАНАМ:")
    countries_test = [
        {"country": "Россия", "limit": 3},
        {"country": "США", "limit": 3},
        {"country": "Франция", "limit": 3}
    ]
    
    for test in countries_test:
        print(f"\n   Страна: {test['country']}")
        movies = search_by_country(test)
        for i, movie in enumerate(movies, 1):
            print(f"   {i}. {movie['title']} - {movie.get('year', 'N/A')}")
    
    # Тест поиска по году
    print("\n5. 📅 ПОИСК ПО ГОДУ:")
    years_test = [
        {"year": 2020, "limit": 3},
        {"year": 2015, "limit": 3}
    ]
    
    for test in years_test:
        print(f"\n   Год: {test['year']}")
        movies = search_by_year(test)
        for i, movie in enumerate(movies, 1):
            print(f"   {i}. {movie['title']} - {movie.get('genres', 'N/A')}")

def test_full_ai_search():
    """Тестируем полный цикл AI поиска"""
    print("\n\n🧪 ТЕСТИРУЕМ ПОЛНЫЙ ЦИКЛ AI ПОИСКА")
    print("=" * 60)
    
    ai = AIService()
    
    full_test_queries = [
        "Комедии 2020 года",
        "Фильмы Тарантино",
        "Русские комедии с Мироновым",
        "Американские боевики 2010-х",
        "Драмы с Леонардо ДиКаприо",
        "Французские романтические фильмы"
    ]
    
    for query in full_test_queries:
        print(f"\n🎯 Полный поиск: '{query}'")
        result = ai.search_with_ai(query)
        
        print(f"📊 Анализ: {result['analysis']}")
        print(f"🎬 Найдено фильмов: {len(result['movies'])}")
        
        for i, movie in enumerate(result['movies'][:3], 1):  # Показываем первые 3
            print(f"   {i}. {movie['title']} ({movie.get('year', 'N/A')})")
            if movie.get('url'):
                print(f"      🔗 {movie['url']}")
        
        if len(result['movies']) > 3:
            print(f"   ... и еще {len(result['movies']) - 3} фильмов")

def test_specific_queries():
    """Тестируем конкретные проблемные запросы"""
    print("\n\n🔧 ТЕСТИРУЕМ ПРОБЛЕМНЫЕ ЗАПРОСЫ")
    print("=" * 60)
    
    ai = AIService()
    
    problem_queries = [
        "Хочу что-то посмотреть",
        "Фильмы",
        "Кино",
        "Что новенького",
        "Рекомендуй что-нибудь"
    ]
    
    for query in problem_queries:
        print(f"\n❓ Проблемный запрос: '{query}'")
        analysis = ai.analyze_user_request(query)
        print(f"📊 Анализ: {analysis}")
        
        result = ai.search_with_ai(query)
        print(f"🎬 Найдено фильмов: {len(result['movies'])}")

if __name__ == '__main__':
    print("🚀 ЗАПУСК ТЕСТОВОГО СКРИПТА")
    print("=" * 60)
    
    # Запускаем тесты
    test_ai_analysis()
    test_database_search() 
    test_full_ai_search()
    test_specific_queries()
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")