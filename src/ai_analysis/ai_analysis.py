"""
src/ai_analysis/ai_analysis.py

AI ile yorum analizi ve özet çıkarma modülü.
- OpenAI GPT kullanarak yorumları özetler
- Chunk-based processing (büyük yorum setleri için)
- Retry logic ile API hatalarını yönetir
"""

import json
import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

import pandas as pd
import openai
from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config.config_settings import settings


logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# ENUMS & DATACLASSES
# ─────────────────────────────────────────

class Sentiment(Enum):
    """Ürün duygu kategorileri."""
    VERY_POSITIVE = "Çok Olumlu"
    POSITIVE = "Olumlu"
    NEUTRAL = "Nötr"
    NEGATIVE = "Olumsuz"
    VERY_NEGATIVE = "Çok Olumsuz"


@dataclass
class ReviewSummary:
    """AI özet sonucunu tutan dataclass."""
    product_id: str
    overall_summary: str
    positive_aspects: List[str]
    negative_aspects: List[str]
    price_performance: str
    packaging_quality: str
    shipping_speed: str
    sentiment: str
    reviews_analyzed: int

    def to_dict(self) -> Dict:
        """CSV'ye kaydet için dict'e çevir."""
        return {
            "product_id": self.product_id,
            "ai_summary": self.overall_summary,
            "positive_points": " | ".join(self.positive_aspects),
            "negative_points": " | ".join(self.negative_aspects),
            "price_performance": self.price_performance,
            "packaging": self.packaging_quality,
            "shipping": self.shipping_speed,
            "sentiment": self.sentiment,
            "reviews_count": self.reviews_analyzed,
        }


# ─────────────────────────────────────────
# LLM CLIENT  (OpenAI sarıcı)
# ─────────────────────────────────────────

class LLMClient:
    """
    OpenAI API ile konuşan client.

    Özellikler:
    - Otomatik retry (RateLimitError, APIError)
    - Token kullanım takibi
    - Logging
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY bulunamadı! "
                ".env dosyasına ekleyin veya environment variable olarak tanımlayın."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.AI_MODEL

        # Kullanım istatistikleri
        self.total_requests = 0
        self.total_tokens = 0

        logger.info(f"LLM Client hazır → model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIError)),
    )
    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        OpenAI'a prompt gönderir, yanıt döndürür.

        Args:
            prompt: Gönderilecek prompt metni
            max_tokens: Max çıktı token sayısı

        Returns:
            Yapay zeka yanıtı (string)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )

            # İstatistik güncelle
            self.total_requests += 1
            if response.usage:
                self.total_tokens += response.usage.total_tokens

            content = response.choices[0].message.content
            logger.debug(f"Yanıt geldi: {len(content)} karakter")
            return content

        except openai.RateLimitError:
            logger.warning("Rate limit doldu, 60s beklenecek...")
            time.sleep(60)
            raise  # retry decorator tekrar deneyecek

        except openai.APIError as e:
            logger.error(f"API hata: {e}")
            raise

    def get_usage_stats(self) -> Dict:
        """Kullanım istatistiklerini döndür."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
        }


# ─────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────

CHUNK_PROMPT = """Aşağıda bir ürüne ait kullanıcı yorumları bulunmaktadır.
Bu yorumlara dayanarak kısa ve objektif bir özet çıkar.

Şu konulara değin:
- Genel değerlendirme
- Olumlu yönler  
- Olumsuz yönler
- Fiyat / performans
- Paketleme kalitesi
- Kargo hızı

Yorumlar:
{reviews}

Özet:"""


FINAL_PROMPT = """Aşağıda bir ürün hakkında farklı yorum gruplarından çıkarılmış özetler var.
Bu özetleri birleştirerek tek bir kapsamlı değerlendirme oluştur.

SADECE aşağıdaki JSON formatında yanıt ver, başka hiçbey şey yazma:
{{
  "overall_summary": "...",
  "positive_aspects": ["...", "..."],
  "negative_aspects": ["...", "..."],
  "price_performance": "...",
  "packaging_quality": "...",
  "shipping_speed": "...",
  "sentiment": "Olumlu veya Nötr veya Olumsuz"
}}

Özetler:
{summaries}
"""


# ─────────────────────────────────────────
# REVIEW SUMMARIZER
# ─────────────────────────────────────────

