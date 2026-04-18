from fastapi import FastAPI
from config import settings

# Inicjalizacja głównej instancji aplikacji FastAPI
app = FastAPI(
    title="World Dashboard API",
    description="Backend agregujący dane ze świata",
    version="1.0.0"
)

# Nawiązanie do Lab 1: Używamy wzorca Dekorator, aby powiązać 
# ścieżkę HTTP (GET "/") z konkretną funkcją Pythona.
@app.get("/")
def health_check():
    """
    Endpoint sprawdzający status działania API.
    """
    return {
        "status": "ok",
        "message": "World Dashboard API działa poprawnie!",
        # Weryfikujemy, czy nasz obiekt Settings poprawnie załadował dane z .env
        "gdelt_source": settings.gdelt_api_url
    }
