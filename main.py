import sqlite3

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
import requests

DB_PATH = "trips.db"
NPB_API_URL = "https://api.nbp.pl/api/exchangerates/rates/A/{currency}/?format=json/"

app = FastAPI(title= "Trips API")

@app.get("/")
def root():
    return {"message": "Trips API dziala!"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)

@app.get("/health")
def health():
    return {"status": "OK"}

class TripIn(BaseModel):
    destination: str = Field(..., example="Barcelona")
    month:str = Field(..., example = "July")
    price_pln: float = Field(..., ge=0, example=2500.0)

    @validator("destination", "month")
    def not_empty(cls,v):
        if not v or not v.strip():
            raise ValueError("destination cannot be empty")
        return v.strip()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trips ( 
    id INTGER PRIMARY KEY AUTOINCREMENT,
    destination TEXT NOT NULL,
    month TEXT NOT NULL,
    price_pln  REAL NOT NULL)''')
    conn.commit()
    conn.close()

def add_trip_to_db(destination: str, month: str, price_pln: float) -> int:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            'INSERT INTO trips (destination, month, price_pln) VALUES (?, ?, ?, ?)',
            (destination, month, price_pln)
        )
        conn.commit()
        trip_id = c.lastrowid
        conn.close()
        return trip_id
    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))


init_db()

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






