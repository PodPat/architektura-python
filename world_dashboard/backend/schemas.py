from pydantic import BaseModel
from typing import List, Optional

class GdeltArticle(BaseModel):
    title: Optional[str] = "Brak tytułu"
    url: Optional[str] = None
    domain: Optional[str] = None
    seendate: Optional[str] = None

    class Config:
        extra = "ignore"  # Ignoruj dodatkowe pola, których nie znamy

class GdeltResponse(BaseModel):
    articles: Optional[List[GdeltArticle]] = []
