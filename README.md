# 🧠 Wikipedia Chatbot – AI Destekli Bilgi Asistanı

Bu proje, **OpenAI GPT-4o-mini** modeliyle çalışan, **Flask** tabanlı bir web uygulamasıdır.
Kullanıcılar, 3D görselli bir web arayüzü üzerinden Türkçe veya İngilizce olarak Vikipedi’den bilgi sorgulayabilir, matematiksel hesaplamalar yapabilir ve sonuçları gerçek zamanlı (streaming) olarak görebilir.

---

## 📋 Genel Özellikler

* **Wikipedia entegrasyonu:** Doğrudan Vikipedi API’sinden özet, başlık ve tablo bilgilerini çeker.
* **Matematik motoru:** Güvenli `numexpr` temelli hesaplama desteği içerir; kullanıcıdan gelen ifadeleri doğrular ve değerlendirir.
* **Gerçek zamanlı yanıt akışı:** `Server-Sent Events (SSE)` ile model çıktısı parça parça kullanıcıya iletilir.
* **Chat geçmişi yönetimi:** Her sohbet için ayrı kimlik (`chat_id`) ve bellek tutulur.
* **Modern 3D arayüz:** HTML/CSS/JS ile geliştirilmiş interaktif ve animasyonlu tasarım.
* **Markdown çıktısı:** Model yanıtları başlıklar, listeler, kod blokları ve vurgu biçimleriyle biçimlendirilir.

---

## 🧩 Proje Yapısı

```
VIKIPEDI-WEBCHATBOT/
│
├── services/            # Alt servisler (search, calculator)
│   ├── search.py         # Wikipedia API entegrasyonu
│   └── calculator.py     # Güvenli hesaplama fonksiyonları
│
├── templates/           # HTML şablonları
│   └── index.html        # 3D web arayüzü (frontend)
│
├── .gitattributes        # Git yapılandırması
├── .gitignore            # Gereksiz dosyaların hariç tutulması
├── app.py                # Flask sunucusu (SSE ve endpoint’ler)
├── chatbot.py            # GPT-4o-mini tabanlı sohbet mantığı
├── requirements.txt      # Bağımlılıklar
└── README.md             # Bu doküman
```

---

## ⚙️ Gereksinimler

Yüklenecek temel kütüphaneler:

```bash
pip install -r requirements.txt
```

`requirements.txt` içeriği:

```
flask
openai
python-dotenv
wikipedia-api
requests
numexpr
```

Ek olarak, oluşturacağınız `.env` dosyasında OpenAI anahtarınızı belirtin:

```
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 🚀 Uygulamayı Çalıştırma

```bash
python app.py
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

   * “Atatürk hakkında bilgi ver.”
   * “5*(12+3)^2 hesapla.”
4. Yanıtlar model tarafından Markdown biçiminde ve parça parça (streaming) olarak gösterilir.
5. Sohbetler tarayıcı LocalStorage’da saklanır; sıfırlama veya silme işlemleri arayüzden yapılabilir.

---

## 🧠 Teknik Akış

* **Frontend (`index.html`)** – Kullanıcı mesajlarını `/chat` endpoint’ine gönderir ve SSE ile stream’i okur.
* **Backend (`app.py`)** – Flask, her sohbet için `WebChatbot` nesnesi oluşturur ve yanıt akışını yönetir.
* **Chatbot Mantığı (`chatbot.py`)** –

  * OpenAI modeliyle konuşma geçmişini işler,
  * Gerekirse `search_info()` veya `calculate()` fonksiyonlarını çağırır.
* **services/search.py & services/calculator.py** –

  * `search_info()` → Wikipedia’dan veri toplar,
  * `calculate()` → Güvenli matematik hesaplaması yapar.

---

## 🧩 Güvenlik & Sınırlamalar

* `calculator.py` yalnızca sayısal karakterleri ve basit operatörleri kabul eder; aşırı uzun ifadeleri veya büyük üs değerlerini engeller.
* `search.py`, yalnızca var olan Vikipedi sayfalarını döndürür ve gereksiz ağ isteklerini sınırlar.
* API anahtarı `.env` dosyasında gizli tutulmalıdır.

---

## 🧰 Teknolojiler

| Katman      | Teknoloji                                       |
| ----------- | ----------------------------------------------- |
| Backend     | Flask, OpenAI API, Python                       |
| Bilgi       | Wikipedia-API                                   |
| Hesaplama   | NumExpr                                         |
| Frontend    | HTML5, CSS3 (3D animasyonlu arayüz), JavaScript |
| Formatlama  | Markdown Rendering (Marked.js)                  |
