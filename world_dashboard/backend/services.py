import requests
from requests.exceptions import HTTPError
from config import settings
from schemas import GdeltResponse

def fetch_latest_news_from_gdelt():
    """
    Pobiera najnowsze artykuły z API GDELT. Jeśli API odpowie błędem 
    (np. 429 Too Many Requests), aplikacja się nie zawiesi, tylko zwróci pustą listę.
    """
    params = {
        "query": "climate",
        "mode": "artlist",
        "format": "json",
        "maxrecords": 5
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(settings.gdelt_api_url, params=params, headers=headers)

    
    try:
        # Próbujemy sprawdzić, czy odpowiedź jest poprawna (status 200)
        response.raise_for_status()
        
        # Jeśli tak, procesujemy JSON
        raw_data = response.json()
        validated_response = GdeltResponse(**raw_data)
        return validated_response.articles
        
    except HTTPError as e:
        # Łapiemy błąd połączenia HTTP (np. 429)
        print(f"⚠️ Błąd pobierania danych z GDELT: {e}")
        # Zwracamy pustą listę artykułów, żeby aplikacja mogła działać dalej
        return []
