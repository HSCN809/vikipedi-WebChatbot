"""
Web Chatbot - Gemini Tabanlı Sohbet Yönetimi.
Wikipedia entegrasyonlu AI asistan.
"""

import os
import traceback
import time
from typing import Generator, Dict, Any, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()

# Servisleri import et
try:
    from src.services import calculator, wikipedia
    from src.config import Config
except ImportError:
    # Doğrudan çalıştırılırsa eski import'ları kullan
    from services import calculator
    from services import search as wikipedia
    
    class Config:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        GEMINI_MODEL = "models/gemini-2.5-flash"
        MAX_HISTORY = 15
        STREAM_CHUNK_SIZE = 3

# Gemini client başlat
genai.configure(api_key=Config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY"))

# Sistem prompt'u
SYSTEM_PROMPT = """Sen Wikipedia entegrasyonlu uzman bir asistansın. ChatGPT gibi net, anlaşılır ve doğrudan cevaplar ver.

**CEVAP FORMATI KURALLARI:**

📚 **Vikipedi Entegrasyonu:**
- Wikipedia bilgilerini özetle ve düzenle
- Karmaşık bilgileri basitleştir
- Kaynak göstermek için [1], [2] gibi referanslar kullan
- Bilgileri güncel ve doğru tut

🎯 **Yapılandırma:**
- Konuyu mantıklı bölümlere ayır
- Ana başlıklar için ##, alt başlıklar için ### kullan
- Önemli tarihleri ve isimleri **kalın** ile vurgula
- Listeler için • kullan
- Kronolojik sıraya dikkat et

💬 **Konuşma Tarzı:**
- Bilgilendirici ama sıkmayan
- Akademik dilden kaçın, anlaşılır ol
- Gereksiz detaylarla boğma
- Önemli noktaları öne çıkar

🔍 **Araştırma Yaklaşımı:**
- Kullanıcının ihtiyacına göre detay seviyesini ayarla
- Temel bilgilerle başla, detaylara in
- Karşılaştırmalı analiz yap
- Bağlam içinde açıkla

❌ **YAPMA:**
- ❌ Kaynaksız bilgi verme
- ❌ Yorum ve kişisel görüş katma
"""


class WebChatbot:
    """
    Gemini tabanlı web chatbot sınıfı.
    Wikipedia araması ve hesaplama özelliklerini destekler.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Chatbot'u başlatır.
        
        Args:
            model_name: Kullanılacak Gemini model adı (opsiyonel)
        """
        self.system_prompt = SYSTEM_PROMPT
        self.messages: List[Dict[str, Any]] = []
        self.user_data: Dict[str, Any] = {
            "calculations": [],
            "notes": [],
        }
        self.max_history = Config.MAX_HISTORY
        self.chunk_size = Config.STREAM_CHUNK_SIZE
        
        # Gemini modelini başlat
        model = model_name or Config.GEMINI_MODEL
        self.model = genai.GenerativeModel(model)
        
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Fonksiyon tanımlarını döndürür.
        
        Returns:
            List[Dict]: Tool tanımları listesi
        """
        # Hangi modülün kullanıldığını kontrol et
        try:
            calc_def = calculator.get_function_def()
        except AttributeError:
            from services.calculator import get_function_def as get_calc_def
            calc_def = get_calc_def()
            
        try:
            search_def = wikipedia.get_function_def()
        except AttributeError:
            from services.search import get_function_def as get_search_def
            search_def = get_search_def()
        
        return [
            {"function_declarations": [calc_def]},
            {"function_declarations": [search_def]}
        ]

    def reset_history(self) -> None:
        """Sohbet geçmişini sıfırlar."""
        self.messages = []
        self.user_data = {"calculations": [], "notes": []}

    def _get_limited_history(self) -> List[Dict[str, Any]]:
        """
        Kısaltılmış mesaj geçmişini döndürür.
        
        Returns:
            List[Dict]: Son N mesaj
        """
        return self.messages[-self.max_history:]

    def _stream_text_char_by_char(self, text: str) -> Generator[Dict[str, str], None, None]:
        """
        Metni küçük parçalar halinde yield eder.
        
        Args:
            text: Parçalanacak metin
            
        Yields:
            Dict: Content chunk'ları
        """
        for i in range(0, len(text), self.chunk_size):
            yield {"type": "content", "content": text[i:i + self.chunk_size]}
            time.sleep(0.01)

    def _execute_function(self, fn_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fonksiyon çağrısını yürütür.
        
        Args:
            fn_name: Fonksiyon adı
            args: Fonksiyon argümanları
            
        Returns:
            Dict: Fonksiyon sonucu
        """
        try:
            if fn_name == "search_info":
                try:
                    return wikipedia.search_info(**args)
                except AttributeError:
                    from services.search import search_info
                    return search_info(**args)
                    
            elif fn_name == "calculate":
                try:
                    return calculator.calculate(**args, user_data=self.user_data)
                except AttributeError:
                    from services.calculator import calculate
                    return calculate(**args, user_data=self.user_data)
            else:
                return {"error": f"Bilinmeyen fonksiyon: {fn_name}"}
                
        except Exception as e:
            return {"error": f"Fonksiyon hatası: {str(e)}"}

    def chat_stream(self, user_message: str) -> Generator[Dict[str, Any], None, None]:
        """
        Kullanıcı mesajını işler ve streaming yanıt döndürür.
        
        Args:
            user_message: Kullanıcının gönderdiği mesaj
            
        Yields:
            Dict: Streaming chunk'ları
        """
        try:
            # Kullanıcı mesajını geçmişe ekle
            self.messages.append({
                "role": "user", 
                "parts": [{"text": user_message}]
            })
            print(f"📝 Kullanıcı mesajı: {user_message}")

            # Gemini'yi çağır
            chat = self.model.start_chat(history=self._get_limited_history())
            
            response = chat.send_message(
                user_message,
                tools=self.get_tools(),
                stream=True
            )

            full_content = ""
            function_calls = []
            accumulated_text = ""

            # Response'u stream et
            for chunk in response:
                if chunk.candidates and chunk.candidates[0].content:
                    parts = chunk.candidates[0].content.parts
                    if parts and hasattr(parts[0], 'text'):
                        content = parts[0].text
                        if content:
                            full_content += content
                            accumulated_text += content
                            
                            if len(accumulated_text) >= 10:
                                for stream_chunk in self._stream_text_char_by_char(accumulated_text):
                                    yield stream_chunk
                                accumulated_text = ""
                
                # Fonksiyon çağrılarını kontrol et
                if (chunk.candidates and 
                    chunk.candidates[0].content and 
                    chunk.candidates[0].content.parts and 
                    hasattr(chunk.candidates[0].content.parts[0], 'function_call')):
                    
                    function_call = chunk.candidates[0].content.parts[0].function_call
                    fn_name = function_call.name
                    
                    if hasattr(function_call, 'args') and function_call.args:
                        args = {k: v for k, v in function_call.args.items()}
                    else:
                        args = {}
                    
                    function_calls.append((fn_name, args))
                    yield {"type": "function_call", "function": fn_name, "args": args}

            # Kalan text'i gönder
            if accumulated_text:
                for stream_chunk in self._stream_text_char_by_char(accumulated_text):
                    yield stream_chunk

            # Fonksiyon çağrılarını işle
            if function_calls:
                for fn_name, args in function_calls:
                    if not fn_name:
                        print("⚠️ Boş fonksiyon ismi, atlanıyor...")
                        continue
                    
                    print(f"🔧 Fonksiyon çağrısı: {fn_name} - {args}")
                    result = self._execute_function(fn_name, args)
                    yield {"type": "function_result", "result": result}

                    # Fonksiyon sonucunu geçmişe ekle
                    self.messages.append({
                        "role": "function",
                        "parts": [{
                            "function_response": {
                                "name": fn_name,
                                "response": result
                            }
                        }]
                    })

                    # Fonksiyon sonucu ile tekrar çağır
                    follow_up_response = chat.send_message(
                        f"Fonksiyon sonucu: {result}",
                        stream=True
                    )

                    follow_up_content = ""
                    follow_up_accumulated = ""
                    
                    for follow_chunk in follow_up_response:
                        if follow_chunk.candidates and follow_chunk.candidates[0].content:
                            parts = follow_chunk.candidates[0].content.parts
                            if parts and hasattr(parts[0], 'text'):
                                content = parts[0].text
                                if content:
                                    follow_up_content += content
                                    follow_up_accumulated += content
                                    
                                    if len(follow_up_accumulated) >= 10:
                                        for stream_chunk in self._stream_text_char_by_char(follow_up_accumulated):
                                            yield stream_chunk
                                        follow_up_accumulated = ""
                    
                    if follow_up_accumulated:
                        for stream_chunk in self._stream_text_char_by_char(follow_up_accumulated):
                            yield stream_chunk

                    if follow_up_content:
                        self.messages.append({
                            "role": "model", 
                            "parts": [{"text": follow_up_content}]
                        })
            else:
                if full_content:
                    self.messages.append({
                        "role": "model", 
                        "parts": [{"text": full_content}]
                    })

            yield {"type": "end"}

        except Exception as e:
            print("🔥 chat_stream hatası:", traceback.format_exc())
            yield {"type": "error", "error": str(e), "trace": traceback.format_exc()}


# Test için
if __name__ == "__main__":
    chatbot = WebChatbot()
    print("Chatbot başlatıldı. Test için mesaj gönderin.")
