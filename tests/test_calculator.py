"""
Calculator Service Tests.
Hesaplama servisinin birim testleri.
"""

import pytest
import sys
import os

# src klasörünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.calculator import calculate, get_function_def


class TestCalculate:
    """calculate fonksiyonu için testler."""
    
    def test_simple_addition(self):
        """Basit toplama işlemi."""
        result = calculate("5+3")
        assert result["result"] == 8
        assert "error" not in result
    
    def test_subtraction(self):
        """Çıkarma işlemi."""
        result = calculate("10-3")
        assert result["result"] == 7
    
    def test_multiplication(self):
        """Çarpma işlemi."""
        result = calculate("4*5")
        assert result["result"] == 20
    
    def test_division(self):
        """Bölme işlemi."""
        result = calculate("20/4")
        assert result["result"] == 5.0
    
    def test_complex_expression(self):
        """Karmaşık ifade."""
        result = calculate("(5+3)*2")
        assert result["result"] == 16
    
    def test_decimal_result(self):
        """Ondalık sonuç."""
        result = calculate("10/3")
        assert abs(result["result"] - 3.333333) < 0.001
    
    def test_empty_expression(self):
        """Boş ifade hatası."""
        result = calculate("")
        assert "error" in result
        assert "boş" in result["error"].lower()
    
    def test_none_expression(self):
        """None ifade hatası."""
        result = calculate(None)
        assert "error" in result
    
    def test_invalid_characters(self):
        """Geçersiz karakterler."""
        result = calculate("5+a")
        assert "error" in result
        assert "Geçersiz karakter" in result["error"]
    
    def test_expression_too_long(self):
        """Çok uzun ifade."""
        long_expr = "1+" * 150 + "1"
        result = calculate(long_expr)
        assert "error" in result
        assert "uzun" in result["error"].lower()
    
    def test_too_many_operators(self):
        """Çok fazla operatör."""
        expr = "+".join(["1"] * 100)
        result = calculate(expr)
        assert "error" in result
    
    def test_exponent_limit(self):
        """Üs limiti."""
        result = calculate("2**100000000")
        assert "error" in result
        assert "üs" in result["error"].lower()
    
    def test_consecutive_operators(self):
        """Ardışık operatörler."""
        result = calculate("5+++++3")
        assert "error" in result
    
    def test_parentheses(self):
        """Parantez kullanımı."""
        result = calculate("((5+3)*(2+1))")
        assert result["result"] == 24
    
    def test_user_data_storage(self):
        """Kullanıcı verisi saklama."""
        user_data = {"calculations": []}
        calculate("5+3", user_data)
        assert len(user_data["calculations"]) == 1
        assert user_data["calculations"][0]["result"] == 8
    
    def test_formatted_result(self):
        """Formatlanmış sonuç."""
        result = calculate("1000+234")
        assert "formatted" in result


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
        assert func_def["name"] == "calculate"
    
    def test_has_description(self):
        """description alanı olmalı."""
        func_def = get_function_def()
        assert "description" in func_def
    
    def test_has_parameters(self):
        """parameters alanı olmalı."""
        func_def = get_function_def()
        assert "parameters" in func_def
        assert "properties" in func_def["parameters"]
        assert "expression" in func_def["parameters"]["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
