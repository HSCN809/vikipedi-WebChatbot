import os
import json
import traceback
import google.generativeai as genai
from dotenv import load_dotenv

# services klasöründen import
from services import calculator, search

# Ortam değişkenlerini yükle (.env)
load_dotenv()

# Gemini client başlat
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class WebChatbot:
    def __init__(self):
        # Başlangıç sistem mesajı (asistanın rolünü tanımlar)
        self.system_prompt = """Sen yardımcı bir asistansın. Kullanıcının sorularını yanıtla, gerektiğinde hesaplama yap ve Wikipedia'dan bilgi ara.

ÖNEMLI: Cevaplarını mutlaka Markdown formatında ver. Şu kuralları takip et:

- Başlıklar için # ## ### kullan
- Önemli metinler için **kalın** yazı kullan
- Listeler için - veya 1. kullan
- Kod parçaları için `kod` veya ```kod bloğu``` kullan
- Bölümleri net başlıklarla ayır
- Uzun cevaplarda alt başlıklar kullan
"""

        # Sohbet geçmişini başlat
        self.history = []
        self.messages = []

        # Kullanıcıya ait ek veriler
        self.user_data = {
            "calculations": [],
            "notes": [],
        }

        # Maksimum tutulacak mesaj sayısı (kayan pencere)
        self.MAX_HISTORY = 15

        # Gemini modelini başlat
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    # Fonksiyon tanımlarını döndürür (hesaplama ve arama)
    def get_tools(self):
        return [
            {
                "function_declarations": [calculator.get_function_def()]
            },
            {
                "function_declarations": [search.get_function_def()]
            }
        ]

    # Sohbet geçmişini sıfırlar (kullanıcı "geçmişi temizle" dediğinde kullanılabilir)
    def reset_history(self):
        self.history = []
        self.messages = []

    # Mesaj geçmişini kısaltır
    def _get_limited_history(self):
        return self.messages[-self.MAX_HISTORY:]

    # Kullanıcı mesajını işler ve modeli stream halinde çağırır
    def chat_stream(self, user_message):
        try:
            # Kullanıcı mesajını geçmişe ekle
            self.messages.append({"role": "user", "parts": [{"text": user_message}]})
            print(f"📝 Kullanıcı mesajı: {user_message}")

            # Gemini'yi çağır
            chat = self.model.start_chat(history=self._get_limited_history())
            
            # Tools/fonksiyonları ekle
            response = chat.send_message(
                user_message,
                tools=self.get_tools(),
                stream=True
            )

            full_content = ""
            function_calls = []

            # Response'u stream et
            for chunk in response:
                if chunk.candidates and chunk.candidates[0].content:
                    content = chunk.candidates[0].content.parts[0].text
                    if content:
                        full_content += content
                        yield {"type": "content", "content": content}
                
                # Fonksiyon çağrılarını kontrol et
                if (chunk.candidates and chunk.candidates[0].content and 
                    chunk.candidates[0].content.parts and 
                    hasattr(chunk.candidates[0].content.parts[0], 'function_call')):
                    
                    function_call = chunk.candidates[0].content.parts[0].function_call
                    fn_name = function_call.name
                    args = {k: v for k, v in function_call.args.items()}
                    
                    function_calls.append((fn_name, args))
                    yield {"type": "function_call", "function": fn_name, "args": args}

            # Fonksiyon çağrılarını işle
            if function_calls:
                for fn_name, args in function_calls:
                    print(f"🔧 Fonksiyon çağrısı: {fn_name} - {args}")
                    
                    # Fonksiyonları çalıştır
                    if fn_name == "search_info":
                        result = search.search_info(**args)
                    elif fn_name == "calculate":
                        result = calculator.calculate(**args, user_data=self.user_data)
                    else:
                        result = {"error": f"Bilinmeyen fonksiyon: {fn_name}"}
                    
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

                    # Follow-up response'u stream et
                    follow_up_content = ""
                    for follow_chunk in follow_up_response:
                        if follow_chunk.candidates and follow_chunk.candidates[0].content:
                            content = follow_chunk.candidates[0].content.parts[0].text
                            if content:
                                follow_up_content += content
                                yield {"type": "content", "content": content}

                    # Asistan cevabını geçmişe ekle
                    if follow_up_content:
                        self.messages.append({"role": "model", "parts": [{"text": follow_up_content}]})
            else:
                # Normal cevabı geçmişe ekle (fonksiyon çağrısı yoksa)
                if full_content:
                    self.messages.append({"role": "model", "parts": [{"text": full_content}]})

            # Stream sonu
            yield {"type": "end"}

        except Exception as e:
            print("🔥 chat_stream hatası:", traceback.format_exc())
            yield {"type": "error", "error": str(e), "trace": traceback.format_exc()}