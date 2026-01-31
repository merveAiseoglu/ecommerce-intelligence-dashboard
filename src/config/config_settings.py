"""
config/config_settings.py

Tüm ayarlar burada. .env dosyasından API key'leri ve diğer değerleri okur.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()


class Settings:
    """Uygulama ayarları."""

    # --- Proje Bilgileri ---
    PROJECT_NAME: str = "E-Commerce Product Intelligence Platform"
    VERSION: str = "1.0.0"

    # --- API Anahtarları (.env'den okunur) ---
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # --- Dizin Yapısı (otomatik oluşturulur) ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent  # projenin ana klasörü
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    OUTPUT_DIR: Path = DATA_DIR / "output"
    LOG_DIR: Path = BASE_DIR / "logs"

    # --- Dosya Adları ---
    PRODUCT_LINKS_FILE: str = "product_links.txt"
    PRODUCTS_CSV: str = "products.csv"
    REVIEWS_CSV: str = "reviews.csv"
    AI_SUMMARIES_CSV: str = "ai_summaries.csv"
    FINAL_OUTPUT_CSV: str = "products_with_ai_insights.csv"

    # --- Scraper Ayarları ---
    SCRAPER_HEADLESS: bool = True
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_PAGE_LOAD_TIMEOUT: int = 60
    REQUESTS_PER_MINUTE: int = 30

    # --- Ürün Filtreleri ---
    MIN_REVIEWS_REQUIRED: int = 1000
    MAX_PRODUCTS: int = 1000

    # --- AI Ayarları ---
    AI_MODEL: str = "gpt-3.5-turbo"
    AI_MAX_TOKENS: int = 1000
    CHUNK_SIZE: int = 200  # Her chunk'ta kaç yorum işlenir

    # --- Hepsiburada Kategoriler ---
    HEPSIBURADA_CATEGORIES: list = [
        "https://www.hepsiburada.com/bilgisayarlar-c-2147483646",
        "https://www.hepsiburada.com/elektrikli-ev-aletleri-c-17071",
        "https://www.hepsiburada.com/foto-kameralari-c-2147483606",
        "https://www.hepsiburada.com/makyaj-urunleri-c-341425",
        "https://www.hepsiburada.com/cilt-bakim-urunleri-c-32000005",
        "https://www.hepsiburada.com/oyuncaklar-c-23031884",
        "https://www.hepsiburada.com/dekorasyon-c-18021300",
        "https://www.hepsiburada.com/mutfak-gerecleri-c-22500",
    ]

    def __init__(self):
        """Başlatıldığında gerekli klasörleri oluştur."""
        self._create_directories()

    def _create_directories(self) -> None:
        """Gerekli klasörleri oluştur."""
        for directory in [
            self.DATA_DIR,
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.OUTPUT_DIR,
            self.LOG_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# Tek bir global instance — her yerden `settings` import edebilirsiniz
settings = Settings()