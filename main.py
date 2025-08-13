import sqlite3

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
import requests

DB_PATH = "trips.db"
NPB_API_URL = "https://api.nbp.pl/api/exchangerates/rates/A/{currency}/?format=json/"




class TripIn(BaseModel):
    destination: str = Field(..., example="London")
    month: str = Field(..., example="January")
    price_pln: float = Field(..., ge=0, example=2500.0)

    @field_validator("destination", "month")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("destination cannot be empty")
        return v.strip()
class TripOut(BaseModel):
    id: int
    destination: str
    month:str
    price: float
    currency: str


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination TEXT NOT NULL,
        month TEXT NOT NULL,
        price_pln  REAL NOT NULL,)
    ''')
    conn.commit()
    conn.close()

def add_trip_to_db(destination:str, month:str, price_pln:float) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'INSERT INTO trips (destination, month, price_pln) VALUES (?, ?, ?)',
        (destination, month, price_pln)
    )
    conn.commit()
    trip_id = c.lastrowid
    conn.close()
    return trip_id

def get_all_trips():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, destination, month, price_pln FROM trips WHERE destination = ?', (destination,)
              )
    rows = c.fetchall()
    conn.close()
    return rows


def convert_price(price_pln: float, currency: str) -> float:
    if currency.upper() == "PLN":
        return round(price_pln, 2)
    try:
        response = requests.get(NPB_API_URL.format(currency=currency.upper()), timeout=5)
        response.raise_for_status()
        data = response.json()
        rate = data["rates"][0]["mid"]
        return round(price_pln / rate, 2)
    except requests.RequestException:
        raise HTTPException(status_code=400, detail="Request failed")


@app.get("/health")
def health():
    return {"status": "OK"}
@app.post("/trips", status_code=201)
def create_trip(trip: TripIn):
    trip_id = add_trip_to_db(trip.destination, trip.month, trip.price_pln)
    return {"trip_id": trip_id,
            "destination": trip.destination,
            "month": trip.month,
            "price_pln": trip.price_pln
            }
@app.get("/")
def root():
    return {"message": "Trips API dziala!"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)






