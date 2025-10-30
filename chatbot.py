import os
import json
import traceback
import google.generativeai as genai
from dotenv import load_dotenv
import time

# services klasöründen import
from services import calculator, search

# Ortam değişkenlerini yükle (.env)
load_dotenv()

# Gemini client başlat
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class WebChatbot:
    def __init__(self):
        # Başlangıç sistem mesajı (asistanın rolünü tanımlar)
        self.system_prompt = """Sen Wikipedia entegrasyonlu uzman bir asistansın. ChatGPT gibi net, anlaşılır ve doğrudan cevaplar ver.

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

        # Sohbet geçmişini başlat
        self.messages = []

        # Kullanıcıya ait ek veriler
        self.user_data = {
            "calculations": [],
            "notes": [],
        }

        # Maksimum tutulacak mesaj sayısı (kayan pencere)
        self.MAX_HISTORY = 15

        # Gemini modelini başlat
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')

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
        self.messages = []

    # Mesaj geçmişini kısaltır
    def _get_limited_history(self):
        return self.messages[-self.MAX_HISTORY:]

    # Harf harf streaming için yardımcı fonksiyon
    def _stream_text_char_by_char(self, text, chunk_size=3):
        """Metni küçük parçalar halinde yield eder"""
        for i in range(0, len(text), chunk_size):
            yield {"type": "content", "content": text[i:i+chunk_size]}
            time.sleep(0.01)  # Daha akıcı görünmesi için küçük delay

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
            accumulated_text = ""

            # Response'u stream et - karakter karakter işle
            for chunk in response:
                if chunk.candidates and chunk.candidates[0].content:
                    # Text content kontrolü
                    if hasattr(chunk.candidates[0].content.parts[0], 'text'):
                        content = chunk.candidates[0].content.parts[0].text
                        if content:
                            full_content += content
                            accumulated_text += content
                            
                            # Küçük parçalar halinde gönder
                            if len(accumulated_text) >= 10:  # 10 karakterde bir gönder
                                for stream_chunk in self._stream_text_char_by_char(accumulated_text):
                                    yield stream_chunk
                                accumulated_text = ""
                
                # Fonksiyon çağrılarını kontrol et
                if (chunk.candidates and chunk.candidates[0].content and 
                    chunk.candidates[0].content.parts and 
                    hasattr(chunk.candidates[0].content.parts[0], 'function_call')):
                    
                    function_call = chunk.candidates[0].content.parts[0].function_call
                    fn_name = function_call.name
                    
                    # Args None kontrolü
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
                    # Fonksiyon ismi boşsa veya None'sa atla
                    if not fn_name:
                        print("⚠️ Boş fonksiyon ismi, atlanıyor...")
                        continue
            
                    print(f"🔧 Fonksiyon çağrısı: {fn_name} - {args}")
                    
                    # Fonksiyonları çalıştır
                    try:
                        if fn_name == "search_info":
                            result = search.search_info(**args)
                        elif fn_name == "calculate":
                            result = calculator.calculate(**args, user_data=self.user_data)
                        else:
                            result = {"error": f"Bilinmeyen fonksiyon: {fn_name}"}
                            yield {"type": "function_result", "result": result}
                            continue
                
                        yield {"type": "function_result", "result": result}
                    
                    except Exception as func_error:
                        result = {"error": f"Fonksiyon hatası: {str(func_error)}"}
                        yield {"type": "function_result", "result": result}
                        continue

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
                    follow_up_accumulated = ""
                    
                    for follow_chunk in follow_up_response:
                        if follow_chunk.candidates and follow_chunk.candidates[0].content:
                            if hasattr(follow_chunk.candidates[0].content.parts[0], 'text'):
                                content = follow_chunk.candidates[0].content.parts[0].text
                                if content:
                                    follow_up_content += content
                                    follow_up_accumulated += content
                                    
                                    # Küçük parçalar halinde gönder
                                    if len(follow_up_accumulated) >= 10:
                                        for stream_chunk in self._stream_text_char_by_char(follow_up_accumulated):
                                            yield stream_chunk
                                        follow_up_accumulated = ""
                    
                    # Kalan follow-up text'i gönder
                    if follow_up_accumulated:
                        for stream_chunk in self._stream_text_char_by_char(follow_up_accumulated):
                            yield stream_chunk

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