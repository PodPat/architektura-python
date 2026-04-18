from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

# 1. Silnik bazy danych (Engine)
engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)

# 2. Fabryka sesji (Session Factory)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Klasa bazowa dla modeli ORM
Base = declarative_base()

# 4. Generator wstrzykiwania zależności (Dependency Injection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
