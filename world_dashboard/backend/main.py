from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import time
from functools import wraps
import asyncio

from config import settings
from database import engine, get_db, SessionLocal
import models
import services
import scraper
import llm
import similarity


# Mapowanie kodów głównych CAMEO (EventRootCode) na przyjazne kategorie dla frontendu
CAMEO_CATEGORIES = {
    "01": "Polityka", "02": "Polityka", "04": "Polityka", "10": "Polityka", "11": "Polityka", "12": "Polityka",
    "03": "Polityka", "05": "Polityka",
    "06": "Gospodarka", "07": "Gospodarka",
    "13": "Konflikty", "14": "Konflikty", "15": "Konflikty", "16": "Konflikty",
    "17": "Konflikty", "18": "Konflikty", "19": "Konflikty", "20": "Konflikty",
    "08": "Inne", "09": "Nauka"
}

MAX_NEW_PER_RUN = 15

async def continuous_fetch_loop():
    """
    Ciągła, reaktywna pętla pobierania danych w tle.
    Jeśli pobrano pełną paczkę (15), szybko przechodzi do kolejnej (10s).
    Jeśli baza jest na bieżąco, przechodzi w tryb czuwania (5 minut).
    """
    print("🔄 [Pętla] Inicjalizacja ciągłej, reaktywnej pętli pobierania...")
    # Odczekujemy chwilę na start serwera uvicorn przed pierwszym pobraniem
    await asyncio.sleep(5)
    
    while True:
        db = SessionLocal()
        sleep_time = 300  # Domyślnie 5 minut czuwania
        try:
            saved_count, remaining_count = await run_fetch_pipeline(db)
            print(f"🔄 [Pętla] Cykl zakończony. Zapisano {saved_count} nowych artykułów.")
            
            # Reaktywne sterowanie czasem uśpienia oparte o faktyczną kolejkę (ignorując odrzucone)
            if remaining_count > 0:
                print(f"🚀 [Pętla] Wykryto więcej oczekujących danych ({remaining_count}). Kolejna porcja za 10 sekund...")
                sleep_time = 10
            else:
                print(f"💤 [Pętla] Wszystkie wiadomości są na bieżąco. Zasypiam na 5 minut...")
                sleep_time = 300
        except Exception as e:
            print(f"❌ [Pętla] Błąd podczas pobierania w tle: {e}")
            sleep_time = 60
        finally:
            db.close()
            
        await asyncio.sleep(sleep_time)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wykonuje się podczas startu serwera
    loop_task = asyncio.create_task(continuous_fetch_loop())
    yield
    # Wykonuje się podczas wyłączania serwera
    loop_task.cancel()
    try:
        await loop_task
    except asyncio.CancelledError:
        pass

