import asyncio
from llm import summarize_article
from main import db, models

async def test():
    res = await summarize_article("To jest testowy krótki artykuł o ataku zbrojnym na terytorium Ukrainy. Wojska rosyjskie wycofały się.", title="Testowy artykuł z Ukrainy")
    print(res)

asyncio.run(test())
