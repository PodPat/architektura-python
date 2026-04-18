# Podsumowanie Projektu: World Dashboard

## 📌 Założenia Projektowe i Architektura
Projekt to aplikacja agregująca, przetwarzająca i wyświetlająca informacje ze świata.
- **Architektura:** Mikroserwisy (rozdzielenie backendu od frontendu, komunikacja po HTTP/CORS).
- **Backend:** FastAPI (Python) - udostępnia własne REST API.
- **Frontend:** Plotly Dash.
- **Baza Danych:** SQLite + ORM (SQLAlchemy).
- **Źródło Danych:** API GDELT Project (DOC API, format JSON).
- **Komponent AI:** Integracja z modelem GenAI (LLM) po stronie backendu do generowania analitycznych podsumowań artykułów.
- **Wymóg akademicki:** Wykorzystanie wzorców i struktur z materiałów z folderu `labs`.

## 🔄 Przepływ Danych (Jak to będzie działać w praktyce?)
System został zaprojektowany jako potok analityczny (Data Pipeline). Całość procesu dzieli się na następujące etapy:

1. **Pobieranie Danych (Ingestion):** 
   Nasz backend (FastAPI) komunikuje się z publicznym API GDELT, pytając o najnowsze doniesienia. Zwrócony stamtąd surowy JSON jest mapowany na obiekty Pydantic i poddawany wstępnej walidacji.
2. **Składowanie Danych (Storage):** 
   Wykorzystując ORM (SQLAlchemy) oraz stworzoną przez nas Fabrykę Sesji, backend zapisuje podstawowe informacje o artykułach (tytuł, link, data) w lokalnej bazie SQLite.
3. **Analiza GenAI (Processing):** 
   Backend przesyła zebrane informacje do modelu językowego (LLM) za pośrednictwem API, prosząc o wygenerowanie inteligentnego podsumowania analitycznego. Zwrócony przez model wynik jest następnie aktualizowany w naszej bazie SQLite.
4. **Udostępnianie Danych (API Layer):** 
   FastAPI wystawia gotowe, bezpieczne endpointy (np. `GET /api/v1/news`), które zwracają wzbogacone przez sztuczną inteligencję dane w czystym formacie JSON.
5. **Wizualizacja (Frontend):** 
   Aplikacja interfejsu (Plotly Dash), stanowiąca niezależny mikroserwis, nie łączy się bezpośrednio z bazą SQLite. Zamiast tego uderza po protokole HTTP do naszego backendu FastAPI (przy odpowiednio skonfigurowanym mechanizmie CORS), pobiera przygotowany JSON i na jego podstawie "rysuje" dla użytkownika interaktywny "World Dashboard" – mapy, wykresy i feed informacyjny.

Poniżej znajduje się zestawienie prac wykonanych podczas dzisiejszej sesji oraz plan działania na nasze kolejne spotkanie. Ten dokument pomoże Ci płynnie wznowić pracę.

## 🏆 Osiągnięcia z dzisiejszej sesji

Zbudowaliśmy solidny, zgodny z dobrymi praktykami architektonicznymi fundament pod mikroserwis backendowy.

1. **Izolacja Środowiska (`venv`)**
   - Rozwiązaliśmy problemy z systemowym modułem `python3-venv` na Linuksie.
   - Skonfigurowaliśmy czyste, hermetyczne środowisko.
   - Ustrukturyzowaliśmy zależności w `requirements.txt`.

2. **Zarządzanie Konfiguracją (Wzorzec *Configuration Object*)**
   - Zabezpieczyliśmy projekt plikiem `.gitignore`.
   - Zdefiniowaliśmy zmienne środowiskowe w ukrytym pliku `.env`.
   - Wdrożyliśmy w pliku `config.py` klasę walidującą konfigurację za pomocą `pydantic-settings` (wzorzec Singleton).

3. **Punkt Wejściowy API (`main.py`)**
   - Zainicjalizowaliśmy instancję serwera FastAPI.
   - Zaimplementowaliśmy wzorzec **Dekoratora** (znany z Lab 1) do podpięcia ścieżki `/` (tzw. Health Check).
   - Uruchomiliśmy serwer `uvicorn` i zweryfikowaliśmy działanie automatycznie generowanej dokumentacji (Swagger UI).

4. **Warstwa Danych (`database.py`)**
   - Wprowadziliśmy zasadę **Separacji Odpowiedzialności**.
   - Skonfigurowaliśmy połączenie (Engine) z bazą SQLite przy użyciu ORM SQLAlchemy.
   - Zbudowaliśmy generator `get_db()`, który pozwala na **Wstrzykiwanie Zależności (Dependency Injection)** – co rozwiązuje problem zarządzania otwartymi połączeniami do bazy.

---

## 🚀 Instrukcje i Plan na Następną Sesję

Podczas kolejnego spotkania zaczniemy przekształcać nasz szkielet w działającą aplikację pobierającą dane.

### Krok 1: Definicja Modeli Danych (`models.py`)
Przed rozpoczęciem pracy przypomnij sobie materiał o programowaniu zorientowanym obiektowo i klasach.
Zdefiniujemy tabelę (np. `Article`), która będzie przechowywać dane o wiadomościach. Zbudujemy klasę dziedziczącą po `Base` (z pliku `database.py`) określającą takie kolumny jak:
- `id` (klucz główny)
- `title` (tytuł wiadomości z GDELT)
- `url` (link do źródła)
- `llm_summary` (puste pole na przyszłe podsumowanie z GenAI).

### Krok 2: Generowanie Bazy SQLite
Napiszemy krótki skrypt wewnątrz `main.py`, który podczas startu serwera stworzy fizyczny plik bazy danych (`world_dashboard.db`) na podstawie naszych modeli (używając metody `Base.metadata.create_all()`).

### Krok 3: Integracja z API GDELT
Do tego zadania wykorzystamy bibliotekę `requests`. Pamiętaj, aby podejrzeć strukturę JSON zwracaną przez DOC API GDELT.
Zbudujemy osobną funkcję (tzw. Serwis), która wyśle zapytanie HTTP do GDELT (używając zmiennej `settings.gdelt_api_url`), pobierze listę artykułów i zamieni je na czyste obiekty w Pythonie (korzystając z modeli walidacji Pydantic).

### Krok 4: Zapis do Bazy (Operacje CRUD)
Stworzymy endpoint POST (np. `/fetch-news`), który wykorzystując wstrzykniętą sesję z bazy (`Depends(get_db)`), uruchomi usługę pobierania z GDELT i zapisze nowe artykuły prosto do naszej lokalnej bazy SQLite.

Do usłyszenia na następnej sesji! Pamiętaj, aby na samym starcie pamiętać o aktywacji środowiska (`source venv/bin/activate`).
