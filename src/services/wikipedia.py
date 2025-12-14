"""
Wikipedia API Entegrasyonu.
Vikipedi'den bilgi aramak için kullanılan servis modülü.
"""

import wikipediaapi
from typing import Dict, Any, List, Optional
import sys
import os

# Config'i import et (src klasöründen çalıştırılırsa)
try:
    from src.config import Config
except ImportError:
    # Doğrudan çalıştırılırsa
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import Config

# Wikipedia API client
wiki = wikipediaapi.Wikipedia(
    user_agent=Config.WIKI_USER_AGENT,
    language=Config.WIKI_LANGUAGE
)


def extract_sections(sections, level: int = 0) -> List[Dict[str, Any]]:
    """
    Bölümleri başlık + içerik + alt bölümler şeklinde hiyerarşik çıkarır.
    
    Args:
        sections: Wikipedia sayfa bölümleri
        level: Hiyerarşi seviyesi
        
    Returns:
        List[Dict]: Bölüm listesi
    """
    results = []
    for section in sections:
        results.append({
            "title": section.title,
            "content": section.text,
            "level": level,
            "subsections": extract_sections(section.sections, level + 1)
        })
    return results


def search_info(query: str) -> Dict[str, Any]:
    """
    Vikipedi'den sayfanın içeriklerini başlıklar halinde döndürür.
    
    Args:
        query: Aranacak konu
        
    Returns:
        Dict: Arama sonuçları veya hata mesajı
    """
    if not query or not query.strip():
        return {"query": query, "error": "Arama sorgusu boş olamaz."}
    
    query = query.strip()
    page = wiki.page(query)
    
    if not page.exists():
        return {
            "query": query, 
            "error": f"'{query}' için bilgi bulunamadı.",
            "suggestion": "Farklı anahtar kelimeler deneyebilirsiniz."
        }

    # summary + bölümler + infobox + tablolar
    data = {
        "title": page.title,
        "summary": page.summary,
        "url": page.fullurl,
        "sections": extract_sections(page.sections)
    }
    
    # InfoBox ekle (varsa)
    if hasattr(page, 'infobox') and page.infobox:
        data["infobox"] = page.infobox
    
    # Tabloları ekle (varsa)
    if hasattr(page, 'tables') and page.tables:
        data["tables"] = page.tables
    
    # Kategorileri ekle
    if hasattr(page, 'categories') and page.categories:
        data["categories"] = list(page.categories.keys())[:10]  # İlk 10 kategori
        
    return {"query": query, "result": data}


def get_function_def() -> Dict[str, Any]:
    """
    Gemini function calling için fonksiyon tanımını döndürür.
    
    Returns:
        Dict: Fonksiyon tanımı
    """
    return {
        "name": "search_info",
        "description": "Vikipedi üzerinden bilgi arar. Konuyla ilgili özet, bölümler, infobox ve tablolar döndürür.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Vikipedi'de aranacak konu veya başlık"
                }
            },
            "required": ["query"]
        }
    }


# Test için
if __name__ == "__main__":
    result = search_info("Atatürk")
    print(f"Başlık: {result.get('result', {}).get('title', 'Bulunamadı')}")
    print(f"Özet: {result.get('result', {}).get('summary', 'Yok')[:200]}...")
