from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class GdeltArticle(BaseModel):
    # Tytuł może być opcjonalny (BigQuery events nie posiada tytułów artykułów prasowych - pobierzemy go w scraperze)
    title: Optional[str] = "Brak tytułu"
    url: str  
    domain: Optional[str] = None
    seendate: Optional[str] = None
    
    # Nowe pola CAMEO z BigQuery
    event_code: Optional[str] = None
    event_root_code: Optional[str] = None
    quad_class: Optional[int] = None
    num_mentions: Optional[int] = 0

    model_config = ConfigDict(extra="ignore")
class GdeltResponse(BaseModel):
    articles: Optional[List[GdeltArticle]] = []