# Definition of Done (DoD) - World News Dashboard

---

## 1. Izolacja, Konfiguracja i Zarządzanie Środowiskiem
* [ ] **Wirtualne środowisko (`venv`):** Projekt musi być w pełni uruchamialny w odizolowanym środowisku Python. Wszelkie zależności biblioteczne muszą być precyzyjnie opisane w pliku `requirements.txt`.
* [ ] **Konfiguracja konfiguracji (Wzorzec *Configuration Object*):**
  - Wszystkie parametry konfiguracyjne (np. adres bazy danych, URL do BigQuery) muszą być wczytywane z lokalnego, ukrytego pliku `.env`.
  - Klasa `Settings` w `config.py` musi walidować typy zmiennych przy użyciu `pydantic-settings` (wzorzec Singleton).
  - Plik `.env` oraz lokalna baza SQLite muszą być dodane do `.gitignore` i pod żadnym pozorem nie mogą być wersjonowane przez Git.

## 2. Pobieranie i Wczesna Filtracja Danych (GDELT / BigQuery)
* [ ] **Zoptymalizowane ładowanie z GCP:** 
  - Pobieranie danych z publicznego zbioru `gdelt-bq.gdeltv2.events_partitioned` musi filtrować wydarzenia wyłącznie z ostatnich 24 godzin dla zaufanych domen prasowych zdefiniowanych w pliku `sources.txt` (redukcja kosztów GCP).
  - Zapytanie SQL musi eliminować szum informacyjny, pobierając jedynie kluczowe wydarzenia (`IsRootEvent = 1`) o minimalnej liczbie wzmianek (`NumMentions >= 5`).
* [ ] **Wczesna filtracja duplikatów:** 
  - Przed wysłaniem pobranych z GDELT linków do scrapera i modeli LLM, system musi zweryfikować unikalność adresów URL bezpośrednio w bazie SQLite przy użyciu szybkiego zapytania `SELECT IN`.
  - Tylko bezwzględne nowości mogą trafiać do dalszego przetwarzania (ochrona zasobów procesora i GPU przed pustymi przebiegami).
* [ ] **Aktualizacja metryk:** Jeśli pobrany artykuł istnieje już w bazie danych, jego popularność (`num_mentions`) w bazie musi zostać zaktualizowana tylko wtedy, gdy nowa wartość z GDELT jest większa.
* [ ] **Zapis wsadowy:** Zapisywanie przetworzonych artykułów musi odbywać się grupowo za pomocą `db.add_all()` na koniec cyklu pipeline'u w celu minimalizacji liczby wolnych operacji wejścia-wyjścia na dysku.

## 3. Ekstrakcja Tekstu (Scraper)
* [ ] **Pobieranie asynchroniczne:** Scraper musi korzystać z asynchronicznego klienta HTTP (`httpx.AsyncClient`) z parametrem `follow_redirects=True` i nagłówkami symulującymi przeglądarkę.
* [ ] **Analiza struktury strony:** Wyciąganie czystego tekstu oraz oryginalnego tytułu strony musi być realizowane automatycznie przez bibliotekę `newspaper3k` (z ignorowaniem reklam i menu).
* [ ] **Odrzucanie paywalli:** Artykuły, dla których scraper wyciągnie treść o długości poniżej 50 znaków, muszą być odrzucane z dalszego przetwarzania.

## 4. Analiza Językowa i Podsumowania AI (Ollama & Gemma2)
* [ ] **Wydajność asynchroniczna:** Odpytywanie lokalnego modelu Ollama (`gemma2`) musi być realizowane asynchronicznie za pomocą `ollama.AsyncClient()`. Współbieżność potoku musi być kontrolowana przy użyciu semafora ograniczonego do 3 procesów.
* [ ] **Strukturyzowany JSON:** Model LLM musi zwracać odpowiedź w czystym formacie JSON o ściśle zdefiniowanej strukturze:
  - `translated_title`: Tytuł przetłumaczony na język polski w stylu nagłówka prasowego (przy pomocy przekazanego tytułu z nagłówka strony).
  - `summary`: Krótkie podsumowanie bezpośrednie (4-5 zdań w języku polskim).
  - `location`: Przypisane państwo (po polsku) lub "Globalne".
  - `sentiment`: "Pozytywny", "Negatywny" lub "Neutralny".
  - `key_figures`: Rozpoznane postacie lub organizacje powiązane z wydarzeniem.
* [ ] **Przypisanie geograficzne:** Konflikty terytorialne, wojny i napięcia międzynarodowe nie mogą być oznaczane jako "Globalne" — LLM musi przypisać konkretne, powiązane z wydarzeniem państwo.

## 5. Grupowanie Semantyczne (SentenceTransformers)
* [ ] **Generowanie wektorów:** Dla każdego zapisanego artykułu musi zostać wygenerowany wektor embeddingu przy użyciu wielojęzycznego modelu `paraphrase-multilingual-MiniLM-L12-v2` na bazie tytułu i streszczenia. Embedding wektora musi być składowany w bazie jako ciąg znaków JSON.
* [ ] **Klastrowanie kosinusowe:** Artykuły muszą być porównywane i grupowane przy użyciu podobieństwa kosinusowego z progiem `SIMILARITY_THRESHOLD = 0.80`.
* [ ] **Obsługa klastrów:** Artykuły podobne semantycznie muszą współdzielić ten sam `cluster_id`. Na mapie ma być wyświetlany wyłącznie reprezentatywny artykuł z klastra (o najwyższej liczbie wzmianek), a pozostałe chowane pod rozwijaną listą powiązanych źródeł.

## 6. Frontend i Wizualizacja (D3.js World Map)
* [ ] **Separacja mikroserwisowa:** Interfejs użytkownika musi działać jako niezależny mikroserwis (serwowany np. przez wbudowany serwer HTTP Pythona na porcie 3000) komunikujący się z backendem (port 8000) za pośrednictwem CORS.
* [ ] **Interaktywna mapa 2D:** Mapa wygenerowana przy użyciu biblioteki **D3.js** (oraz TopoJSON) musi dynamicznie podświetlać kraje, które posiadają powiązane artykuły w bazie danych.
* [ ] **Dwuetapowy Panel Szczegółów (Region):** Kliknięcie w podświetlone państwo na mapie musi najpierw wygenerować listę dostępnych kategorii (Polityka, Konflikty, Gospodarka itp.) wraz z liczbą artykułów, a dopiero po wyborze kategorii zaprezentować przefiltrowany spis newsów z możliwością rozwijania streszczeń AI.
* [ ] **Zakładka TOP 5:** Interfejs musi oferować panel prezentujący 5 najważniejszych i najbardziej popularnych wydarzeń dnia na świecie na podstawie metryki `num_mentions` z bazy danych.
