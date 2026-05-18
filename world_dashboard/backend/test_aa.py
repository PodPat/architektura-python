import asyncio
from scraper import scrape_article

async def test():
    url = "https://aa.com.tr/en/africa/nigeria-says-42-students-abducted-in-boko-haram-attack-on-school-in-borno/3939913"
    print("Próbuję scrapować AA...")
    res = await scrape_article(url)
    print("Tytuł:", res.get("title"))
    print("Tekst (pierwsze 200 znaków):", res.get("text")[:200] if res.get("text") else "PUSTO!")

asyncio.run(test())
