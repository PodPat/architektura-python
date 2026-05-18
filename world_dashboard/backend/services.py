import asyncio
import os
from datetime import datetime
from urllib.parse import urlparse
from google.cloud import bigquery
from schemas import GdeltArticle

def load_sources():
    """
    Dynamicznie wczytuje domeny prasowe z pliku sources.txt.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sources_path = os.path.join(current_dir, "sources.txt")
    
    default_sources = [
        "tvn24.pl", "onet.pl", "wp.pl", "cnn.com", "reuters.com", "bbc.com", "aljazeera.com"
    ]
    
    if not os.path.exists(sources_path):
        print(f"⚠️ Nie znaleziono pliku sources.txt. Używam domyślnych źródeł.")
        return default_sources
        
    try:
        with open(sources_path, "r", encoding="utf-8") as f:
            sources = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    sources.append(line)
            return sources if sources else default_sources
    except Exception as e:
        print(f"⚠️ Błąd podczas wczytywania sources.txt: {e}. Używam domyślnych źródeł.")
        return default_sources

async def fetch_latest_events_from_bigquery():
    """
    Pobiera najnowsze wydarzenia (eventy) z Google BigQuery (tabela gdeltv2.events_partitioned).
    Filtruje zapytanie do ostatnich 24 godzin i konkretnych domen prasowych w celu redukcji kosztów.
    Wybiera tylko kluczowe, szeroko komentowane na świecie wydarzenia (IsRootEvent, NumMentions >= 5)
    i sortuje je według popularności (NumMentions DESC).
    """
    try:
        # Inicjalizacja oficjalnego klienta GCP BigQuery
        client = bigquery.Client()
    except Exception as e:
        print(f"❌ [BigQuery] Błąd inicjalizacji klienta: {e}")
        print("💡 Upewnij się, że masz skonfigurowany projekt GCP w pliku .env (GOOGLE_CLOUD_PROJECT)")
        return []

    # Dynamicznie ładujemy źródła z pliku i budujemy warunek SQL
    sources = load_sources()
    source_filters = " OR ".join([f"SOURCEURL LIKE '%{source}%'" for source in sources])

    # Definiujemy wysoce zoptymalizowane zapytanie SQL filtrujące szum i plotki
    query = f"""
    SELECT 
      GLOBALEVENTID,
      SQLDATE,
      DATEADDED,
      SOURCEURL,
      NumMentions,
      EventCode,
      EventRootCode,
      QuadClass
    FROM `gdelt-bq.gdeltv2.events_partitioned`
    WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
      AND SOURCEURL IS NOT NULL
      AND IsRootEvent = 1       -- Tylko główne, źródłowe wydarzenia (odrzuca szum relacyjny)
      AND NumMentions >= 5      -- Odrzuca marginalne notki (musiało być wspomniane w >= 5 źródłach)
      AND ({source_filters})
    ORDER BY NumMentions DESC   -- Sortujemy od najpopularniejszych, trendujących tematów dnia!
    LIMIT 150                   -- Szeroka sieć: pobieramy TOP 150, z czego odfiltrujemy duplikaty
    """
    
    now = datetime.now().strftime("%H:%M:%S")
    print(f"📡 [{now}] Wysyłam zapytanie do Google BigQuery (ostatnie 24h, TOP events)...")
    
    try:
        # Asynchroniczne odpytanie BigQuery (nieblokujące pętli zdarzeń FastAPI)
        query_job = await asyncio.to_thread(client.query, query)
        results = await asyncio.to_thread(query_job.result)
        
        articles = []
        seen_urls = set()  # Zbiór do śledzenia unikalności w obrębie pobranej paczki!
        
        for row in results:
            url = row.SOURCEURL
            
            # Jeśli ten URL już przetwarzaliśmy w tej paczce, pomiń go!
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Wyciągamy domenę prasową
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace("www.", "")
            
            # Formatujemy seendate (BigQuery zwraca DATEADDED jako int, np. 20260517141500)
            date_str = str(row.DATEADDED)
            if len(date_str) == 14:
                seendate = f"{date_str[:8]}T{date_str[8:]}Z"
            else:
                seendate = date_str
            
            # Tworzymy obiekt GdeltArticle. Tytuł zaktualizujemy podczas pobierania tekstu artykułu!
            articles.append(GdeltArticle(
                title="Brak tytułu", 
                url=url,
                domain=domain,
                seendate=seendate,
                event_code=row.EventCode,
                event_root_code=row.EventRootCode,
                quad_class=row.QuadClass,
                num_mentions=row.NumMentions
            ))
            
        print(f"✅ [{now}] BigQuery zwrócił {len(articles)} UNIKALNYCH, ważnych artykułów prasowych.")
        return articles
        
    except Exception as e:
        print(f"❌ [BigQuery] Błąd podczas wykonywania zapytania: {e}")
        return []
