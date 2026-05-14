import httpx
from datetime import datetime
import asyncio
import random
from config import settings
from schemas import GdeltResponse, GdeltArticle

async def fetch_latest_news_from_gdelt():
    """
    Pobiera najnowsze artykuły z API GDELT za pomocą jednego zbiorczego zapytania.
    Zawiera logikę ponawiania prób w przypadku błędów.
    """
    domains = [
        "domain:tvn24.pl", "domain:onet.pl", "domain:wp.pl", 
        "domain:cnn.com", "domain:reuters.com", "domain:bbc.com",
        "domain:aljazeera.com", "domain:nytimes.com", "domain:bloomberg.com"
    ]
    query = "(" + " OR ".join(domains) + ") (sourcelang:polish OR sourcelang:english)"
    
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": 30,
        "timespan": "5h",
        "sortby": "date"
    }
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    max_retries = 3
    for attempt in range(max_retries):
        now = datetime.now().strftime("%H:%M:%S")
        headers = {"User-Agent": random.choice(user_agents)}
        
        try:
            async with httpx.AsyncClient(timeout=50.0) as client:
                print(f"📡 [{now}] Pobieram newsy z GDELT (próba {attempt + 1}/{max_retries})...")
                response = await client.get(settings.gdelt_api_url, params=params, headers=headers)
                
                if response.status_code == 429:
                    print(f"⏳ [{now}] Rate limit (429). Czekam 10s przed ponowieniem...")
                    await asyncio.sleep(10)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                validated = GdeltResponse(**data)
                
                print(f"✅ [{now}] GDELT zwrócił {len(validated.articles)} artykułów.")
                return validated.articles
                
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            print(f"⚠️ [{now}] Błąd połączenia/timeout: {e}. Ponawiam za 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"❌ [{now}] Nieoczekiwany błąd: {e}")
            break
            
    return []