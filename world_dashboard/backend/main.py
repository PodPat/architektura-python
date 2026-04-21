from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import concurrent.futures
from config import settings
from database import engine, get_db
import models
import services
import scraper
import llm


models.Base.metadata.create_all(bind=engine)
# Inicjalizacja głównej instancji aplikacji FastAPI
app = FastAPI(
    title="World Dashboard API",
    description="Backend agregujący dane ze świata",
    version="1.0.0"
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

def process_article(article_item):
    """
    Funkcja pomocnicza. Działa w osobnym wątku.
    Pobiera treść artykułu i odpytuje lokalny model LLM.
    """
    article_text = scraper.scrape_article_text(article_item.url)
    ai_summary = llm.summarize_article(article_text)
    
    return {
        "title": article_item.title,
        "url": article_item.url,
        "llm_summary": ai_summary
    }

@app.post("/fetch-news")
def fetch_and_save_news(db: Session = Depends(get_db)):
    """
    Endpoint pobierający dane z GDELT i zapisujący je do bazy SQLite.
    Używamy "Wstrzykiwania Zależności" (Depends), dzięki czemu FastAPI 
    samo otwiera i zamyka połączenie (sesję) z bazą danych przy każdym zapytaniu.
    """
    
    # 1. Pobieramy zweryfikowane dane za pomocą naszego serwisu
    articles_data = services.fetch_latest_news_from_gdelt()
    
    saved_count = 0
    
    processed_articles = []
    
    # 2. Równoległe pobieranie i przetwarzanie przez LLM w 5 wątkach (koncepcja z Lab 2)
    # Znacznie przyśpieszy to generowanie jeśli mamy np. 50 artykułów
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(process_article, articles_data)
        for res in results:
            if res:
                processed_articles.append(res)
                
    # 3. Sekwencyjny zapis do bazy danych (aby zachować bezpieczeństwo sesji SQLAlchemy)
    for data in processed_articles:
        db_article = models.Article(
            title=data["title"],
            url=data["url"],
            llm_summary=data["llm_summary"]
        )
        
        db.add(db_article)
        try:
            db.commit()
            saved_count += 1
        except Exception:
            db.rollback()

    # Zwracamy odpowiedź w formacie JSON
    return {
        "status": "ok", 
        "message": f"Zapisano {saved_count} nowych artykułów do bazy!"
    }
