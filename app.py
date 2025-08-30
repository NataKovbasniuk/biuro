
import sqlite3
import re
import requests
from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, Field, constr

DB_PATH = "travel.db"
NBP_URL = "https://api.nbp.pl/api/exchangerates/rates/A/{code}/?format=json"
CURRENCY_REGEX = re.compile(r"^[A-Z]{3}$")


class DatabaseError(Exception):
    """Błąd bazy danych"""

class CurrencyError(Exception):
    """Błąd waluty lub API NBP"""

def get_conn() -> sqlite3.Connection:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
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
        raise CurrencyError("NBP: nieoczekiwany format odpowiedzi") from e

def convert_pln_to(amount_pln: float, currency: str) -> float:
    if amount_pln < 0:
        raise CurrencyError("Kwota w PLN nie może być ujemna")
    rate = fetch_rate_nbp(currency)
    converted = Decimal(str(amount_pln)) / Decimal(str(rate))
    return float(converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


app = FastAPI(
    title="Biuro Podróży API",
    version="1.0.0",
    description="Proste API do zarządzania ofertami podróży (SQLite + NBP)"
)


@app.on_event("startup")
def _startup():
    try:
        init_db()
    except DatabaseError as e:

        print(f"[startup] DB init failed: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


NonEmptyStr = constr(min_length=1, strip_whitespace=True)

class TripIn(BaseModel):
    destination: NonEmptyStr = Field(..., description="Miejsce podróży, np. 'Rzym'")
    month: NonEmptyStr = Field(..., description="Miesiąc, np. '2025-07' albo 'lipiec'")
    price_pln: float = Field(..., ge=0, description="Cena w PLN (>= 0)")

class TripOut(BaseModel):
    id: int
    destination: str
    month: str
    price: float
    currency: str

def _rows_to_out(rows: List[Dict[str, Any]], currency: str) -> List[TripOut]:
    target = (currency or "PLN").strip().upper()
    out: List[TripOut] = []
    for r in rows:
        base = float(r["price_pln"])
        price = base if target == "PLN" else convert_pln_to(base, target)
        out.append(TripOut(
            id=int(r["id"]),
            destination=r["destination"],
            month=r["month"],
            price=price,
            currency=target
        ))
    return out


@app.post("/trips", response_model=TripOut, status_code=201)
def create_trip(payload: TripIn):
    try:
        new_id = add_trip(payload.destination, payload.month, payload.price_pln)

        return TripOut(
            id=new_id,
            destination=payload.destination,
            month=payload.month,
            price=float(payload.price_pln),
            currency="PLN"
        )
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/trips", response_model=List[TripOut])
def get_trips(currency: Optional[str] = Query(None, description="Waluta docelowa (np. EUR, USD). Domyślnie PLN")):
    try:
        rows = get_all_trips()
        return _rows_to_out(rows, currency or "PLN")
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CurrencyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/trips/{destination}", response_model=List[TripOut])
def get_trips_by_dest(
    destination: str = Path(..., description="Kierunek podróży, np. 'Rzym'"),
    currency: Optional[str] = Query(None, description="Waluta docelowa (np. EUR, USD). Domyślnie PLN")
):
    try:
        rows = get_trips_by_destination(destination)
        return _rows_to_out(rows, currency or "PLN")
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CurrencyError as e:
        raise HTTPException(status_code=400, detail=str(e))


