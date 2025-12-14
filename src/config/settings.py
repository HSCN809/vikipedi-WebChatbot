"""
Uygulama yapılandırma ayarları.
Tüm konfigürasyon değerleri burada merkezi olarak yönetilir.
"""

import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()


class Config:
    """Ana yapılandırma sınıfı."""
    
    # Gemini API Ayarları
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    
    # Chatbot Ayarları
    MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "15"))
    MAX_CHATBOT_INSTANCES: int = int(os.getenv("MAX_INSTANCES", "100"))
    STREAM_CHUNK_SIZE: int = int(os.getenv("STREAM_CHUNK_SIZE", "3"))
    
    # Flask Ayarları
    DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Calculator Ayarları
    CALC_MAX_LEN: int = int(os.getenv("CALC_MAX_LEN", "200"))
    CALC_MAX_OPERATORS: int = int(os.getenv("CALC_MAX_OPERATORS", "60"))
    CALC_MAX_EXPONENT: int = int(os.getenv("CALC_MAX_EXPONENT", "6"))
    
    # Wikipedia Ayarları
    WIKI_USER_AGENT: str = os.getenv("WIKI_USER_AGENT", "vikipedi-chatbot/1.0")
    WIKI_LANGUAGE: str = os.getenv("WIKI_LANGUAGE", "tr")
    
    @classmethod
    def validate(cls) -> bool:
        """Gerekli yapılandırmaları doğrular."""
        if not cls.GEMINI_API_KEY:
            print("⚠️ GEMINI_API_KEY bulunamadı! .env dosyasını kontrol edin.")
            return False
        return True
    
    @classmethod
    def to_dict(cls) -> dict:
        """Yapılandırmayı dictionary olarak döndürür (hassas bilgiler hariç)."""
        return {
            "GEMINI_MODEL": cls.GEMINI_MODEL,
            "MAX_HISTORY": cls.MAX_HISTORY,
            "MAX_CHATBOT_INSTANCES": cls.MAX_CHATBOT_INSTANCES,
            "DEBUG": cls.DEBUG,
            "HOST": cls.HOST,
            "PORT": cls.PORT,
            "WIKI_LANGUAGE": cls.WIKI_LANGUAGE,
        }
