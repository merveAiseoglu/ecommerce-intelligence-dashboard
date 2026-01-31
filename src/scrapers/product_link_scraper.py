"""
src/scrapers/product_link_scraper.py

Hepsiburada'dan ürün linklerini toplayan scraper.
- Kategorileri tarar
- Yorum sayısı 1000+ olan ürünleri filtre eder
- Değerlendirme özeti olan ürünleri seçer
- Sonuçları .txt dosyasına kaydeder
"""

import logging
from typing import List, Set, Optional
from pathlib import Path
from dataclasses import dataclass

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.scrapers.base_scraper import BaseScraper, retry_on_failure
from src.config.config_settings import settings


logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# İLERLEYİŞ TAKIP
# ─────────────────────────────────────────

@dataclass
class ScrapingProgress:
    """Scraping'in nerede olduğunu takip eder."""
    total_products_found: int = 0
    valid_products: int = 0
    categories_processed: int = 0
    pages_scraped: int = 0
    errors: int = 0
    skipped_no_reviews: int = 0
    skipped_no_summary: int = 0

    def __str__(self) -> str:
        return (
            f"Bulunan: {self.valid_products}/{settings.MAX_PRODUCTS} ürün | "
            f"Kategori: {self.categories_processed} | "
            f"Sayfa: {self.pages_scraped} | "
            f"Hata: {self.errors}"
        )


# ─────────────────────────────────────────
# PRODUCT LINK SCRAPER
# ─────────────────────────────────────────

