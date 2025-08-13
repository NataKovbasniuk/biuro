from dbm import sqlite3

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

DB_PATH = "trips.db"

app = FastAPI(title= "Trips API")

@app.get("/")
def root():
    return {"message": "Trips API dziala!"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload = True)

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







