import os
import json
import traceback
from openai import OpenAI
from dotenv import load_dotenv

# services klasöründen import
from services import calculator, search

# Ortam değişkenlerini yükle (.env)
load_dotenv()

# OpenAI client başlat
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class WebChatbot:
    def __init__(self):
        # Başlangıç sistem mesajı (asistanın rolünü tanımlar)
        self.system_prompt = {
            "role": "system",
            "content": """Sen yardımcı bir asistansın. Kullanıcının sorularını yanıtla, gerektiğinde hesaplama yap ve Wikipedia'dan bilgi ara.

ÖNEMLI: Cevaplarını mutlaka Markdown formatında ver. Şu kuralları takip et:

- Başlıklar için # ## ### kullan
- Önemli metinler için **kalın** yazı kullan
- Listeler için - veya 1. kullan
- Kod parçaları için `kod` veya ```kod bloğu``` kullan
- Bölümleri net başlıklarla ayır
- Uzun cevaplarda alt başlıklar kullan
"""
        }

        # Sohbet geçmişini başlat (sadece sistem mesajı ile)
        self.messages = [self.system_prompt]

        # Kullanıcıya ait ek veriler
        self.user_data = {
            "calculations": [],
            "notes": [],
        }

        # Maksimum tutulacak mesaj sayısı (kayan pencere)
        self.MAX_HISTORY = 15

    # Fonksiyon tanımlarını döndürür (hesaplama ve arama)
    def get_functions(self):
        return [
            calculator.get_function_def(),
            search.get_function_def()
        ]

    # Sohbet geçmişini sıfırlar (kullanıcı "geçmişi temizle" dediğinde kullanılabilir)
    def reset_history(self):
        self.messages = [self.system_prompt]

    # Mesaj geçmişini kısaltır (sadece sistem mesajı + son N mesaj)
    def _get_limited_history(self):
        # Sistem mesajını koru, sadece son N mesajı ekle
        return [self.system_prompt] + self.messages[-self.MAX_HISTORY:]

    # Kullanıcı mesajını işler ve modeli stream halinde çağırır
    def chat_stream(self, user_message):
        try:
            # Kullanıcı mesajını geçmişe ekle
            self.messages.append({"role": "user", "content": user_message})
            print(f"📝 Kullanıcı mesajı: {user_message}")

            # Modeli çağırırken sadece sınırlı geçmişi gönder
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self._get_limited_history(),
                functions=self.get_functions(),
                function_call="auto"
            )

            message = response.choices[0].message

            # Fonksiyon çağrısı var mı kontrol et
            if hasattr(message, 'function_call') and message.function_call:
                fn_name = message.function_call.name
                args = json.loads(message.function_call.arguments)

                print(f"🔧 Fonksiyon çağrısı: {fn_name} - {args}")
                yield {"type": "function_call", "function": fn_name, "args": args}

                # Fonksiyonları çalıştır
                if fn_name == "search_info":
                    result = search.search_info(**args)
                    yield {"type": "function_result", "result": result}

                elif fn_name == "calculate":
                    result = calculator.calculate(**args, user_data=self.user_data)
                    yield {"type": "function_result", "result": result}

                # Fonksiyon sonucunu geçmişe ekle
                self.messages.append({
                    "role": "function",
                    "name": fn_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })

                # Streaming cevap al
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self._get_limited_history(),
                    stream=True
                )

                full_content = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_content += content
                        yield {"type": "content", "content": content}

                # Tam cevabı geçmişe ekle
                self.messages.append({"role": "assistant", "content": full_content})

            else:
                # Normal cevap (fonksiyon çağrısı yok)
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self._get_limited_history(),
                    stream=True
                )

                full_content = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_content += content
                        yield {"type": "content", "content": content}

                # Tam cevabı geçmişe ekle
                self.messages.append({"role": "assistant", "content": full_content})

            # Stream sonu
            yield {"type": "end"}

        except Exception as e:
            print("🔥 chat_stream hatası:", traceback.format_exc())
            yield {"type": "error", "error": str(e), "trace": traceback.format_exc()}