class ProductLinkScraper(BaseScraper):
    """
    Hepsiburada'dan ürün URL'lerini toplayan scraper.

    Kullanımı:
        scraper = ProductLinkScraper(headless=True)
        links = scraper.scrape(max_products=100)
    """

    # CSS Selectors — Hepsiburada'nın kullandığı selectors
    PRODUCT_CARD_SELECTOR = "li.productListContent-zAP0Y5msy8OHn5z7T_K_"
    REVIEW_COUNT_SELECTOR = "span.rate-module_count__fjUng"
    SUMMARY_HEADING_XPATH = "//h2[contains(text(), 'Değerlendirme özeti')]"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progress = ScrapingProgress()
        self.collected_links: Set[str] = set()

    # ─────────────────────────
    # ANA METOT
    # ─────────────────────────
    def scrape(
        self,
        categories: Optional[List[str]] = None,
        max_products: int = settings.MAX_PRODUCTS,
        min_reviews: int = settings.MIN_REVIEWS_REQUIRED,
        output_file: Optional[Path] = None,
    ) -> Set[str]:
        """
        Kategorileri tarar ve ürün linklerini toplur.

        Args:
            categories: Tarayacağınız kategori URL'leri (None ise settings'den alır)
            max_products: Kaç ürün toplayacağınız
            min_reviews: Minimum yorum sayısı
            output_file: Sonuçların kaydedileceği dosya yolu

        Returns:
            Toplanan ürün URL'lerinin seti
        """
        if categories is None:
            categories = settings.HEPSIBURADA_CATEGORIES

        if output_file is None:
            output_file = settings.RAW_DATA_DIR / settings.PRODUCT_LINKS_FILE

        logger.info(
            f"Scraping başladı → {len(categories)} kategori | "
            f"Hedef: {max_products} ürün | Min yorum: {min_reviews}"
        )

        try:
            for category_url in categories:
                # Hedef ürün sayısına ulaştıysanız durun
                if len(self.collected_links) >= max_products:
                    logger.info(f"Hedef {max_products} ürüne ulaştı!")
                    break

                self._scrape_category(
                    category_url=category_url,
                    max_products=max_products,
                    min_reviews=min_reviews,
                )
                self.progress.categories_processed += 1

            # Sonuçları kaydet
            self._save_links(output_file)
            logger.info(f"Tamamlandı. {self.progress}")
            return self.collected_links

        except Exception as e:
            logger.error(f"Scraping başarısız: {e}", exc_info=True)
            raise
        finally:
            self.close()

    # ─────────────────────────
    # BIR KATEGORİ TARAMA
    # ─────────────────────────
    def _scrape_category(
        self,
        category_url: str,
        max_products: int,
        min_reviews: int,
    ) -> None:
        """Bir kategori içindeki sayfaları tarar."""
        logger.info(f"Kategori başladı: {category_url}")

        for page_num in range(1, 51):  # Max 50 sayfa
            if len(self.collected_links) >= max_products:
                break

            try:
                page_url = f"{category_url}?sayfa={page_num}"
                self._scrape_page(page_url, min_reviews)
                self.progress.pages_scraped += 1

            except Exception as e:
                logger.warning(f"Sayfa {page_num} hatası: {e}")
                self.progress.errors += 1
                continue

    # ─────────────────────────
    # BIR SAYFA TARAMA
    # ─────────────────────────
    @retry_on_failure(max_retries=3)
    def _scrape_page(self, page_url: str, min_reviews: int) -> None:
        """Tek bir sayfayı tarar, ürün kartlarını inceler."""
        self.get_page(page_url)

        # Ürün kartları yüklenene kadar bekle
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.PRODUCT_CARD_SELECTOR)
                )
            )
        except TimeoutException:
            logger.warning(f"Ürün bulunamadı: {page_url}")
            return

        product_cards = self.driver.find_elements(
            By.CSS_SELECTOR, self.PRODUCT_CARD_SELECTOR
        )
        logger.debug(f"{len(product_cards)} ürün kartı bulundu")

        # ── Yorum sayısına göre filtre ──
        potential_links: List[str] = []

        for card in product_cards:
            try:
                review_text = self.safe_get_text(
                    By.CSS_SELECTOR,
                    self.REVIEW_COUNT_SELECTOR,
                    parent=card,
                )

                if not review_text:
                    continue

                # "(1.234)" → 1234
                review_count = int(
                    review_text.strip("()").replace(".", "").replace(",", "")
                )

                if review_count >= min_reviews:
                    link_el = card.find_element(By.TAG_NAME, "a")
                    url = link_el.get_attribute("href")

                    if url and url not in self.collected_links:
                        potential_links.append(url)
                        self.progress.total_products_found += 1
                else:
                    self.progress.skipped_no_reviews += 1

            except (NoSuchElementException, ValueError):
                continue

        # ── Değerlendirme özeti kontrolü ──
        for product_url in potential_links:
            if len(self.collected_links) >= settings.MAX_PRODUCTS:
                break

            if self._has_review_summary(product_url):
                self.collected_links.add(product_url)
                self.progress.valid_products += 1
                logger.info(
                    f"✅ Eklendi ({self.progress.valid_products}/"
                    f"{settings.MAX_PRODUCTS})"
                )
            else:
                self.progress.skipped_no_summary += 1

    # ─────────────────────────
    # ÖZET KONTROLÜ
    # ─────────────────────────
    def _has_review_summary(self, product_url: str) -> bool:
        """Ürünün yorum özeti var mı kontrol eder."""
        reviews_url = self._get_reviews_url(product_url)

        # Yeni sekme aç
        self.driver.execute_script(f"window.open('{reviews_url}');")
        self.driver.switch_to.window(self.driver.window_handles[-1])

        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, self.SUMMARY_HEADING_XPATH)
                )
            )
            has_summary = True
        except TimeoutException:
            has_summary = False
        finally:
            # Sekmeyi kapat, ana sekmeye dön
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

        return has_summary

    # ─────────────────────────
    # YARDIMCI METOTLAR
    # ─────────────────────────
    @staticmethod
    def _get_reviews_url(product_url: str) -> str:
        """Ürün URL'sini yorum sayfası URL'sine çevirir."""
        clean_url = product_url.split("?")[0]
        if "-yorumlari" not in clean_url:
            clean_url += "-yorumlari"
        return clean_url

    def _save_links(self, output_file: Path) -> None:
        """Toplanan linkler dosyaya kaydedilir."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            for link in sorted(self.collected_links):
                f.write(f"{link}\n")

        logger.info(f"💾 {len(self.collected_links)} link → {output_file}")


# ─────────────────────────────────────────
# ÇALIŞTIRMA (python -m src.scrapers.product_link_scraper)
# ─────────────────────────────────────────

if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("🚀 Product Link Scraper başlıyor...\n")

    with ProductLinkScraper(headless=True) as scraper:
        links = scraper.scrape(
            max_products=10,   # Test için küçük sayı
            min_reviews=1000,
        )

    print(f"\n{'─' * 50}")
    print(f"✅ Toplanan ürün sayısı: {len(links)}")
    print(f"📁 Kaydetilen dosya: {settings.RAW_DATA_DIR / settings.PRODUCT_LINKS_FILE}")