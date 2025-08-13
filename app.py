#app.py
#kod dodany bedzie przez Dev B

# app.py — krok 1: utworzenie bazy i tabeli
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "travel.db")

def init_db() -> None:
    """
    Tworzy plik travel.db (jeśli nie istnieje) i tabelę trips.
    """
    first_time = not os.path.exists(DB_PATH)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trips (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                destination TEXT    NOT NULL,
                month       TEXT    NOT NULL,
                price_pln   REAL    NOT NULL CHECK(price_pln >= 0)
            );
            """
        )
        conn.commit()

    if first_time:
        print("Utworzono plik bazy: travel.db")
    else:
        print("Plik travel.db już istniał — tabela trips została zapewniona.")

if __name__ == "__main__":
    init_db()
