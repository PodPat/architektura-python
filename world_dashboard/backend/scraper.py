import httpx
from newspaper import Article

async def scrape_article_text(url: str) -> str:
    """
    Pobiera asynchronicznie kod HTML, a następnie wyciąga czysty tekst za pomocą newspaper3k.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            html = response.text
            
        article = Article(url)
        article.set_html(html)
        article.parse()
        return article.text
    except Exception as e:
        print(f"⚠️ Błąd scrapowania {url}: {e}")
        return ""
