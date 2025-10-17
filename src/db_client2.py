import psycopg2
from typing import List, Dict, Any
from datetime import datetime

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
    Поиск фильмов по жанрам, годам и другим параметрам
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Сопоставление жанров пользователя с жанрами в БД
        genre_mapping = {
            "комедия": "Комедии",
            "драма": "Драмы", 
            "боевик": "Боевики",
            "триллер": "Триллеры",
            "фантастика": "Фантастика",
            "ужасы": "Ужасы",
            "мелодрама": "Мелодрамы",
            "приключения": "Приключения",
            "детектив": "Детективы",
            "фэнтези": "Фэнтези",
            "криминал": "Криминальное",
            "семейный": "Семейное"
        }

        # Основной запрос
        query = """
        SELECT 
            t.title_id,
            t.serial_name as title,
            t.content_type,
            t.release_date,
            EXTRACT(YEAR FROM t.release_date) as year,
            t.age_rating,
            t.description,
            t.url,
            STRING_AGG(DISTINCT g.name, ', ') as genres,
            STRING_AGG(DISTINCT a.name, ', ') as actors,
            STRING_AGG(DISTINCT d.name, ', ') as directors
        FROM title t
        LEFT JOIN title_genre tg ON t.title_id = tg.title_id
        LEFT JOIN genre g ON tg.genre_id = g.genre_id
        LEFT JOIN title_actor ta ON t.title_id = ta.title_id
        LEFT JOIN actor a ON ta.actor_id = a.actor_id
        LEFT JOIN title_director_item tdi ON t.title_id = tdi.title_id
        LEFT JOIN director_item d ON tdi.director_item_id = d.director_item_id
        WHERE t.content_type = 'Фильм'
        """
        params = []

        # Фильтр по жанру (используем маппинг)
        if filters.get("genre"):
            user_genre = filters["genre"].lower()
            db_genre = genre_mapping.get(user_genre, filters["genre"])
            query += " AND g.name ILIKE %s"
            params.append(f"%{db_genre}%")

        # Фильтр по году выпуска
        if filters.get("min_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) >= %s"
            params.append(filters["min_year"])
        if filters.get("max_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) <= %s"
            params.append(filters["max_year"])

        # Группировка и сортировка
        query += """
        GROUP BY 
            t.title_id, t.serial_name, t.content_type, t.release_date, 
            t.age_rating, t.description, t.url
        ORDER BY t.release_date DESC
        """

        # Ограничение количества
        limit = min(filters.get("limit", 5), 20)
        query += f" LIMIT {limit}"

        print(f"🔍 Выполняем запрос с жанром: {filters.get('genre')} -> {params}")
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Преобразуем в список словарей
        columns = [
            "title_id", "title", "content_type", "release_date", "year", 
            "age_rating", "description", "url", "genres", "actors", "directors"
        ]
        
        movies = []
        for row in rows:
            movie_dict = dict(zip(columns, row))
            if movie_dict["year"]:
                movie_dict["year"] = int(movie_dict["year"])
            movies.append(movie_dict)

        print(f"🎬 Найдено фильмов: {len(movies)}")
        return movies

    except Exception as e:
        print(f"❌ Ошибка в search_movies: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def search_by_director(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Поиск фильмов по режиссеру
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT DISTINCT
            t.title_id,
            t.serial_name as title,
            t.content_type,
            t.release_date,
            EXTRACT(YEAR FROM t.release_date) as year,
            t.age_rating,
            t.description,
            t.url,
            STRING_AGG(DISTINCT g.name, ', ') as genres,
            STRING_AGG(DISTINCT a.name, ', ') as actors,
            STRING_AGG(DISTINCT d.name, ', ') as directors
        FROM title t
        LEFT JOIN title_genre tg ON t.title_id = tg.title_id
        LEFT JOIN genre g ON tg.genre_id = g.genre_id
        LEFT JOIN title_actor ta ON t.title_id = ta.title_id
        LEFT JOIN actor a ON ta.actor_id = a.actor_id
        LEFT JOIN title_director_item tdi ON t.title_id = tdi.title_id
        LEFT JOIN director_item d ON tdi.director_item_id = d.director_item_id
        WHERE t.content_type = 'Фильм'
        AND d.name ILIKE %s
        """
        params = [f"%{filters['director']}%"]

        # Фильтр по году
        if filters.get("min_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) >= %s"
            params.append(filters["min_year"])
        if filters.get("max_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) <= %s"
            params.append(filters["max_year"])

        query += """
        GROUP BY 
            t.title_id, t.serial_name, t.content_type, t.release_date, 
            t.age_rating, t.description, t.url
        ORDER BY t.release_date DESC
        LIMIT %s
        """
        
        limit = min(filters.get("limit", 6), 20)
        params.append(limit)

        print(f"🎬 Ищем фильмы режиссера: {filters['director']}")
        cursor.execute(query, params)
        rows = cursor.fetchall()

        columns = [
            "title_id", "title", "content_type", "release_date", "year", 
            "age_rating", "description", "url", "genres", "actors", "directors"
        ]
        
        movies = []
        for row in rows:
            movie_dict = dict(zip(columns, row))
            if movie_dict["year"]:
                movie_dict["year"] = int(movie_dict["year"])
            movies.append(movie_dict)

        print(f"📽 Найдено фильмов режиссера {filters['director']}: {len(movies)}")
        return movies

    except Exception as e:
        print(f"❌ Ошибка в search_by_director: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def search_by_actor(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Поиск фильмов по актеру
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT DISTINCT
            t.title_id,
            t.serial_name as title,
            t.content_type,
            t.release_date,
            EXTRACT(YEAR FROM t.release_date) as year,
            t.age_rating,
            t.description,
            t.url,
            STRING_AGG(DISTINCT g.name, ', ') as genres,
            STRING_AGG(DISTINCT a.name, ', ') as actors,
            STRING_AGG(DISTINCT d.name, ', ') as directors
        FROM title t
        LEFT JOIN title_genre tg ON t.title_id = tg.title_id
        LEFT JOIN genre g ON tg.genre_id = g.genre_id
        LEFT JOIN title_actor ta ON t.title_id = ta.title_id
        LEFT JOIN actor a ON ta.actor_id = a.actor_id
        LEFT JOIN title_director_item tdi ON t.title_id = tdi.title_id
        LEFT JOIN director_item d ON tdi.director_item_id = d.director_item_id
        WHERE t.content_type = 'Фильм'
        AND a.name ILIKE %s
        """
        params = [f"%{filters['actor']}%"]

        # Фильтр по году
        if filters.get("min_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) >= %s"
            params.append(filters["min_year"])
        if filters.get("max_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) <= %s"
            params.append(filters["max_year"])

        query += """
        GROUP BY 
            t.title_id, t.serial_name, t.content_type, t.release_date, 
            t.age_rating, t.description, t.url
        ORDER BY t.release_date DESC
        LIMIT %s
        """
        
        limit = min(filters.get("limit", 6), 20)
        params.append(limit)

        print(f"🎭 Ищем фильмы с актером: {filters['actor']}")
        cursor.execute(query, params)
        rows = cursor.fetchall()

        columns = [
            "title_id", "title", "content_type", "release_date", "year", 
            "age_rating", "description", "url", "genres", "actors", "directors"
        ]
        
        movies = []
        for row in rows:
            movie_dict = dict(zip(columns, row))
            if movie_dict["year"]:
                movie_dict["year"] = int(movie_dict["year"])
            movies.append(movie_dict)

        print(f"🌟 Найдено фильмов с актером {filters['actor']}: {len(movies)}")
        return movies

    except Exception as e:
        print(f"❌ Ошибка в search_by_actor: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def search_by_country(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Поиск фильмов по стране
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT DISTINCT
            t.title_id,
            t.serial_name as title,
            t.content_type,
            t.release_date,
            EXTRACT(YEAR FROM t.release_date) as year,
            t.age_rating,
            t.description,
            t.url,
            STRING_AGG(DISTINCT g.name, ', ') as genres,
            STRING_AGG(DISTINCT a.name, ', ') as actors,
            STRING_AGG(DISTINCT d.name, ', ') as directors
        FROM title t
        LEFT JOIN title_genre tg ON t.title_id = tg.title_id
        LEFT JOIN genre g ON tg.genre_id = g.genre_id
        LEFT JOIN title_actor ta ON t.title_id = ta.title_id
        LEFT JOIN actor a ON ta.actor_id = a.actor_id
        LEFT JOIN title_director_item tdi ON t.title_id = tdi.title_id
        LEFT JOIN director_item d ON tdi.director_item_id = d.director_item_id
        LEFT JOIN title_country tc ON t.title_id = tc.title_id
        WHERE t.content_type = 'Фильм'
        AND tc.country ILIKE %s
        """
        params = [f"%{filters['country']}%"]

        # Фильтр по году
        if filters.get("min_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) >= %s"
            params.append(filters["min_year"])
        if filters.get("max_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) <= %s"
            params.append(filters["max_year"])

        # Фильтр по жанру если есть
        if filters.get("genre"):
            query += " AND g.name ILIKE %s"
            params.append(f"%{filters['genre']}%")

        query += """
        GROUP BY 
            t.title_id, t.serial_name, t.content_type, t.release_date, 
            t.age_rating, t.description, t.url
        ORDER BY t.release_date DESC
        LIMIT %s
        """
        
        limit = min(filters.get("limit", 6), 20)
        params.append(limit)

        print(f"🌍 Ищем фильмы страны: {filters['country']}")
        cursor.execute(query, params)
        rows = cursor.fetchall()

        columns = [
            "title_id", "title", "content_type", "release_date", "year", 
            "age_rating", "description", "url", "genres", "actors", "directors"
        ]
        
        movies = []
        for row in rows:
            movie_dict = dict(zip(columns, row))
            if movie_dict["year"]:
                movie_dict["year"] = int(movie_dict["year"])
            movies.append(movie_dict)

        print(f"🇺🇳 Найдено фильмов страны {filters['country']}: {len(movies)}")
        return movies

    except Exception as e:
        print(f"❌ Ошибка в search_by_country: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def search_by_keywords(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Поиск по ключевым словам в названии и описании
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT 
            t.title_id,
            t.serial_name as title,
            t.content_type,
            t.release_date,
            EXTRACT(YEAR FROM t.release_date) as year,
            t.age_rating,
            t.description,
            t.url,
            STRING_AGG(DISTINCT g.name, ', ') as genres
        FROM title t
        LEFT JOIN title_genre tg ON t.title_id = tg.title_id
        LEFT JOIN genre g ON tg.genre_id = g.genre_id
        WHERE t.content_type = 'Фильм'
        AND (t.serial_name ILIKE %s OR t.description ILIKE %s)
        """
        
        keywords = filters.get("keywords", "")
        params = [f"%{keywords}%", f"%{keywords}%"]

        # Фильтр по году
        if filters.get("min_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) >= %s"
            params.append(filters["min_year"])
        if filters.get("max_year"):
            query += " AND EXTRACT(YEAR FROM t.release_date) <= %s"
            params.append(filters["max_year"])

        query += """
        GROUP BY t.title_id, t.serial_name, t.content_type, t.release_date, t.age_rating, t.description, t.url
        ORDER BY t.release_date DESC
        LIMIT %s
        """
        
        limit = min(filters.get("limit", 5), 20)
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = ["title_id", "title", "content_type", "release_date", "year", "age_rating", "description", "url", "genres"]
        movies = []
        for row in rows:
            movie_dict = dict(zip(columns, row))
            if movie_dict["year"]:
                movie_dict["year"] = int(movie_dict["year"])
            movies.append(movie_dict)
            
        print(f"🔍 Поиск по ключевым словам '{keywords}': найдено {len(movies)} фильмов")
        return movies
        
    except Exception as e:
        print(f"❌ Ошибка в search_by_keywords: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def search_by_year(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Специальный поиск фильмов по году
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        current_year = datetime.now().year
        query = """
        SELECT 
            t.title_id,
            t.serial_name as title,
            t.content_type,
            t.release_date,
            EXTRACT(YEAR FROM t.release_date) as year,
            t.age_rating,
            t.description,
            t.url,
            STRING_AGG(DISTINCT g.name, ', ') as genres,
            STRING_AGG(DISTINCT a.name, ', ') as actors
        FROM title t
        LEFT JOIN title_genre tg ON t.title_id = tg.title_id
        LEFT JOIN genre g ON tg.genre_id = g.genre_id
        LEFT JOIN title_actor ta ON t.title_id = ta.title_id
        LEFT JOIN actor a ON ta.actor_id = a.actor_id
        WHERE t.content_type = 'Фильм'
        AND t.release_date IS NOT NULL
        AND EXTRACT(YEAR FROM t.release_date) <= %s
        AND EXTRACT(YEAR FROM t.release_date) = %s  -- Конкретный год
        GROUP BY 
            t.title_id, t.serial_name, t.content_type, t.release_date, 
            t.age_rating, t.description, t.url
        ORDER BY t.release_date DESC
        LIMIT %s
        """
        
        target_year = filters["year"]
        limit = filters.get("limit", 8)  # Больше результатов для поиска по году
        
        params = [current_year, target_year, limit]

        print(f"🔍 Поиск по году {target_year}, лимит: {limit}")
        cursor.execute(query, params)
        rows = cursor.fetchall()

        columns = [
            "title_id", "title", "content_type", "release_date", "year", 
            "age_rating", "description", "url", "genres", "actors"
        ]
        
        movies = []
        for row in rows:
            movie_dict = dict(zip(columns, row))
            if movie_dict["year"]:
                movie_dict["year"] = int(movie_dict["year"])
            movies.append(movie_dict)

        print(f"🎬 Найдено фильмов {target_year} года: {len(movies)}")
        return movies

    except Exception as e:
        print(f"❌ Ошибка в search_by_year: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()