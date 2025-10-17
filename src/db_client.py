import psycopg2
from typing import List, Dict, Any

DB_CONFIG = {
    "host": "109.73.203.167",
    "port": 5432,
    "database": "default_db",
    "user": "vibethon",
    "password": "wCjP24a7&*N8"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def search_movies(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Исправленная функция поиска с правильными названиями колонок
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Основной запрос с JOIN для получения жанров - ИСПРАВЛЕНО: g.name вместо g.genre_name
        query = """
            SELECT 
                t.title_id,
                t.serial_name as title,
                t.description,
                t.release_date,
                t.age_rating,
                STRING_AGG(g.name, ', ') as genres,
                t.url,
                t.content_type
            FROM title t
            LEFT JOIN title_genre tg ON t.title_id = tg.title_id
            LEFT JOIN genre g ON tg.genre_id = g.genre_id
            WHERE 1=1
        """
        params = []
        group_by = " GROUP BY t.title_id, t.serial_name, t.description, t.release_date, t.age_rating, t.url, t.content_type"

        # Фильтр по жанру
        if filters.get("genre"):
            query += " AND g.name ILIKE %s"
            params.append(f"%{filters['genre']}%")

        # Фильтр по типу контента
        if filters.get("content_type"):
            query += " AND t.content_type = %s"
            params.append(filters["content_type"])

        # Ограничение количества
        limit = min(filters.get("limit", 5), 20)
        query += group_by + f" LIMIT {limit}"

        print(f"🔍 Выполняем запрос: {query}")
        print(f"🔍 Параметры: {params}")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Преобразуем в список словарей
        columns = ["id", "title", "description", "release_date", "age_rating", "genres", "url", "content_type"]
        results = [dict(zip(columns, row)) for row in rows]
        
        print(f"✅ Найдено {len(results)} результатов")
        return results

    except Exception as e:
        print(f"❌ Ошибка в search_movies: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def test_db_connection():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("✅ Подключение к БД успешно!")
        
        # Тестируем поиск с разными жанрами
        test_genres = ["драма", "комедия", "боевик"]
        for genre in test_genres:
            print(f"\n🔍 Тестируем поиск жанра: {genre}")
            test_filters = {"genre": genre, "limit": 2}
            results = search_movies(test_filters)
            print(f"Найдено фильмов: {len(results)}")
            for film in results:
                print(f"  - {film['title']} | {film['genres']}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False
    
def get_all_genres():
    """Получаем все доступные жанры из БД"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT name FROM genre ORDER BY name")
        genres = [row[0] for row in cursor.fetchall()]
        
        print(f"📚 Доступные жанры в БД: {genres}")
        return genres
        
    except Exception as e:
        print(f"❌ Ошибка при получении жанров: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def search_movies_by_keywords(user_message: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Умный поиск по ключевым словам из сообщения пользователя"""
    message_lower = user_message.lower()
    
    # Сопоставление ключевых слов с жанрами
    keyword_to_genre = {
        'комедия': 'комедия',
        'смех': 'комедия', 
        'весел': 'комедия',
        'юмор': 'комедия',
        'драма': 'драма',
        'грустн': 'драма',
        'печал': 'драма',
        'боевик': 'боевик',
        'экшн': 'боевик',
        'action': 'боевик',
        'стрельб': 'боевик',
        'фантастика': 'фантастика',
        'космос': 'фантастика',
        'будущ': 'фантастика',
        'научн': 'фантастика',
        'ужас': 'ужасы',
        'хоррор': 'ужасы',
        'страшн': 'ужасы',
        'триллер': 'триллер',
        'детектив': 'детектив',
        'мистик': 'мистика',
        'приключен': 'приключения',
        'роман': 'мелодрама',
        'любов': 'мелодрама'
    }
    
    # Ищем подходящий жанр
    for keyword, genre in keyword_to_genre.items():
        if keyword in message_lower:
            return search_movies({"genre": genre, "limit": limit})
    
    # Если не нашли по ключевым словам, возвращаем популярные фильмы
    return search_movies({"limit": limit})