class ReviewSummarizer:
    """
    Ürün yorumlarını AI ile özetleyen sınıf.

    Nasıl çalışır:
    1. Yorumları chunk_size'luk gruplara ayırır
    2. Her grubu ayrıca özetletir (CHUNK_PROMPT)
    3. Tüm özet parçalarını tek bir özete birleştir (FINAL_PROMPT)
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.chunk_size = settings.CHUNK_SIZE
        logger.info(f"ReviewSummarizer hazır → chunk_size: {self.chunk_size}")

    def summarize(
        self, product_id: str, reviews: List[str]
    ) -> ReviewSummary:
        """
        Bir ürünün yorumlarını analiz eder ve özet üretir.

        Args:
            product_id: Ürün ID'si
            reviews: Yorum listesi

        Returns:
            ReviewSummary dataclass
        """
        if not reviews:
            logger.warning(f"{product_id}: Yorum yok, boş özet döndürülüyor.")
            return self._empty_summary(product_id)

        logger.info(f"[{product_id}] {len(reviews)} yorum analiz ediliyor...")

        try:
            # Step 1: Chunk'lara ayır ve her birini özetle
            chunk_summaries = self._process_chunks(reviews)

            if not chunk_summaries:
                return self._empty_summary(product_id)

            # Step 2: Tüm özet parçalarını birleştir
            final = self._generate_final_summary(chunk_summaries)

            return ReviewSummary(
                product_id=product_id,
                overall_summary=final.get("overall_summary", ""),
                positive_aspects=final.get("positive_aspects", []),
                negative_aspects=final.get("negative_aspects", []),
                price_performance=final.get("price_performance", ""),
                packaging_quality=final.get("packaging_quality", ""),
                shipping_speed=final.get("shipping_speed", ""),
                sentiment=final.get("sentiment", "Nötr"),
                reviews_analyzed=len(reviews),
            )

        except Exception as e:
            logger.error(f"[{product_id}] Özet üretim hatası: {e}", exc_info=True)
            return self._error_summary(product_id, str(e))

    # ── Chunk işleme ──
    def _process_chunks(self, reviews: List[str]) -> List[str]:
        """Yorumları gruplara ayırır, her grubu ayrıca özetler."""
        chunks = [
            reviews[i : i + self.chunk_size]
            for i in range(0, len(reviews), self.chunk_size)
        ]

        summaries = []
        for idx, chunk in enumerate(chunks, 1):
            try:
                review_text = "\n".join(chunk)
                prompt = CHUNK_PROMPT.format(reviews=review_text)

                result = self.llm.generate(prompt=prompt, max_tokens=500)
                summaries.append(result)

                logger.debug(f"  Chunk {idx}/{len(chunks)} tamamlandı")
                time.sleep(1.5)  # Rate limit koruma

            except Exception as e:
                logger.warning(f"  Chunk {idx} başarısız: {e}")
                continue

        return summaries

    # ── Final özet ──
    def _generate_final_summary(self, chunk_summaries: List[str]) -> Dict:
        """Tüm chunk özetlerini tek JSON'a birleştir."""
        summaries_text = "\n\n---\n\n".join(chunk_summaries)
        prompt = FINAL_PROMPT.format(summaries=summaries_text)

        raw_result = self.llm.generate(prompt=prompt, max_tokens=800)

        # JSON parse et
        try:
            # Eğer markdown code block içindeyse temizle
            cleaned = raw_result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()

            return json.loads(cleaned)

        except json.JSONDecodeError:
            # JSON parse başarısız olursa raw text döndür
            logger.warning("JSON parse başarısız, raw text kullanılıyor")
            return {
                "overall_summary": raw_result[:500],
                "positive_aspects": [],
                "negative_aspects": [],
                "price_performance": "Analiz edilemedi",
                "packaging_quality": "Analiz edilemedi",
                "shipping_speed": "Analiz edilemedi",
                "sentiment": "Nötr",
            }

    # ── Boş/Hata özetleri ──
    def _empty_summary(self, product_id: str) -> ReviewSummary:
        return ReviewSummary(
            product_id=product_id,
            overall_summary="Yeterli yorum bulunamadı.",
            positive_aspects=[],
            negative_aspects=[],
            price_performance="—",
            packaging_quality="—",
            shipping_speed="—",
            sentiment="Nötr",
            reviews_analyzed=0,
        )

    def _error_summary(self, product_id: str, error: str) -> ReviewSummary:
        return ReviewSummary(
            product_id=product_id,
            overall_summary=f"Analiz hatası: {error}",
            positive_aspects=[],
            negative_aspects=[],
            price_performance="—",
            packaging_quality="—",
            shipping_speed="—",
            sentiment="Nötr",
            reviews_analyzed=0,
        )


# ─────────────────────────────────────────
# ANA PIPELINE FONKSIYONU
# ─────────────────────────────────────────

def run_ai_analysis(
    reviews_csv: str = None,
    output_csv: str = None,
) -> pd.DataFrame:
    """
    CSV'deki yorumları oku, AI özet üret, sonuçları kaydet.

    Args:
        reviews_csv: Yorum CSV dosyası yolu
        output_csv: Özet CSV dosyası yolu

    Returns:
        Özet DataFrame
    """
    if reviews_csv is None:
        reviews_csv = str(settings.RAW_DATA_DIR / settings.REVIEWS_CSV)
    if output_csv is None:
        output_csv = str(settings.PROCESSED_DATA_DIR / settings.AI_SUMMARIES_CSV)

    logger.info(f"📂 Yorumlar okunuyor: {reviews_csv}")

    # CSV oku
    df = pd.read_csv(reviews_csv)
    grouped = df.groupby("product_id")["review"].apply(list)

    # AI components
    llm = LLMClient()
    summarizer = ReviewSummarizer(llm)

    # Her ürün için özet üret
    results = []
    total = len(grouped)

    for idx, (product_id, review_list) in enumerate(grouped.items(), 1):
        logger.info(f"[{idx}/{total}] {product_id} işleniyor...")

        summary = summarizer.summarize(product_id, review_list)
        results.append(summary.to_dict())

    # Sonuçları kaydet
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_csv, index=False)

    logger.info(f"💾 Özetler kaydedildi: {output_csv}")
    logger.info(f"📊 API kullanım: {llm.get_usage_stats()}")

    return result_df


# ─────────────────────────────────────────
# ÇALIŞTIRMA
# ─────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("🤖 AI Analysis başlıyor...\n")
    result = run_ai_analysis()
    print(f"\n✅ Tamamlandı! {len(result)} ürün analiz edildi.")