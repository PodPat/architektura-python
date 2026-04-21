from PIL import TiffImagePlugin
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
        "query": "(domain:bbc.com OR domain:reuters.com OR domain:cnn.com OR domain:theguardian.com) (sourcelang:english OR sourcelang:polish)",
        "mode": "artlist",
        "format": "json",
        "maxrecords": 5
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(settings.gdelt_api_url, params=params, headers=headers, timeout=30)

    
    try:
        response.raise_for_status()
        
        # Ochrona przed pustą odpowiedzią
        if not response.text:
            print("⚠️ GDELT zwrócił pustą odpowiedź.")
            return []
        raw_data = response.json()
        validated_response = GdeltResponse(**raw_data)
        return validated_response.articles
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Błąd sieciowy: {e}")
        return []
    except ValueError as e:
        print(f"⚠️ Błąd formatu (to nie jest JSON): {e}")
        return []