models.Base.metadata.create_all(bind=engine)
# Inicjalizacja głównej instancji aplikacji FastAPI
app = FastAPI(
    title="World Dashboard API",
    description="Backend agregujący dane ze świata",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Nawiązanie do Lab 1: Używamy wzorca Dekorator, aby powiązać 
# ścieżkę HTTP (GET "/") z konkretną funkcją Pythona.
@app.get("/")
def health_check():
    """
    Endpoint sprawdzający status działania API.
    """
    return {
        "status": "ok",
        "message": "World Dashboard API działa poprawnie!",
        "gcp_project": settings.google_cloud_project or "Nieskonfigurowany (używa domyślnego GCP)"
    }


def measure_execution_time(func):
    """
    Dekorator mierzący czas wykonania funkcji asynchronicznych.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        print(f"⏱️ [Timer] Funkcja '{func.__name__}' wykonała się w {duration:.2f} sekund.")
        return result
    return wrapper

@measure_execution_time
async def process_article(article_item):
    """
    Funkcja pomocnicza. Działa asynchronicznie.
    Pobiera treść i tytuł artykułu, a następnie odpytuje lokalny model LLM.
    """
    scraped = await scraper.scrape_article(article_item.url)
    article_text = scraped.get("text") or ""
    
    # NOWA ZASADA: Jeśli nie udało się pobrać treści (blokada / paywall), całkowicie odrzucamy artykuł!
    if not article_text.strip():
        print(f"⚠️ Odrzucam newsa: Brak treści z {article_item.domain}")
        return None
    
    # Wybieramy oryginalny tytuł: 1. Pobrany ze strony, 2. Przekazany ze struktury danych, 3. Domyślny
    original_title = scraped.get("title") or article_item.title or "Brak tytułu"
    
    ai_result = await llm.summarize_article(article_text, title=original_title)
    
    # ODRZUCENIE AWARII LLM: Jeśli model gemma2 wyłożył się i zepsuł strukturę JSON, całkowicie odrzucamy artykuł.
    if "błąd dekodowania" in ai_result["summary"].lower() or "zapętlił się" in ai_result["summary"].lower():
        print(f"⚠️ Odrzucam newsa: Model AI zwrócił błąd dla {article_item.url}")
        return None
        
    # Wybieramy tytuł końcowy: preferujemy przetłumaczony przez LLM, w razie braku oryginalny
    final_title = ai_result.get("translated_title") or original_title
    
    # Mapujemy kod CAMEO na kategorię bezpośrednio w backendzie!
    category = CAMEO_CATEGORIES.get(article_item.event_root_code, "Inne")
    
    return {
        "title": final_title,
        "url": article_item.url,
        "domain": article_item.domain,
        "seendate": article_item.seendate,
        "llm_summary": ai_result["summary"],
        "location": ai_result["location"],
        "sentiment": ai_result["sentiment"],
        "category": category,                  # Kategoria z mapowania CAMEO!
        "key_figures": ai_result["key_figures"],
        "event_code": article_item.event_code,
        "event_root_code": article_item.event_root_code,
        "quad_class": article_item.quad_class,
        "num_mentions": article_item.num_mentions
    }


@measure_execution_time
async def run_fetch_pipeline(db: Session):
    """
    Niezależna logika pobierania danych. Używana zarówno przez API jak i Scheduler.
    """
    articles_data = await services.fetch_latest_events_from_bigquery()
    if not articles_data:
        return 0, 0

    # Usunięcie duplikatów URL-i w obrębie samej paczki z BigQuery (zostawiamy te z najwyższym num_mentions)
    seen_urls = {}
    for article in articles_data:
        url = article.url
        if not url:
            continue
        if url not in seen_urls:
            seen_urls[url] = article
        else:
            existing_mock = seen_urls[url]
            if article.num_mentions and existing_mock.num_mentions and article.num_mentions > existing_mock.num_mentions:
                seen_urls[url] = article
    articles_data = list(seen_urls.values())

    # OPTYMALIZACJA 1: Wczesne filtrowanie duplikatów (operacja blokująca, na bazie SQLite)
    incoming_urls = [article.url for article in articles_data]
    existing_articles = db.query(models.Article).filter(models.Article.url.in_(incoming_urls)).all()
    existing_articles_dict = {a.url: a for a in existing_articles}
    
    # FAZA UPDATE: Zaktualizuj NumMentions dla istniejących artykułów (Upsert)
    updated_count = 0
    for article in articles_data:
        if article.url in existing_articles_dict:
            existing = existing_articles_dict[article.url]
            # Jeśli nowe NumMentions z GDELT jest większe, aktualizujemy w bazie!
            if article.num_mentions and existing.num_mentions is not None and article.num_mentions > existing.num_mentions:
                existing.num_mentions = article.num_mentions
                updated_count += 1
                
    if updated_count > 0:
        db.commit()
        print(f"🔄 Zaktualizowano num_mentions dla {updated_count} istniejących artykułów.")
    
    new_articles = [a for a in articles_data if a.url not in existing_articles_dict]
    
    if not new_articles:
        print("Wszystkie pobrane artykuły są już w bazie. Pomijam analizę AI.")
        return 0, 0
        
    total_new = len(new_articles)
    remaining_count = max(0, total_new - MAX_NEW_PER_RUN)

    # OGRANICZENIE WYDAJNOŚCIOWE: Przetwarzaj maksymalnie MAX_NEW_PER_RUN nowych artykułów na jeden cykl!
    if total_new > MAX_NEW_PER_RUN:
        print(f"⚠️ Wykryto {total_new} nowości. Ograniczam przetwarzanie do TOP {MAX_NEW_PER_RUN} dla ochrony wydajności.")
        new_articles = new_articles[:MAX_NEW_PER_RUN]
        
    print(f"Rozpoczynam analizę AI dla {len(new_articles)} nowych artykułów...")
    
    # Asynchroniczne przetwarzanie z limitem współbieżności (semafor) dla pełnego bezpieczeństwa
    sem = asyncio.Semaphore(3)
    async def process_with_semaphore(article):
        async with sem:
            return await process_article(article)
            
    tasks = [process_with_semaphore(article) for article in new_articles]
    results = await asyncio.gather(*tasks)
    
    processed_articles = [res for res in results if res]
                
    # OPTYMALIZACJA 2: Zapis Wsadowy (Bulk Insert)
    db_articles = []
    for data in processed_articles:
        db_articles.append(models.Article(
            title=data["title"],
            url=data["url"],
            domain=data["domain"],
            seendate=data["seendate"],
            llm_summary=data["llm_summary"],
            location=data["location"],
            sentiment=data["sentiment"],
            category=data["category"],
            key_figures=data["key_figures"],
            # ZAPIS NOWYCH PÓL
            event_code=data.get("event_code"),
            event_root_code=data.get("event_root_code"),
            quad_class=data.get("quad_class"),
            num_mentions=data.get("num_mentions", 0)
        ))
        
    if db_articles:
        db.add_all(db_articles)
        try:
            db.commit()
            saved = len(db_articles)
            # Grupowanie po zapisaniu
            print("🔍 Uruchamiam similarity clustering...")
            similarity.assign_clusters(db)
            return saved, remaining_count
        except Exception as e:
            db.rollback()
            print(f"Błąd podczas zapisu do bazy: {e}")
            return 0, remaining_count
            
    return 0, remaining_count


@app.post("/fetch-news")
async def fetch_and_save_news(db: Session = Depends(get_db)):
    """
    Ręczne wywołanie pobierania przez użytkownika API.
    """
    saved_count, remaining_count = await run_fetch_pipeline(db)
    return {
        "status": "ok", 
        "message": f"Zapisano {saved_count} nowych artykułów do bazy! Oczekuje jeszcze: {remaining_count}"
    }


@app.get("/articles/by-location")
def get_articles_by_location(db: Session = Depends(get_db)):
    """
    Zwraca artykuły zgrupowane wg lokalizacji — używane przez frontend mapy.
    """
    articles = db.query(models.Article).all()
    grouped: dict = {}
    for article in articles:
        loc = article.location or "Nieznana"
        if loc not in grouped:
            grouped[loc] = []
        grouped[loc].append({
            "id": article.id,
            "title": article.title,
            "summary": article.llm_summary,
            "sentiment": article.sentiment,
            "category": article.category,
            "url": article.url,
            "cluster_id": article.cluster_id,
            # PRZESYŁAMY DO FRONTENDU
            "event_code": article.event_code,
            "event_root_code": article.event_root_code,
            "quad_class": article.quad_class
        })
    return grouped

@app.get("/articles/top-5")
def get_top_5_articles(db: Session = Depends(get_db)):
    """
    Zwraca 5 najważniejszych wydarzeń globalnych (posortowane malejąco po num_mentions).
    """
    from sqlalchemy import desc
    top_articles = db.query(models.Article).order_by(desc(models.Article.num_mentions)).limit(5).all()
    
    return [
        {
            "id": a.id,
            "title": a.title,
            "summary": a.llm_summary,
            "location": a.location,
            "sentiment": a.sentiment,
            "category": a.category,
            "url": a.url,
            "num_mentions": a.num_mentions,
            "event_root_code": a.event_root_code
        }
        for a in top_articles
    ]
