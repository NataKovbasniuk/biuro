import os
import sqlite3
from typing import List, Dict, Any

DB_PATH = "travel.db"

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # <-- ВАЖЛИВО: рядки як словники
    return conn

def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                destination TEXT NOT NULL,
                month TEXT NOT NULL,
                price_pln REAL NOT NULL CHECK(price_pln >= 0)
            );
        """)
        conn.commit()

def add_trip(destination: str, month: str, price_pln: float) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO trips(destination, month, price_pln) VALUES (?, ?, ?);",
            (destination, month, price_pln),
        )
        conn.commit()
        return cur.lastrowid

def get_all_trips() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, destination, month, price_pln FROM trips ORDER BY id;"
        ).fetchall()
        return [dict(r) for r in rows]

def get_trips_by_destination(destination: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, destination, month, price_pln FROM trips "
            "WHERE destination = ? COLLATE NOCASE ORDER BY id;",
            (destination,),
        ).fetchall()
        return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
    if not get_all_trips():
        add_trip("Warszawa", "maj", 1200.0)
        add_trip("Gdańsk", "lipiec", 950.0)
        add_trip("warszawa", "sierpień", 1300.0)

    print("Wszystkie:", get_all_trips())
    print("Warszawa (case-insensitive):", get_trips_by_destination("WARSZAWA"))
