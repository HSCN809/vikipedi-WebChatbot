# calculator.py
import re
import numexpr as ne

MAX_LEN = 200
MAX_OPERATORS = 60
MAX_EXPONENT_DIGITS = 6  # üs kısmındaki rakam sayısı bu limitin üstündeyse reddet
ALLOWED_CHARS_RE = re.compile(r'^[0-9+\-*/().\s]+$')

def calculate(expression, user_data=None):
    """Güvenli matematiksel hesaplama (numexpr kullanır)."""
    expr = (expression or "").strip()

    # Basit uzunluk kontrolü
    if not expr:
        return {"error": "İfade boş olamaz."}
    if len(expr) > MAX_LEN:
        return {"error": "İfade çok uzun."}

    # İzin verilen karakterler kontrolü (harf/alt çizgi vs. engellenir)
    if not ALLOWED_CHARS_RE.match(expr):
        return {"error": "Geçersiz karakter; sadece sayılar ve aritmetik operatörlere izin verilir."}

    # Operatör sayısı kontrolü (aşırı karmaşık ifadeleri engellemek için)
    operator_count = sum(expr.count(op) for op in ['+', '-', '*', '/', '(', ')', '.'])
    if operator_count > MAX_OPERATORS:
        return {"error": "İfade çok karmaşık veya uzun operatör dizisi içeriyor."}

    # Çok büyük üs (exponent) girişlerini sınırlama: '**' ile takip eden rakam sayısını kontrol et
    # (numexpr '**' destekler - burası basit bir koruma sağlar)
    for m in re.finditer(r'\*\*\s*(\d+)', expr):
        exp_digits = len(m.group(1))
        if exp_digits > MAX_EXPONENT_DIGITS:
            return {"error": "Üs kısmı çok büyük; daha küçük bir değer kullanın."}
        try:
            # ayrıca çok büyük bir üs değeri varsa reddet (örn. 10**100000)
            if int(m.group(1)) > 10000:
                return {"error": "Üs değeri çok büyük; daha küçük bir değer kullanın."}
        except Exception:
            return {"error": "Üs ifadesi hatalı."}

    # Ek güvenlik: ardışık operatörlerin aşırı tekrarını engelle (ör. '+++++')
    if re.search(r'[\+\-*/]{5,}', expr):
        return {"error": "Aşırı operatör tekrarı tespit edildi."}

    try:
        # numexpr ile hesapla
        result = ne.evaluate(expr)

        # numexpr numpy scalar/array döndürebilir - scalar değeri elde et
        try:
            value = result.item()  # numpy scalar ise
        except Exception:
            # eğer array dönmüşse ve tek elemanlıysa onu çek; aksi halde hata ver
            try:
                import numpy as _np
                arr = _np.array(result)
                if arr.size == 1:
                    value = arr.flatten()[0].item()
                else:
                    return {"error": "Çoklu sonuç içeren ifadeler desteklenmiyor."}
            except Exception:
                return {"error": "Sonuç işlenirken hata oluştu."}

        # Python tipine çevir (ör. numpy types -> native)
        try:
            if isinstance(value, (float, int)):
                py_value = value
            else:
                py_value = float(value)
        except Exception:
            py_value = value

        calculation = {"expression": expression, "result": py_value}

        if isinstance(user_data, dict):
            user_data.setdefault("calculations", []).append(calculation)

        return calculation

    except Exception as e:
        # Hata mesajını kullanıcıya çok detaylı vermemek güvenlik açısından iyidir,
        # fakat geliştirme aşamasında hata detayını loglamak faydalıdır.
        return {"error": f"Hesaplama hatası: {str(e)}"}


def get_function_def():
    return {
        "name": "calculate",
        "description": "Matematik hesaplaması yapar",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Hesaplanacak matematik ifadesi"
                }
            },
            "required": ["expression"]
        }
    }
