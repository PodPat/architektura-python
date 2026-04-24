import pytest
from pydantic import ValidationError

# Ważne: importujemy z naszego modułu głównego!
from schemas import GdeltArticle, GdeltResponse

def test_gdelt_article_valid():
    """Testujemy poprawne utworzenie obiektu."""
    article = GdeltArticle(title="Nowy artykuł", url="http://example.com")
    assert article.title == "Nowy artykuł"
    assert article.url == "http://example.com"

def test_gdelt_article_missing_fields():
    """Sprawdzamy czy próba utworzenia obiektu bez parametru 'url' rzuci wyjątek ValidationError."""
    with pytest.raises(ValidationError):
        # Tytuł jest, ale brakuje wymaganego argumentu 'url'
        GdeltArticle(title="Nowy artykuł bez URL") 

def test_gdelt_response_parsing(mock_gdelt_json):
    """Sprawdzamy czy główny model poprawnie przetwarza naszą Atrapę z conftest.py."""
    # Podajemy fixture do modelu - ** rozpakowuje słownik
    response = GdeltResponse(**mock_gdelt_json)
    
    # Proste asercje sprawdzające czy model sparsował listę artykułów
    assert len(response.articles) == 2
    assert response.articles[0].title == "Testowy news 1"
    assert response.articles[1].url == "http://test2.com"
