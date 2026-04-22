from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time
from functools import wraps
import asyncio

from config import settings
from database import engine, get_db, SessionLocal
import models
import services
import scraper
import llm


async def scheduled_fetch():
    """Funkcja uruchamiana automatycznie w tle. Tworzy własną sesję DB."""
    db = SessionLocal()
    try:
        await run_fetch_pipeline(db)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Wykonuje się podczas startu serwera
    scheduler = AsyncIOScheduler()
    # Uruchamiamy zadanie w tle (np. co 15 minut)
    scheduler.add_job(scheduled_fetch, 'interval', minutes=15)
    scheduler.start()
    yield
    # Wykonuje się podczas wyłączania serwera
    scheduler.shutdown()

models.Base.metadata.create_all(bind=engine)
# Inicjalizacja głównej instancji aplikacji FastAPI
app = FastAPI(
    title="World Dashboard API",
    description="Backend agregujący dane ze świata",
    version="1.0.0",
    lifespan=lifespan
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
        # Weryfikujemy, czy nasz obiekt Settings poprawnie załadował dane z .env
        "gdelt_source": settings.gdelt_api_url
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
    Pobiera treść artykułu i odpytuje lokalny model LLM.
    """
    article_text = await scraper.scrape_article_text(article_item.url)
    ai_summary = await llm.summarize_article(article_text)
    
    return {
        "title": article_item.title,
        "url": article_item.url,
        "llm_summary": ai_summary
    }

@measure_execution_time
async def run_fetch_pipeline(db: Session):
    """
    Niezależna logika pobierania danych. Używana zarówno przez API jak i Scheduler.
    """
    articles_data = await services.fetch_latest_news_from_gdelt()
    if not articles_data:
        return 0

    # OPTYMALIZACJA 1: Wczesne filtrowanie duplikatów (operacja blokująca, na bazie SQLite)
    incoming_urls = [article.url for article in articles_data]
    existing_urls = db.query(models.Article.url).filter(models.Article.url.in_(incoming_urls)).all()
    existing_urls_set = {url[0] for url in existing_urls}
    
    new_articles = [a for a in articles_data if a.url not in existing_urls_set]
    
    if not new_articles:
        print("Wszystkie pobrane artykuły są już w bazie. Pomijam analizę AI.")
        return 0
        
    print(f"Znaleziono {len(new_articles)} nowych artykułów do przeanalizowania przez AI.")
    
    # Asynchroniczne przetwarzanie wszystkich nowych artykułów naraz
    tasks = [process_article(article) for article in new_articles]
    results = await asyncio.gather(*tasks)
    
    processed_articles = [res for res in results if res]
                
    # OPTYMALIZACJA 2: Zapis Wsadowy (Bulk Insert)
    db_articles = []
    for data in processed_articles:
        db_articles.append(models.Article(
            title=data["title"],
            url=data["url"],
            llm_summary=data["llm_summary"]
        ))
        
    if db_articles:
        db.add_all(db_articles)
        try:
            db.commit()
            return len(db_articles)
        except Exception as e:
            db.rollback()
            print(f"Błąd podczas zapisu do bazy: {e}")
            return 0
            
    return 0


@app.post("/fetch-news")
async def fetch_and_save_news(db: Session = Depends(get_db)):
    """
    Ręczne wywołanie pobierania przez użytkownika API.
    """
    saved_count = await run_fetch_pipeline(db)
    return {
        "status": "ok", 
        "message": f"Zapisano {saved_count} nowych artykułów do bazy!"
    }
