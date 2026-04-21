from newspaper import Article

def scrape_article_text(url: str) -> str:
    """
    Pobiera i zwraca czysty tekst artykułu z podanego URL.
    Biblioteka newspaper3k automatycznie usuwa reklamy, menu, stopki itp.
    """
    try:
        article = Article(url)
        article.download()   # 1. Pobiera surowy HTML ze strony
        article.parse()      # 2. Wyciąga tekst artykułu z HTML-a
        return article.text   # 3. Zwraca czysty tekst
    except Exception as e:
        print(f"⚠️ Błąd scrapowania {url}: {e}")
        return ""
