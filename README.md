# 🧠 Wikipedia Chatbot – AI Destekli Bilgi Asistanı

Bu proje, **Google Gemini 2.5 Flash** modeliyle çalışan, **Flask** tabanlı bir web uygulamasıdır.
Kullanıcılar, 3D görselli bir web arayüzü üzerinden Türkçe veya İngilizce olarak Vikipedi'den bilgi sorgulayabilir, matematiksel hesaplamalar yapabilir ve sonuçları gerçek zamanlı (streaming) olarak görebilir.

---

## 📋 Genel Özellikler

* **Wikipedia entegrasyonu:** Doğrudan Vikipedi API'sinden özet, başlık ve tablo bilgilerini çeker.
* **Matematik motoru:** Güvenli `numexpr` temelli hesaplama desteği içerir; kullanıcıdan gelen ifadeleri doğrular ve değerlendirir.
* **Gerçek zamanlı yanıt akışı:** `Server-Sent Events (SSE)` ile model çıktısı parça parça kullanıcıya iletilir.
* **Chat geçmişi yönetimi:** Her sohbet için ayrı kimlik (`chat_id`) ve bellek tutulur.
* **Modern 3D arayüz:** HTML/CSS/JS ile geliştirilmiş interaktif ve animasyonlu tasarım.
* **Markdown çıktısı:** Model yanıtları başlıklar, listeler, kod blokları ve vurgu biçimleriyle biçimlendirilir.
* **Function Calling:** Gemini'nin native function calling özelliği ile Wikipedia araması ve hesaplama.

---

## 🧩 Proje Yapısı

```
VIKIPEDI-WEBCHATBOT/
│
├── src/                     # Kaynak kod
│   ├── app.py               # Flask sunucusu (SSE ve endpoint'ler)
│   ├── chatbot.py           # Gemini tabanlı sohbet mantığı
│   │
│   ├── services/            # Alt servisler
│   │   ├── __init__.py
│   │   ├── wikipedia.py     # Wikipedia API entegrasyonu
│   │   └── calculator.py    # Güvenli hesaplama fonksiyonları
│   │
│   ├── routes/              # API endpoint'leri
│   │   ├── __init__.py
│   │   └── chat_routes.py
│   │
│   └── config/              # Yapılandırma
│       ├── __init__.py
│       └── settings.py
│
├── static/                  # Statik dosyalar
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── main.js
│
├── templates/               # HTML şablonları
│   └── index.html           # 3D web arayüzü (frontend)
│
├── tests/                   # Test dosyaları
│   ├── __init__.py
│   ├── test_calculator.py
│   └── test_wikipedia.py
│
├── .env.example             # Örnek ortam değişkenleri
├── .gitattributes           # Git yapılandırması
├── .gitignore               # Gereksiz dosyaların hariç tutulması
├── requirements.txt         # Bağımlılıklar
├── run.py                   # Uygulama başlatma noktası
└── README.md                # Bu doküman
```

---

## ⚙️ Gereksinimler

Yüklenecek temel kütüphaneler:

```bash
pip install -r requirements.txt
```

`requirements.txt` içeriği:

```
# Web Framework
flask>=3.0.0
flask-cors>=4.0.0

# AI/LLM
google-generativeai>=0.8.0

# Wikipedia
wikipedia-api>=0.6.0

# Utilities
python-dotenv>=1.0.0
requests>=2.31.0
numexpr>=2.8.0
```

Ek olarak, oluşturacağınız `.env` dosyasında Gemini API anahtarınızı belirtin:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🚀 Uygulamayı Çalıştırma

```bash
python run.py
```

veya doğrudan:

```bash
python src/app.py
```

Başlatıldığında terminalde:

```
🚀 Chatbot başlatılıyor...
🔗 http://127.0.0.1:5000 adresinde çalışacak
```

Tarayıcıda açarak etkileşimli arayüze ulaşabilirsiniz:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 💬 Kullanım

1. Tarayıcıda uygulamayı açın.
2. Sol panelden **Yeni Sohbet** oluşturun.
3. Mesaj kutusuna bir konu yazın:

   * "Atatürk hakkında bilgi ver."
   * "5*(12+3)^2 hesapla."
4. Yanıtlar model tarafından Markdown biçiminde ve parça parça (streaming) olarak gösterilir.
5. Sohbetler tarayıcı LocalStorage'da saklanır; sıfırlama veya silme işlemleri arayüzden yapılabilir.

---

## 🧠 Teknik Akış

* **Frontend (`templates/index.html`)** – Kullanıcı mesajlarını `/chat` endpoint'ine gönderir ve SSE ile stream'i okur.
* **Backend (`src/app.py`)** – Flask, her sohbet için `WebChatbot` nesnesi oluşturur ve yanıt akışını yönetir.
* **Chatbot Mantığı (`src/chatbot.py`)** –

  * Gemini modeliyle konuşma geçmişini işler,
  * Function calling ile `search_info()` veya `calculate()` fonksiyonlarını çağırır.
* **services/wikipedia.py & services/calculator.py** –

  * `search_info()` → Wikipedia'dan veri toplar,
  * `calculate()` → Güvenli matematik hesaplaması yapar.

---

## 🧩 Güvenlik & Sınırlamalar

* `calculator.py` yalnızca sayısal karakterleri ve basit operatörleri kabul eder; aşırı uzun ifadeleri veya büyük üs değerlerini engeller.
* `wikipedia.py`, yalnızca var olan Vikipedi sayfalarını döndürür ve gereksiz ağ isteklerini sınırlar.
* API anahtarı `.env` dosyasında gizli tutulmalıdır.
* Rate limiting ile API istekleri sınırlandırılmıştır.

---

## 🧰 Teknolojiler

| Katman      | Teknoloji                                       |
| ----------- | ----------------------------------------------- |
| Backend     | Flask, Google Gemini API, Python                |
| AI Model    | Gemini 2.5 Flash                                |
| Bilgi       | Wikipedia-API                                   |
| Hesaplama   | NumExpr                                         |
| Frontend    | HTML5, CSS3 (3D animasyonlu arayüz), JavaScript |
| Formatlama  | Markdown Rendering (Marked.js)                  |

---

## 🔧 Geliştirme

### Test Çalıştırma

```bash
python -m pytest tests/ -v
```

### Kod Formatı

```bash
black src/
flake8 src/
```
