"""
src/scrapers/base_scraper.py

Tüm scraper'ların kullanacağı temel sınıf.
- Otomatik retry (başarısız olursa tekrar dener)
- Rate limiting (çok hızlı istek atmayı engeller)
- Hata yönetimi
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from functools import wraps

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
)
from webdriver_manager.chrome import ChromeDriverManager

# Kendi settings'imizi import ediyoruz
from src.config.config_settings import settings


# Logger kurulum
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# CUSTOM EXCEPTION SINIFLAR
# ─────────────────────────────────────────

class ScraperException(Exception):
    """Scraper'a özgü genel hata."""
    pass


class ElementNotFoundException(ScraperException):
    """Sayfa üzerinde aranan element bulunamadığında."""
    pass


# ─────────────────────────────────────────
# RETRY DECORATOR  (otomatik tekrar deneme)
# ─────────────────────────────────────────

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 2.0,
    backoff_multiplier: float = 2.0,
):
    """
    Bir fonksiyon başarısız olursa otomatik olarak tekrar eder.

    Args:
        max_retries: Kaç kez tekrar denesin
        delay: İlk bekle süresi (saniye)
        backoff_multiplier: Her denede bekle süresi ne kadar artsın
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (WebDriverException, TimeoutException, ScraperException) as e:
                    if attempt < max_retries:
                        logger.warning(
                            f"[{func.__name__}] Deneme {attempt + 1}/{max_retries} başarısız: {e} "
                            f"→ {current_delay:.1f}s beklenecek..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_multiplier
                    else:
                        logger.error(f"[{func.__name__}] {max_retries} deneme de başarısız oldu.")
                        raise

        return wrapper
    return decorator


# ─────────────────────────────────────────
# RATE LIMITER  (istek hızı sınırlama)
# ─────────────────────────────────────────

class RateLimiter:
    """
    Belirli bir süre içinde yapılan istek sayısını sınırlar.
    Böylece site tarafından engellenmekten kaçınılır.
    """

    def __init__(self, max_requests: int = 30, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window  # saniye
        self.requests: list = []

    def wait_if_needed(self) -> None:
        """Limit dolmak üzereyse bekle."""
        now = time.time()

        # Zaman penceresi dışında kalan eski istekleri sil
        self.requests = [
            t for t in self.requests if now - t < self.time_window
        ]

        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 1
            if sleep_time > 0:
                logger.info(f"Rate limit doldu. {sleep_time:.1f}s beklenecek...")
                time.sleep(sleep_time)
                self.requests = []

        self.requests.append(now)


# ─────────────────────────────────────────
# BASE SCRAPER SINIFI
# ─────────────────────────────────────────

class BaseScraper(ABC):
    """
    Tüm scraper'ların miras aldığı temel sınıf.

    Sağladığı özellikler:
    - Chrome WebDriver kurulum / kapatma
    - Rate limiting
    - Retry logic
    - Güvenli element arama
    - Context manager desteği (with ... as ...:)
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        self.headless = headless
        self.timeout = timeout
        self.rate_limiter = rate_limiter or RateLimiter(
            max_requests=settings.REQUESTS_PER_MINUTE
        )

        self._driver: Optional[webdriver.Chrome] = None
        self._wait: Optional[WebDriverWait] = None

        logger.info(f"{self.__class__.__name__} başlatıldı.")

    # ── Driver kurulum ──
    def _setup_driver(self) -> webdriver.Chrome:
        """Chrome WebDriver'ı kurar ve ayarlar."""
        options = Options()

        if self.headless:
            options.add_argument("--headless")

        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # Resim yüklememe → daha hızlı
        prefs = {"profile.default_content_setting_values": {"images": 2}}
        options.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(settings.SCRAPER_PAGE_LOAD_TIMEOUT)

        logger.info("WebDriver hazır.")
        return driver

    # ── Lazy-load properties ──
    @property
    def driver(self) -> webdriver.Chrome:
        """Driver ilk kullanıldığında kurulur."""
        if self._driver is None:
            self._driver = self._setup_driver()
            self._wait = WebDriverWait(self._driver, self.timeout)
        return self._driver

    @property
    def wait(self) -> WebDriverWait:
        if self._wait is None:
            self._wait = WebDriverWait(self.driver, self.timeout)
        return self._wait

    # ── Sayfa açma ──
    @retry_on_failure(max_retries=3)
    def get_page(self, url: str) -> None:
        """URL'ye git. Başarısız olursa otomatik tekrar dener."""
        self.rate_limiter.wait_if_needed()
        logger.debug(f"Sayfa açılıyor: {url}")
        self.driver.get(url)
        time.sleep(1)  # Sayfa stabilize olsun

    # ── Kapatma ──
    def close(self) -> None:
        """Driver'ı kapatır ve kaynakları serbest bırakır."""
        if self._driver:
            try:
                self._driver.quit()
                logger.info("WebDriver kapatıldı.")
            except Exception as e:
                logger.error(f"Driver kapatma hatası: {e}")
            finally:
                self._driver = None
                self._wait = None

    # ── Context manager (with ... as ...) ──
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ── Güvenli element arama ──
    def safe_find_element(
        self,
        by: str,
        value: str,
        default: Any = None,
        parent=None,
    ) -> Any:
        """
        Element arar, bulunamazsa exception yerine default döndürür.
        """
        context = parent if parent else self.driver
        try:
            return context.find_element(by, value)
        except NoSuchElementException:
            return default

    def safe_get_text(
        self,
        by: str,
        value: str,
        default: str = "",
        parent=None,
    ) -> str:
        """Element'in text'ini döndürür. Bulunamazsa default döndürür."""
        element = self.safe_find_element(by, value, default=None, parent=parent)
        if element:
            return element.text.strip()
        return default

    # ── Soyut metot (alt sınıflar doldurur) ──
    @abstractmethod
    def scrape(self, *args, **kwargs) -> Any:
        """
        Her scraper kendi scrape() metotunu yazır.
        """
        pass