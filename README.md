
---

# 🛍️ E-Commerce Product Intelligence Dashboard

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge\&logo=python\&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-FF4B4B?style=for-the-badge\&logo=streamlit\&logoColor=white)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI%20GPT-412991?style=for-the-badge\&logo=openai\&logoColor=white)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> **Hepsiburada ürün verilerini analiz eden, kullanıcı yorumlarını Yapay Zeka (GPT) ile özetleyen ve satıcılar için stratejik içgörüler sunan uçtan uca veri analitiği platformu.**

---

## 📸 Proje Önizlemesi
<div align="center">
  <img src="png/13.PNG" alt="Dashboard Preview 1" width="90%">
  <br><br>
  <img src="png/14.PNG" alt="Dashboard Preview 2" width="90%">
  <br><br>
  <img src="png/15.PNG" alt="Dashboard Preview 3" width="90%">
</div>




---

## 📊 Proje Metrikleri & Kapsam

Bu proje, büyük ölçekli e-ticaret verilerini işleyebilecek kapasitede tasarlanmıştır.

| 📦 Analiz Edilen Ürün | 💬 İşlenen Yorum | ⭐ Ortalama Puan | 🤖 AI Özet Sayısı |
| --------------------- | ---------------- | --------------- | ----------------- |
| **1,000+**            | **3,500,000+**   | **4.53 / 5.0**  | **130+**          |

---

## 🏗️ Sistem Mimarisi

Proje, veri kazıma (scraping), işleme (processing) ve sunum (presentation) katmanlarından oluşan modüler bir yapıya sahiptir.

```mermaid
graph TD
    User[Kullanıcı] -->|Görüntüler| UI[Streamlit Dashboard]
    UI -->|İstek Atar| Backend[Data Layer]
    
    subgraph "Veri Toplama & İşleme"
    Scraper[Selenium Scraper] -->|Veri Çeker| HB[Hepsiburada]
    Scraper -->|Ham Veri| RawData[(Raw CSV)]
    RawData -->|Temizleme| Pandas[Pandas Processing]
    end
    
    subgraph "Yapay Zeka Katmanı"
    Pandas -->|Yorum Text| GPT[OpenAI GPT Modeli]
    GPT -->|Özet & Duygu Analizi| AI_Data[(Processed Data)]
    end
    
    AI_Data --> UI
```

### ⚙️ Çalışma Mantığı

1. **Link Toplama:** `product_link_scraper.py` kategori sayfalarını tarar ve nitelikli ürünleri (1000+ yorum) belirler.
2. **Veri Çekme:** Seçilen ürünlerin fiyat, puan ve yorum özetleri Selenium ile çekilir.
3. **AI Analiz:** `ai_analysis.py`, yorumları *chunk-based* (parçalı) yöntemle işler ve GPT modeline göndererek tek paragraflık stratejik özetler oluşturur.
4. **Görselleştirme:** İşlenen veriler Streamlit arayüzünde interaktif grafiklere dönüştürülür.

---

## 📂 Dosya Yapısı

```bash
ecommerce-intelligence/
├── app.py                          # 🚀 Ana uygulama (Dashboard giriş noktası)
├── requirements.txt                # Python kütüphane bağımlılıkları
├── .env                            # API Anahtarları (Git'e dahil edilmez)
├── src/
│   ├── scrapers/
│   │   ├── base_scraper.py         # Retry & Rate limiting mekanizması
│   │   └── product_link_scraper.py # Hepsiburada link toplama modülü
│   ├── ai_analysis/
│   │   └── ai_analysis.py          # GPT-3.5/4 entegrasyon servisi
│   └── config/                     # Merkezi konfigürasyon ayarları
└── data/
    ├── raw/                        # Scraper çıktısı ham veriler
    └── processed/                  # AI ve Pandas tarafından işlenmiş veriler
```

---

## ✨ Temel Özellikler

* **📈 İnteraktif Dashboard:** Fiyat dağılımı, puan analizi ve en çok yorum alan ürünlerin Plotly ile görselleştirilmesi
* **🤖 AI Destekli Yorum Analizi:** Binlerce yorumu okumak yerine yapay zeka tarafından oluşturulan “Alınır mı? / Alınmaz mı?” özetleri
* **🔍 Detaylı Filtreleme:** Fiyat aralığı, yorum sayısı ve puana göre gelişmiş filtreleme
* **⚔️ Rakip Kıyaslaması:** Best Seller ve potansiyeli düşük ürünlerin otomatik tespiti
* **🛡️ Robust Scraping:** Exponential backoff ve rate limiting ile kesintisiz veri akışı

---

## 💻 Kurulum ve Çalıştırma

### 1. Projeyi Klonlayın

```bash
git clone https://github.com/merveAiseoglu/ecommerce-intelligence-dashboard.git
cd ecommerce-intelligence-dashboard
```

### 2. Sanal Ortam Oluşturun (Önerilir)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac / Linux
source venv/bin/activate
```

### 3. Kütüphaneleri Yükleyin

```bash
pip install -r requirements.txt
```

### 4. `.env` Dosyasını Ayarlayın

```env
OPENAI_API_KEY=sk-sizin-api-keyiniz-buraya
```

### 5. Uygulamayı Başlatın

```bash
streamlit run app.py
```


## Tarayıcıda otomatik olarak `http://localhost:8501` açılır.
====


---

## 👤 Geliştirici

Bu proje **Merve Aişeoğlu** tarafından geliştirilmiştir.


* 🐙 **GitHub:** [@merveAiseoglu](https://github.com/merveAiseoglu)
* 💼 **LinkedIn:** [Profilime Git](https://www.linkedin.com/in/merve-ai%C5%9Feo%C4%9Flu-6842b71b9/)

---

<div align="center">
⭐️ Bu projeyi beğendiyseniz sağ üst köşeden <b>Star</b> vermeyi unutmayın!
</div>

---


