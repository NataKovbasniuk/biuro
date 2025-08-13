import os
import sqlite3
from typing import List, Dict, Any
import requests
import re
from decimal import Decimal, ROUND_HALF_UP


DB_PATH = "travel.db"


class DatabaseError(Exception):
    """Błąd bazy danych"""

class CurrencyError(Exception):
    """Błąd waluty lub API NBP"""


def get_conn() -> sqlite3.Connection:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # zwraca wyniki jako słowniki
        return conn
    except sqlite3.Error as e:
        raise DatabaseError(f"Błąd połączenia z bazą: {e}")


def init_db() -> None:
    try:
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
    except sqlite3.Error as e:
        raise DatabaseError(f"Błąd inicjalizacji bazy: {e}")


def add_trip(destination: str, month: str, price_pln: float) -> int:
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO trips(destination, month, price_pln) VALUES (?, ?, ?);",
                (destination, month, price_pln),
            )
            conn.commit()
            return cur.lastrowid
    except sqlite3.Error as e:
        raise DatabaseError(f"Błąd dodawania rekordu: {e}")


def get_all_trips() -> List[Dict[str, Any]]:
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, destination, month, price_pln FROM trips ORDER BY id;"
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        raise DatabaseError(f"Błąd odczytu bazy: {e}")


def get_trips_by_destination(destination: str) -> List[Dict[str, Any]]:
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, destination, month, price_pln FROM trips "
                "WHERE destination = ? COLLATE NOCASE ORDER BY id;",
                (destination,),
            ).fetchall()
            return [dict(r) for r in rows]
    except sqlite3.Error as e:
        raise DatabaseError(f"Błąd odczytu bazy: {e}")


NBP_URL = "https://api.nbp.pl/api/exchangerates/rates/A/{code}/?format=json"
CURRENCY_REGEX = re.compile(r"^[A-Z]{3}$")

def _validate_currency(code: str) -> str:
    code = code.strip().upper()
    if code == "PLN":
        return "PLN"
    if not CURRENCY_REGEX.match(code):
        raise CurrencyError(f"Niepoprawny kod waluty: {code}")
    return code

def fetch_rate_nbp(code: str) -> float:
    code = _validate_currency(code)
    if code == "PLN":
        return 1.0

    try:
        r = requests.get(NBP_URL.format(code=code), timeout=5)
        r.raise_for_status()
    except requests.Timeout:
        raise CurrencyError("Przekroczono czas oczekiwania na odpowiedź NBP")
    except requests.RequestException as e:
        raise CurrencyError(f"Błąd połączenia z API NBP: {e}")

    try:
        data = r.json()
        return float(data["rates"][0]["mid"])
    except (ValueError, KeyError, IndexError) as e:
        raise CurrencyError(f"NBP: nieoczekiwany format odpowiedzi") from e

def convert_pln_to(amount_pln: float, currency: str) -> float:
    if amount_pln < 0:
        raise CurrencyError("Kwota w PLN nie może być ujemna")
    rate = fetch_rate_nbp(currency)
    converted = Decimal(str(amount_pln)) / Decimal(str(rate))
    return float(converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


if __name__ == "__main__":
    init_db()
    if not get_all_trips():
        add_trip("Warszawa", "maj", 1200.0)
        add_trip("Gdańsk", "lipiec", 950.0)
        add_trip("warszawa", "sierpień", 1300.0)

    print("Wszystkie:", get_all_trips())
    print("Warszawa:", get_trips_by_destination("WARSZAWA"))
    print("Kurs EUR:", fetch_rate_nbp("eur"))
    print("100 PLN w EUR:", convert_pln_to(100, "eur"))

