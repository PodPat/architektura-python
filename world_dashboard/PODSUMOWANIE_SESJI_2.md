# Podsumowanie Sesji 2: World Dashboard

## 🏆 Osiągnięcia z dzisiejszej sesji

Przekształciliśmy szkielet backendowy w działający potok danych (Data Pipeline), który pobiera prawdziwe informacje ze świata i przechowuje je lokalnie.

### 1. Warstwa Danych — Model SQLAlchemy (`models.py`) ✅
- Zdefiniowaliśmy klasę `Article` dziedziczącą po `Base` (ORM).
- Tabela `articles` zawiera kolumny: `id`, `title`, `url`, `llm_summary`.
- Naprawiliśmy błąd składni: `primary key` → `primary_key` (ważna lekcja: Python nie lubi spacji w nazwach argumentów!).

### 2. Generowanie Bazy Danych (`main.py`) ✅
- Dodaliśmy `models.Base.metadata.create_all(bind=engine)` do `main.py`.
- Podczas startu serwera Uvicorn automatycznie tworzy plik `world_dashboard.db`.

### 3. Schematy Walidacji Pydantic (`schemas.py`) ✅
- Stworzyliśmy modele `GdeltArticle` i `GdeltResponse`.
- Nauczyliśmy się różnicy między **modelami SQLAlchemy** (baza danych) a **modelami Pydantic** (walidacja danych w locie).

### 4. Logika Biznesowa — Serwis GDELT (`services.py`) ✅
- Napisaliśmy funkcję `fetch_latest_news_from_gdelt()` korzystającą z biblioteki `requests`.
- Rozwiązaliśmy problem blokady `429 Too Many Requests` przez dodanie nagłówka `User-Agent` (podszywanie się pod przeglądarkę).
- Zabezpieczyliśmy aplikację blokiem `try...except HTTPError`, dzięki czemu błędy zewnętrznego API nie "wywracają" naszego serwera.

### 5. Endpoint Zapisu (`main.py`) ✅
- Zaimplementowaliśmy `POST /fetch-news` korzystający z **Dependency Injection** (`Depends(get_db)`).
- Endpoint pobiera dane z GDELT → waliduje przez Pydantic → zapisuje do SQLite.
- Zabezpieczenie przed duplikatami: pole `url` ma `unique=True`, a baza zwraca wyjątek, który "łapiemy" przez `db.rollback()`.

### 6. Weryfikacja Danych w Bazie ✅
- Potwierdziliśmy działanie poleceniem:
  ```bash
  sqlite3 world_dashboard.db "SELECT id, title FROM articles;"
  ```

---

## Stan obecnych plików backendu

```
backend/
├── .env                  # Zmienne środowiskowe (DATABASE_URL, GDELT_API_URL)
├── config.py             # Singleton konfiguracji (pydantic-settings)
├── database.py           # Engine, SessionLocal, get_db() — Dependency Injection
├── models.py             # Model SQLAlchemy — tabela "articles"
├── schemas.py            # Modele Pydantic — GdeltArticle, GdeltResponse
├── services.py           # Logika pobierania z GDELT
├── main.py               # Serwer FastAPI — endpointy: GET /, POST /fetch-news
├── world_dashboard.db    # Fizyczna baza SQLite (generowana automatycznie)
└── requirements.txt
```

---

## 🚀 Plan na Sesję 3

### Krok 1: Wzbogacenie Modelu Danych
Dodamy do tabeli `articles` nowe kolumny, aby przechowywać więcej informacji z GDELT:
- `source_country` (kraj wydawcy artykułu — do rysowania na mapie)
- `image_url` (miniatura artykułu — do wyświetlania kart wiadomości)
- `published_date` (data publikacji)

Zaktualizujemy też `schemas.py`, by pobierać te pola z GDELT.

### Krok 2: Integracja z modelem GenAI (LLM)
To główny cel sesji 3 — wypełnienie pola `llm_summary`.
- Zintegrujemy się z API modelu językowego (np. Gemini lub OpenAI).
- Wyślemy tytuł artykułu do modelu z prośbą o wyekstrahowanie:
  - Krótkiego podsumowania (2-3 zdania)
  - Nazwy kraju/miasta, którego dotyczy wydarzenie

### Krok 3: Wielowątkowość z Lab 2 (`concurrent.futures`)
Wywołania API modelu AI są wolne (każde czeka na odpowiedź serwera → **I/O-bound**).
- Zastosujemy wzorzec z **Lab 2** (`ThreadPoolExecutor`), żeby wysyłać wiele zapytań do LLM równolegle.
- Zobaczymy na własne oczy różnicę w czasie działania sekwencyjnego vs. wielowątkowego.

### Krok 4: Endpoint odczytu (`GET /news`)
- Dodamy endpoint zwracający artykuły z bazy jako JSON.
- To będzie "brama" komunikacji z przyszłym Frontendem Plotly Dash.

### Krok 5 (opcjonalnie): Pierwsze testy jednostkowe (Lab 3)
- Napiszemy kilka podstawowych testów `pytest` dla logiki w `services.py`.

---

## Jak zacząć kolejną sesję?

```bash
cd world_dashboard/backend
source venv/bin/activate
uvicorn main:app --reload
```
