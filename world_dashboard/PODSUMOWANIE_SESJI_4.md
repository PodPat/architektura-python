# Podsumowanie Sesji 4: Optymalizacja, Asynchroniczność i Analiza Wydajności

Poniżej znajduje się podsumowanie zmian, wdrożeń oraz analiz z czwartej sesji tworzenia projektu **World Dashboard**. Backend jest teraz wydajną i wysoce zoptymalizowaną maszyną do masowego mielenia danych.

## 🚀 1. Optymalizacja przepływu danych (Wczesne filtrowanie i Bulk Insert)
Początkowa architektura, choć poprawnie wykorzystywała narzędzia do odfiltrowywania danych przed zapisem, była podatna na olbrzymie straty wydajności. Aplikacja pobierała z GDELT artykuły, odpytywała model Ollama o podsumowanie (zużywając ciężkie zasoby GPU przez kilkadziesiąt sekund) i *dopiero po podsumowaniu* sprawdzała unikalność przed zapisem.
**Wdrożone rozwiązanie:**
- Przepisano mechanikę w `main.py`. Skrypt najpierw zbiera listę URL z surowych artykułów (GDELT), natychmiast pyta bazę SQLite `SELECT ... IN (...)` i dopiero w pełni przefiltrowaną listę *absolutnych nowości* wpuszcza na karty graficzne. Dzięki temu "puste" pobrania kończą się natychmiast (ok. 15 sekund), zamiast zabierać 2 minuty.
- Pojedyncze `db.add()` i `db.commit()` wewnątrz pętli zamieniono na **Zapis Wsadowy** (`db.add_all()`), co drastycznie zredukowało liczbę operacji odczytu/zapisu na dysku.

## ⚡ 2. Transformacja Architektury: Asyncio
Przeniesiono model wielowątkowości (oparty na blokowaniu poprzez systemowe wątki w `ThreadPoolExecutor`) na nowoczesny, natywny model asynchroniczny Pythona.
- Stara biblioteka `requests` ustąpiła miejsca bibliotece **`httpx`**, która umożliwia nieblokujące zapytania sieciowe (`await client.get(...)`).
- Logika modułu `llm.py` została zrefaktoryzowana z użyciem dedykowanego, asynchronicznego klienta `ollama.AsyncClient()`. Wątek główny aplikacji nie jest już wstrzymywany podczas gdy model wylicza wektory macierzy.
- W `main.py` wprowadzono instrukcję `await asyncio.gather(*tasks)`, aby wystrzeliwać wszystkie pobrania i zapytania LLM jednocześnie w ramach zwinnej pętli zdarzeń.
- Zaadaptowano Background Schedulera używając `AsyncIOScheduler` tak, aby zadania automatyczne nie łamały logiki asynchronicznej.

## 🛠️ 3. Fixy i Troubleshooting
Podczas testów nowej asynchronicznej struktury wykryto i naprawiono kilka ukrytych pułapek sieciowych:
- **Przekierowania scrapera:** Biblioteka `httpx` (w przeciwieństwie do `requests`) domyślnie blokuje podążanie za przekierowaniami. Skutkowało to zwracaniem pustych stron (Błąd 301/302 HTTP) do modelu i fałszywymi rekordami w bazie ("Brak tekstu do podsumowania"). Zabezpieczono klienta flagą `follow_redirects=True`.
- **Obsługa API Rate Limits:** Skrypt ulegał awarii krytycznej przy częstym ręcznym testowaniu endpointu. Dodano przechwytywanie wyjątków `httpx.HTTPError` dla 429 Too Many Requests, przez co serwer łagodnie loguje problem i po prostu przerywa potok, zachowując stabilność.

## 📊 4. Analiza Wydajności (Dynamic Batching Ollamy)
Wykorzystano autorski dekorator pomiaru czasu `@measure_execution_time` do prześledzenia logów aplikacji przy limicie pobierania z GDELT równym `10` artykułom. 
Wykazało to perfekcyjne działanie wskaźnika GPU `OLLAMA_NUM_PARALLEL=4`. 
Czas trwania procesów pokazał wyraźne pogrupowanie:
- **Grupa I (Artykuły 1-4):** Wystartowała od razu, zrzuciła podsumowania po ok. ~93 do 132 sekundy.
- **Grupa II (Artykuły 5-8):** Zaczekała na zwolnienie VRAM i oddała wynik w przedziale 150-220 sekund.
- **Grupa III (Ostatnie 2 artykuły):** Zakończyły zmagania w ok. 240 sekundy.
Łączny czas operacji zajął równe 4,5 minuty. Potwierdzono, że Python nie jest już wąskim gardłem – kod zrównolegla pracę idealnie, a ogranicznikiem jest w tym momencie tylko pamięć karty graficznej i rozmiar użytego modelu (np. 9B `gemma2`).

## ⏭️ Co dalej?
Po wdrożeniu tych mechanizmów nasz Back-End stanowi gotowe, niewrażliwe na błędy, w 100% zautomatyzowane ramię pobierające dane dla usługi.
Projekt może bezpiecznie płynąć w stronę Frontendu, czyli czytania naszej potężnej bazy SQLite za pomocą interfejsu w **Plotly Dash**.
