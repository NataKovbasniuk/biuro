import os
import sqlite3
from typing import List, Dict, Any

DB_PATH = "travel.db"

def init_db() -> None:
    """Tworzy bazę danych i tabelę trips, jeśli nie istnieje."""
    first_time = not os.path.exists(DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                destination TEXT NOT NULL,
                month TEXT NOT NULL,
                price_pln REAL NOT NULL CHECK(price_pln >= 0)
            );
        """)
        conn.commit()

    if first_time:
        print("Utworzono plik bazy: travel.db")
    else:
        print("Plik travel.db już istnieje – tabela trips została zapewniona.")

def get_conn():
    """Zwraca połączenie do bazy danych."""
    return sqlite3.connect(DB_PATH)

def add_trip(destination: str, month: str, price_pln: float) -> None:
    """Dodaje nową podróż do bazy."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO trips (destination, month, price_pln)
            VALUES (?, ?, ?)
        """, (destination, month, price_pln))
        conn.commit()

def get_all_trips() -> List[Dict[str, Any]]:
    """Zwraca wszystkie podróże."""
    with get_conn() as conn:
        rows = conn.execute("SELECT id, destination, month, price_pln FROM trips").fetchall()
        return [dict(r) for r in rows]

def get_trips_by_destination(destination: str) -> List[Dict[str, Any]]:
    """Zwraca podróże do danego miejsca (bez rozróżniania wielkości liter)."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, destination, month, price_pln FROM trips
            WHERE destination = ? COLLATE NOCASE ORDER BY id
        """, (destination,)).fetchall()
        return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()

    if not get_all_trips():
        add_trip("Warszawa", "maj", 1200.0)
        add_trip("Gdańsk", "lipiec", 950.0)
        add_trip("warszawa", "sierpień", 1300.0)

    print("Wszystkie:", get_all_trips())
    print("Warszawa (case-insensitive):", get_trips_by_destination("WARSZAWA"))
