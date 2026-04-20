from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from config import settings
from database import engine, get_db
import models
import services


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
    
    # 2. Przechodzimy pętlą po każdym pobranym artykule
    for article_item in articles_data:
        
        # 3. Zamieniamy model Pydantic na model bazy danych SQLAlchemy
        db_article = models.Article(
            title=article_item.title,
            url=article_item.url
        )
        
        # 4. Kolejkujemy artykuł do zapisu
        db.add(db_article)
        
        # 5. Próbujemy go fizycznie zapisać (commit)
        try:
            db.commit()
            saved_count += 1
        except Exception:
            # W pliku models.py ustawiliśmy unique=True na polu url.
            # Jeżeli próbujemy zapisać ten sam artykuł drugi raz, 
            # baza wyrzuci błąd. Musimy wycofać wtedy transakcję (rollback).
            db.rollback()

    # Zwracamy odpowiedź w formacie JSON
    return {
        "status": "ok", 
        "message": f"Zapisano {saved_count} nowych artykułów do bazy!"
    }
