import pytest

@pytest.fixture
def mock_gdelt_json():
    """Zwraca atrapę danych przypominającą JSON z GDELT."""
    return {
        "articles": [
            {"title": "Testowy news 1", "url": "http://test1.com"},
            {"title": "Testowy news 2", "url": "http://test2.com"}
        ]
    }
