from pydantic import BaseModel
from typing import List, Optional

class GdeltArticle(BaseModel):
    title: str
    url: str
    domain: Optional[str] = None
    seendate: Optional[str] = None

class GdeltResponse(BaseModel):
    articles: List[GdeltArticle]
