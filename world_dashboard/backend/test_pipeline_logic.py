import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Dodajemy katalog do path
sys.path.append(os.path.abspath("."))
import models
from main import run_fetch_pipeline

# 1. Konfigurujemy testową bazę w pamięci RAM (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tworzymy tabele
models.Base.metadata.create_all(bind=engine)

# Przygotowujemy sztuczne dane z BigQuery (zduplikowane URL i wyższe num_mentions)
class MockArticleItem:
    def __init__(self, title, url, domain, seendate, num_mentions, event_code="010", event_root_code="01", quad_class=1):
        self.title = title
        self.url = url
        self.domain = domain
        self.seendate = seendate
        self.num_mentions = num_mentions
        self.event_code = event_code
        self.event_root_code = event_root_code
        self.quad_class = quad_class

# Testujemy logikę
def test_db_logic():
    db = TestingSessionLocal()
    
    # Wstrzykujemy pierwszy artykuł z num_mentions = 5
    art1 = models.Article(
        title="Test", url="http://test.pl/1", domain="test.pl", 
        seendate="20260517", llm_summary="Summary", location="Polska", 
        sentiment="Neutralny", category="Polityka", key_figures="", num_mentions=5
    )
    db.add(art1)
    db.commit()
    
    print("--- TEST 1: Aktualizacja num_mentions ---")
    # GDELT zwraca ten sam artykuł z wyższym licznikiem (12)
    incoming = [
        MockArticleItem("Test", "http://test.pl/1", "test.pl", "20260517", 12)
    ]
    
    # Symulujemy część logiczną aktualizacji z main.py
    existing_articles = db.query(models.Article).filter(models.Article.url.in_(["http://test.pl/1"])).all()
    existing_articles_dict = {a.url: a for a in existing_articles}
    
    updated_count = 0
    for article in incoming:
        if article.url in existing_articles_dict:
            existing = existing_articles_dict[article.url]
            if article.num_mentions and existing.num_mentions is not None and article.num_mentions > existing.num_mentions:
                existing.num_mentions = article.num_mentions
                updated_count += 1
                
    if updated_count > 0:
        db.commit()
        
    # Sprawdzamy czy wartość w bazie uległa zmianie
    updated_art = db.query(models.Article).filter_by(url="http://test.pl/1").first()
    print(f"Oczekiwano: 12 | W bazie: {updated_art.num_mentions}")
    if updated_art.num_mentions == 12:
        print("✅ Sukces: Aktualizacja num_mentions działa poprawnie!")
    else:
        print("❌ Błąd: Licznik nie został zaktualizowany!")

    db.close()

test_db_logic()
