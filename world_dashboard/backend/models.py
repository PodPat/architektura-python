from sqlalchemy import Column, Integer, String, Text
from database import Base

class Article(Base):

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    domain = Column(String, nullable=True)
    seendate = Column(String, nullable=True)

    llm_summary = Column(String, nullable=True)
    location = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)
    category = Column(String, nullable=True)
    key_figures = Column(String, nullable=True)
    embedding = Column(Text, nullable=True)      # JSON embedding wektora
    cluster_id = Column(Integer, nullable=True)  # ID grupy tematycznej

    # NOWE KOLUMNY CAMEO
    event_code = Column(String, nullable=True)
    event_root_code = Column(String, nullable=True)
    quad_class = Column(Integer, nullable=True)
    num_mentions = Column(Integer, default=0)


