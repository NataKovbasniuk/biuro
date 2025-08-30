# 🧳 Biuro Podróży – Proste API (FastAPI + SQLite + NBP)

Proste API do zarządzania ofertami podróży.  
Dane w **SQLite** (`travel.db`). Konwersja walut przez **NBP (tabela A)**.

---

## 0. Sprint 0 – środowisko
- Repo na GitHub + venv ✅  
- Minimalny serwer FastAPI + endpoint `/health` ✅  
- `requirements.txt` działa (pip install) ✅  

---

## 1. Baza danych
- Plik `travel.db` tworzony automatycznie.  
- Tabela `trips` z kolumnami:  
  - `id` (PK, AUTOINCREMENT)  
  - `destination` (TEXT, NOT NULL)  
  - `month` (TEXT, NOT NULL)  
  - `price_pln` (REAL, >=0)  
- Funkcje insert/select działają poprawnie.  

---

## 2. POST /trips
Dodaje nową ofertę.

**Body (JSON)**
~~~json
{ "destination": "Rzym", "month": "2025-07", "price_pln": 1999 }
~~~

**Walidacja**
- `destination` – niepuste  
- `month` – niepuste  
- `price_pln` – `>= 0`  

**Odpowiedzi**
- **201** – utworzony wpis  
- **422** – błędne dane wejściowe  
- **400** – błąd bazy  

---

## 3. GET /trips i GET /trips/{destination}
- `GET /trips` – zwraca wszystkie oferty, sortowane po `id`.  
- `GET /trips/{destination}` – zwraca tylko oferty dla kierunku (case-insensitive).  
- Pusta lista → kod 200 i `[]`.  

---

## 4. Walidacje i obsługa błędów
- Niepoprawne dane wejściowe → **422**  
- Błędy bazy → **400**  
- Błędy NBP → **400**  

---

## 5. Uruchomienie i dokumentacja
### Szybki start
~~~bash
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
~~~

- Healthcheck: `GET http://127.0.0.1:8000/health` → `{"status":"ok"}`  
- Dokumentacja: `http://127.0.0.1:8000/docs`

---

## 6. Przykłady (curl)

**Health**
~~~bash
curl http://127.0.0.1:8000/health
~~~

**Dodanie oferty**
~~~bash
curl -X POST http://127.0.0.1:8000/trips \
 -H "Content-Type: application/json" \
 -d '{"destination":"Rzym","month":"2025-07","price_pln":1999}'
~~~

**Lista wszystkich (PLN)**
~~~bash
curl "http://127.0.0.1:8000/trips"
~~~

**Lista w EUR**
~~~bash
curl "http://127.0.0.1:8000/trips?currency=EUR"
~~~

**Tylko dla kierunku (case-insensitive) + USD**
~~~bash
curl "http://127.0.0.1:8000/trips/rzym?currency=USD"
~~~

**Walidacja (422)**
~~~bash
curl -X POST http://127.0.0.1:8000/trips \
 -H "Content-Type: application/json" \
 -d '{"destination":"", "month":"", "price_pln":-10}'
~~~

---

## 7. Konwersja walut (NBP) — ostatni punkt wymagań
- Źródło kursów: `https://api.nbp.pl/api/exchangerates/rates/A/{CODE}/?format=json`  
- Dla `PLN` kurs = 1.0  
- Kwoty zaokrąglane do 2 miejsc (`ROUND_HALF_UP`)  
- Błędy połączenia/formatu/nieznany kod waluty → **400**  

---

## ⚠️ Znane ograniczenia
- `month` to zwykły tekst (brak walidacji formatu daty).  
- Brak cache kursów NBP (każde zapytanie robi request).  
- SQLite – baza plikowa, nie serwerowa.  
- Jeden plik `app.py` dla prostoty.  

---

## 🛠 Troubleshooting
- **Port 8000 zajęty**
  ~~~bash
  lsof -iTCP:8000 -sTCP:LISTEN -nP
  kill -9 <PID>       # lub
  pkill -f "uvicorn app:app"
  ~~~
- **Przypadkowo uśpiłam serwer (Ctrl+Z)**  
  Wpisz `fg`, potem zakończ serwer `Ctrl+C`, uruchom ponownie `uvicorn app:app --reload`.  
- **422 przy POST** – popraw `destination`, `month` (niepuste), `price_pln >= 0`.  
- **Ostrzeżenie o LibreSSL/urllib3** – nie blokuje działania; najlepiej Python 3.11+.  

---

## 🔀 Git workflow (zrealizowane)
- Dev A: `feature/db-nbp` → PR → merge → usunięcie gałęzi  
- Dev B: `feature/api-readme` → PR → merge → usunięcie gałęzi  
