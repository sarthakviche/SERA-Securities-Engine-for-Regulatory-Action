from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from pathlib import Path

# Get the absolute path to the backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "SERA Regulatory Monitoring Service"
    DEBUG_MODE: bool = False
    
    # SEBI Scraping configuration
    SEBI_BASE_URL: str = "https://www.sebi.gov.in"
    SEBI_CIRCULARS_URL: str = f"{SEBI_BASE_URL}/sebiweb/other/OtherAction.do?doListing=yes&sid=3&ssid=0&smid=0"
    
    # Timeouts and retries
    HTTP_TIMEOUT_CONNECT: int = 10
    HTTP_TIMEOUT_READ: int = 30
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_RETRY_DELAY: int = 5
    
    # Data directories
    DATA_DIR: Path = Field(default=BACKEND_DIR / "data")
    DOWNLOADS_DIR: Path = Field(default=BACKEND_DIR / "downloads")
    
    # File paths
    DOCUMENTS_FILE: Path = Field(default=BACKEND_DIR / "data" / "documents.json")
    CHANGE_REPORT_FILE: Path = Field(default=BACKEND_DIR / "data" / "change_report.json")
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.DOWNLOADS_DIR, exist_ok=True)
