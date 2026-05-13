### Podsumowanie prac nad projektem World Dashboard (Sesja 13.05.2026)

### 1. Kluczowe funkcjonalności i zmiany
*   **Similarity Clustering (Grupowanie):** Wdrożono moduł `similarity.py` oparty na `sentence-transformers`. System teraz automatycznie wykrywa podobne wiadomości i nadaje im wspólne `cluster_id`, grupując różne źródła wokół tych samych wydarzeń.
*   **Interaktywny Dashboard 2D:** Stworzono frontend jako osobny mikroserwis (port 3000). Wykorzystano bibliotekę **D3.js** do wygenerowania mapy świata, która dynamicznie podświetla kraje z aktywnymi newsami.
*   **Panel Szczegółów i Kategorie:** Dodano funkcjonalność klikania w kraj na mapie. Po kliknięciu użytkownik najpierw wybiera kategorię (np. Polityka, Konflikty), a następnie widzi przefiltrowaną listę artykułów z pełnymi podsumowaniami AI.
*   **Optymalizacja Analizy AI:** Zaktualizowano `llm.py` i `main.py`, aby do modelu przekazywać również **tytuł artykułu**. Znacznie poprawiło to rozpoznawanie lokalizacji (np. poprawne przypisywanie newsów o USA czy Ukrainie, które wcześniej trafiały do "Globalne").

### 2. Stan bazy danych i migracji
*   **Nowe kolumny:** Do tabeli `articles` dodano pola `embedding` (wektor JSON) oraz `cluster_id` (ID grupy).
*   **Naprawa danych:** Skorygowano ręcznie lokalizacje dla artykułów o id 43, 49 i 50, przenosząc je z "Globalne" do właściwych państw na mapie.

### 3. Architektura i komunikacja
*   **Mikroserwisy:** Aplikacja działa teraz w modelu dwuskładnikowym:
    *   **Backend (FastAPI, :8000)** – analiza, baza, API.
    *   **Frontend (HTTP Server, :3000)** – wizualizacja mapy.
*   **CORS:** Dodano middleware do FastAPI, umożliwiając bezpieczną komunikację między różnymi portami localhosta.

### 4. Następne kroki
1.  **Dalsza optymalizacja scrapera:** Rozważenie obsługi większej liczby domen zagranicznych.
2.  **Super-podsumowania:** Możliwość generowania jednego zbiorczego podsumowania dla całego klastra artykułów (zamiast czytać 5 podobnych).
3.  **Deploy:** Przygotowanie skryptu startowego (np. `start.sh`), który uruchomi oba serwisy naraz w tle.

---
**Uruchamianie:**
- Backend: `uvicorn main:app --reload`
- Frontend: `python3 -m http.server 3000`
