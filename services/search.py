import wikipediaapi

wiki = wikipediaapi.Wikipedia(
    user_agent="kairu-llm-chatbot/0.1",
    language="tr"
)

def extract_sections(sections, level=0):
    """Bölümleri başlık + içerik + alt bölümler şeklinde hiyerarşik çıkarır."""
    results = []
    for section in sections:
        results.append({
            "title": section.title,
            "content": section.text,
            "subsections": extract_sections(section.sections, level + 1)
        })
    return results

def search_info(query):
    """Vikipedi'den sayfanın içeriklerini başlıklar halinde döndürür."""
    page = wiki.page(query)
    if not page.exists():
        return {"query": query, "result": f"'{query}' için bilgi bulunamadı."}

    # summary + bölümler + infobox + tablolar
    data = {
        "summary": page.summary,
        "sections": extract_sections(page.sections)
    }
    
    # InfoBox ekle
    if hasattr(page, 'infobox') and page.infobox:
        data["infobox"] = page.infobox
    
    # Tabloları ekle
    if hasattr(page, 'tables') and page.tables:
        data["tables"] = page.tables
        
    return {"query": query, "result": data}

def get_function_def():
    return {
        "name": "search_info",
        "description": "Vikipedi üzerinden bilgi arar (içerik + infobox + tablolar)",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Aranacak konu"
                }
            },
            "required": ["query"]
        }
    }