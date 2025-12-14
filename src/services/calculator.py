"""
Güvenli Hesaplama Servisi.
Matematiksel ifadeleri güvenli bir şekilde hesaplar.
"""

import re
from typing import Dict, Any, Optional
import numexpr as ne
import sys
import os

# Config'i import et
try:
    from src.config import Config
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import Config


# Sabitler
MAX_LEN = Config.CALC_MAX_LEN
MAX_OPERATORS = Config.CALC_MAX_OPERATORS
MAX_EXPONENT_DIGITS = Config.CALC_MAX_EXPONENT

# İzin verilen karakterler regex'i
ALLOWED_CHARS_RE = re.compile(r'^[0-9+\-*/().\s]+$')


def calculate(expression: str, user_data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Güvenli matematiksel hesaplama (numexpr kullanır).
    
    Args:
        expression: Hesaplanacak matematik ifadesi
        user_data: Kullanıcı verilerini saklamak için optional dict
        
    Returns:
        Dict: Hesaplama sonucu veya hata mesajı
    """
    expr = (expression or "").strip()

    # Basit uzunluk kontrolü
    if not expr:
        return {"error": "İfade boş olamaz."}
    
    if len(expr) > MAX_LEN:
        return {"error": f"İfade çok uzun (maksimum {MAX_LEN} karakter)."}

    # İzin verilen karakterler kontrolü (harf/alt çizgi vs. engellenir)
    if not ALLOWED_CHARS_RE.match(expr):
        return {"error": "Geçersiz karakter; sadece sayılar ve aritmetik operatörlere izin verilir."}

    # Operatör sayısı kontrolü (aşırı karmaşık ifadeleri engellemek için)
    operator_count = sum(expr.count(op) for op in ['+', '-', '*', '/', '(', ')', '.'])
    if operator_count > MAX_OPERATORS:
        return {"error": f"İfade çok karmaşık (maksimum {MAX_OPERATORS} operatör)."}

    # Çok büyük üs (exponent) girişlerini sınırlama
    for m in re.finditer(r'\*\*\s*(\d+)', expr):
        exp_digits = len(m.group(1))
        if exp_digits > MAX_EXPONENT_DIGITS:
            return {"error": f"Üs kısmı çok büyük (maksimum {MAX_EXPONENT_DIGITS} basamak)."}
        try:
            if int(m.group(1)) > 10000:
                return {"error": "Üs değeri çok büyük (maksimum 10000)."}
        except Exception:
            return {"error": "Üs ifadesi hatalı."}

    # Ek güvenlik: ardışık operatörlerin aşırı tekrarını engelle
    if re.search(r'[\+\-*/]{5,}', expr):
        return {"error": "Aşırı operatör tekrarı tespit edildi."}

    try:
        # numexpr ile hesapla
        result = ne.evaluate(expr)

        # numexpr numpy scalar/array döndürebilir - scalar değeri elde et
        value = _extract_scalar_value(result)
        if value is None:
            return {"error": "Sonuç işlenirken hata oluştu."}

        # Python tipine çevir
        py_value = _to_python_type(value)

        calculation = {
            "expression": expression, 
            "result": py_value,
            "formatted": _format_result(py_value)
        }

        # Kullanıcı verilerine ekle
        if isinstance(user_data, dict):
            user_data.setdefault("calculations", []).append(calculation)

        return calculation

    except ZeroDivisionError:
        return {"error": "Sıfıra bölme hatası."}
    except Exception as e:
        return {"error": f"Hesaplama hatası: {str(e)}"}


def _extract_scalar_value(result) -> Optional[float]:
    """Numpy sonucundan scalar değer çıkarır."""
    try:
        return result.item()
    except Exception:
        try:
            import numpy as np
            arr = np.array(result)
            if arr.size == 1:
                return arr.flatten()[0].item()
            return None
        except Exception:
            return None


def _to_python_type(value) -> float:
    """Değeri Python tipine çevirir."""
    try:
        if isinstance(value, (float, int)):
            return value
        return float(value)
    except Exception:
        return value


def _format_result(value: float) -> str:
    """Sonucu okunabilir formatta döndürür."""
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}".replace(",", ".")
        return f"{value:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(value)


def get_function_def() -> Dict[str, Any]:
    """
    Gemini function calling için fonksiyon tanımını döndürür.
    
    Returns:
        Dict: Fonksiyon tanımı
    """
    return {
        "name": "calculate",
        "description": "Matematik hesaplaması yapar. Toplama, çıkarma, çarpma, bölme ve parantez destekler.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Hesaplanacak matematik ifadesi (örn: '5*(12+3)/2')"
                }
            },
            "required": ["expression"]
        }
    }


# Test için
if __name__ == "__main__":
    test_cases = [
        "5+3",
        "10*5+2",
        "100/4",
        "(5+3)*2",
        "2**10",
    ]
    
    for expr in test_cases:
        result = calculate(expr)
        print(f"{expr} = {result.get('result', result.get('error'))}")
