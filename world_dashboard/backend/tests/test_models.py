import pytest
from models import Article

def test_article_creation():
    """Sprawdza, czy obiekt Article poprawnie zapisuje swoje atrybuty."""
    article = Article(
        title="Ważne wydarzenie", 
        url="http://news.com/123", 
        domain="news.com",
        seendate="20260424T120000Z",
        llm_summary="Krótkie podsumowanie AI.",
        location="Polska, Warszawa",
        sentiment="Pozytywny",
        category="Polityka",
        key_figures="Prezydent"
    )
    
    assert article.title == "Ważne wydarzenie"
    assert article.url == "http://news.com/123"
    assert article.domain == "news.com"
    assert article.seendate == "20260424T120000Z"
    assert article.llm_summary == "Krótkie podsumowanie AI."
    assert article.location == "Polska, Warszawa"
    assert article.sentiment == "Pozytywny"
    assert article.category == "Polityka"
    assert article.key_figures == "Prezydent"
