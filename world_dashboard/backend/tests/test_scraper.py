import pytest
from scraper import scrape_article_text

@pytest.mark.asyncio
@pytest.mark.parametrize("url, expected_result", [
    ("http://nieistniejacy-adres-123456789.com", ""), # Wywołanie powinno wejść w bloku except i oddać pusty string
    ("not-a-valid-url", ""),                          # Totalnie błędny format URL
    ("", "")                                          # Pusty adres URL
])
async def test_scrape_article_text_failures(url, expected_result):
    """Sprawdzamy czy scraper poprawnie radzi sobie z błędnymi adresami używając parametryzacji."""
    result = await scrape_article_text(url)
    assert result == expected_result
