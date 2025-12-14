"""
Wikipedia Service Tests.
Wikipedia servisinin birim testleri.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# src klasörünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.wikipedia import search_info, get_function_def, extract_sections


class TestSearchInfo:
    """search_info fonksiyonu için testler."""
    
    def test_empty_query(self):
        """Boş sorgu hatası."""
        result = search_info("")
        assert "error" in result
        assert "boş" in result["error"].lower()
    
    def test_whitespace_query(self):
        """Sadece boşluk sorgu hatası."""
        result = search_info("   ")
        assert "error" in result
    
    def test_query_stripped(self):
        """Sorgunun trim edilmesi."""
        # Bu test mock ile yapılmalı gerçek API çağrısından kaçınmak için
        with patch('src.services.wikipedia.wiki') as mock_wiki:
            mock_page = MagicMock()
            mock_page.exists.return_value = False
            mock_wiki.page.return_value = mock_page
            
            result = search_info("  test  ")
            assert result["query"] == "test"
    
    def test_page_not_found(self):
        """Sayfa bulunamadı durumu."""
        with patch('src.services.wikipedia.wiki') as mock_wiki:
            mock_page = MagicMock()
            mock_page.exists.return_value = False
            mock_wiki.page.return_value = mock_page
            
            result = search_info("nonexistent_page_12345")
            assert "error" in result
            assert "bulunamadı" in result["error"]
    
    def test_successful_search(self):
        """Başarılı arama."""
        with patch('src.services.wikipedia.wiki') as mock_wiki:
            mock_page = MagicMock()
            mock_page.exists.return_value = True
            mock_page.title = "Test Title"
            mock_page.summary = "Test summary content"
            mock_page.fullurl = "https://tr.wikipedia.org/wiki/Test"
            mock_page.sections = []
            mock_wiki.page.return_value = mock_page
            
            result = search_info("Test")
            assert "result" in result
            assert result["result"]["title"] == "Test Title"
            assert result["result"]["summary"] == "Test summary content"
    
    def test_result_structure(self):
        """Sonuç yapısı kontrolü."""
        with patch('src.services.wikipedia.wiki') as mock_wiki:
            mock_page = MagicMock()
            mock_page.exists.return_value = True
            mock_page.title = "Test"
            mock_page.summary = "Summary"
            mock_page.fullurl = "https://example.com"
            mock_page.sections = []
            mock_wiki.page.return_value = mock_page
            
            result = search_info("Test")
            data = result["result"]
            
            assert "title" in data
            assert "summary" in data
            assert "url" in data
            assert "sections" in data


class TestExtractSections:
    """extract_sections fonksiyonu için testler."""
    
    def test_empty_sections(self):
        """Boş bölümler."""
        result = extract_sections([])
        assert result == []
    
    def test_single_section(self):
        """Tek bölüm."""
        mock_section = MagicMock()
        mock_section.title = "Section 1"
        mock_section.text = "Content 1"
        mock_section.sections = []
        
        result = extract_sections([mock_section])
        assert len(result) == 1
        assert result[0]["title"] == "Section 1"
        assert result[0]["content"] == "Content 1"
        assert result[0]["level"] == 0
    
    def test_nested_sections(self):
        """İç içe bölümler."""
        mock_subsection = MagicMock()
        mock_subsection.title = "Subsection"
        mock_subsection.text = "Sub content"
        mock_subsection.sections = []
        
        mock_section = MagicMock()
        mock_section.title = "Section"
        mock_section.text = "Content"
        mock_section.sections = [mock_subsection]
        
        result = extract_sections([mock_section])
        assert len(result) == 1
        assert len(result[0]["subsections"]) == 1
        assert result[0]["subsections"][0]["level"] == 1


class TestGetFunctionDef:
    """get_function_def fonksiyonu için testler."""
    
    def test_returns_dict(self):
        """Dictionary döndürmeli."""
        func_def = get_function_def()
        assert isinstance(func_def, dict)
    
    def test_has_name(self):
        """name alanı olmalı."""
        func_def = get_function_def()
        assert "name" in func_def
        assert func_def["name"] == "search_info"
    
    def test_has_description(self):
        """description alanı olmalı."""
        func_def = get_function_def()
        assert "description" in func_def
        assert "Vikipedi" in func_def["description"]
    
    def test_has_parameters(self):
        """parameters alanı olmalı."""
        func_def = get_function_def()
        assert "parameters" in func_def
        assert "properties" in func_def["parameters"]
        assert "query" in func_def["parameters"]["properties"]
    
    def test_query_required(self):
        """query parametresi required olmalı."""
        func_def = get_function_def()
        assert "required" in func_def["parameters"]
        assert "query" in func_def["parameters"]["required"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
