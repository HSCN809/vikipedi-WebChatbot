#!/usr/bin/env python
"""
Vikipedi Chatbot - Ana Çalıştırma Noktası.
Bu dosyayı çalıştırarak uygulamayı başlatabilirsiniz.
"""

import sys
import os

# Proje kök dizinini path'e ekle
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.app import app
from src.config import Config


def main():
    """Uygulamayı başlatır."""
    print("=" * 50)
    print("🧠 Vikipedi Chatbot - AI Destekli Bilgi Asistanı")
    print("=" * 50)
    print()
    
    # Yapılandırmayı göster
    print("📋 Yapılandırma:")
    for key, value in Config.to_dict().items():
        print(f"   {key}: {value}")
    print()
    
    # API key kontrolü
    if not Config.validate():
        print("=" * 50)
        print("⚠️  Lütfen .env dosyasını oluşturun ve GEMINI_API_KEY ekleyin!")
        print("📄 Örnek için .env.example dosyasına bakın.")
        print("=" * 50)
        return
    
    print("🚀 Sunucu başlatılıyor...")
    print(f"🔗 http://{Config.HOST}:{Config.PORT}")
    print()
    print("Ctrl+C ile durdurmak için.")
    print("=" * 50)
    
    # Flask uygulamasını başlat
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )


if __name__ == "__main__":
    main()
