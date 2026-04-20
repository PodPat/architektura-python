from pydantic import BaseModel
from typing import List

class GdeltArticle(BaseModel):
    title: str
    url: str

class GdeltResponse(BaseModel):
    articles: List[GdeltArticle]
