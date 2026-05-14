import httpx
from newspaper import Article

async def scrape_article_text(url: str) -> str:
    """
    Pobiera asynchronicznie kod HTML, a następnie wyciąga czysty tekst za pomocą newspaper3k.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                print(f"⚠️ Serwer zwrócił status {response.status_code} dla {url}")
                return ""
            html = response.text
            
        article = Article(url)
        article.set_html(html)
        article.parse()
        
        # Jeśli newspaper wyciągnął tylko kilka słów, to prawdopodobnie trafił na paywall/cookies
        if len(article.text) < 100:
            return ""
            
        return article.text
    except Exception as e:
        print(f"⚠️ Błąd scrapowania {url}: {type(e).__name__}")
        return ""
