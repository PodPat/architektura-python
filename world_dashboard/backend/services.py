from PIL import TiffImagePlugin
import httpx
from config import settings
from schemas import GdeltResponse

async def fetch_latest_news_from_gdelt():
    """
    Pobiera najnowsze artykuły z API GDELT.
    """
    params = {
        "query": "(domain:tvn24.pl OR domain:onet.pl OR domain:wp.pl OR domain:wyborcza.pl OR domain:polsatnews.pl OR domain:rmf24.pl OR domain:tokfm.pl OR domain:cnn.com OR domain:bbc.com OR domain:reuters.com) sourcelang:polish",
        "mode": "artlist",
        "format": "json",
        "maxrecords": 50
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.gdelt_api_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Ochrona przed pustą odpowiedzią
            if not response.text:
                print("⚠️ GDELT zwrócił pustą odpowiedź.")
                return []
            raw_data = response.json()
            validated_response = GdeltResponse(**raw_data)
            return validated_response.articles
            
    except httpx.HTTPError as e:
        print(f"⚠️ Błąd sieciowy/HTTP: {e}")
        return []
    except ValueError as e:
        print(f"⚠️ Błąd formatu (to nie jest JSON): {e}")
        return []