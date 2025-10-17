# src/db_client.py

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
    Пример: filters = {"genre": "драма", "mood": "грустный", "limit": 5}
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Начало запроса
        query = "SELECT title, genre, description, year, rating FROM movies WHERE 1=1"
        params = []

        # Фильтр по жанру (частичное совпадение)
        if filters.get("genre"):
            query += " AND genre ILIKE %s"
            params.append(f"%{filters['genre']}%")

        # Фильтр по году (если указан)
        if filters.get("max_year"):
            query += " AND year <= %s"
            params.append(filters["max_year"])
        if filters.get("min_year"):
            query += " AND year >= %s"
            params.append(filters["min_year"])

        # Ограничение количества
        limit = min(filters.get("limit", 5), 20)  # не больше 20
        query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Преобразуем в список словарей
        columns = ["title", "genre", "description", "year", "rating"]
        return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        print(f"Ошибка в search_movies: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
