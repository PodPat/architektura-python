import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
class Settings(BaseSettings):
    database_url: str
    google_application_credentials: Optional[str] = None
    google_cloud_project: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
# Automatyczne załadowanie zmiennych środowiskowych dla bibliotek Google Cloud
if settings.google_application_credentials:
    # Pobieramy pełną ścieżkę absolutną, gdyby podano ścieżkę względną w .env
    abs_path = os.path.abspath(settings.google_application_credentials)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path
if settings.google_cloud_project:
    os.environ["GOOGLE_CLOUD_PROJECT"] = settings.google_cloud_project