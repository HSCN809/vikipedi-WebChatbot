from flask import Flask, request, Response, jsonify, render_template
from chatbot import WebChatbot
import json
import traceback
import os

# Flask uygulamasını başlat
app = Flask(__name__)

# Her sohbet için ayrı chatbot instance'ları tut (chat_id: WebChatbot)
chatbot_instances = {}


# Ana sayfa route'u - index.html'i render eder
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Chatbot Hatası</title></head>
        <body>
            <h1>Template Hatası: {str(e)}</h1>
            <p>templates/index.html dosyasını kontrol edin.</p>
        </body>
        </html>
        """


# Chat endpoint'i - kullanıcı mesaj gönderir, SSE ile yanıt döner
@app.route('/chat', methods=['POST'])
def chat():
    try:
        # JSON verisini al
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON verisi bulunamadı'}), 400

        # Kullanıcı mesajını al ve boş mu kontrol et
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Mesaj boş olamaz'}), 400

        # Frontend'den chat_id'yi al (her sohbet için ayrı geçmiş tutmak için)
        chat_id = data.get('chat_id', 'default')
        
        # Bu sohbet için chatbot yoksa yeni bir tane oluştur
        if chat_id not in chatbot_instances:
            chatbot_instances[chat_id] = WebChatbot()
            print(f"🆕 Yeni chatbot oluşturuldu: {chat_id}")
        
        # İlgili sohbetin chatbot'unu al
        chatbot = chatbot_instances[chat_id]
        
        print(f"📝 Kullanıcı mesajı (Chat: {chat_id}): {user_message}")

        # Streaming response generator - parça parça yanıt gönderir
        def generate():
            try:
                # Chatbot'tan streaming yanıt al
                for chunk in chatbot.chat_stream(user_message):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

                # Stream sonu bildirimi
                yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"

            except Exception as e:
                # Hata durumunda hata mesajı gönder
                error_chunk = {
                    'type': 'error',
                    'error': str(e),
                    'trace': traceback.format_exc()
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

        # SSE (Server-Sent Events) response döndür
        return Response(generate(),
                       mimetype='text/event-stream',
                       headers={
                           'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive',
                           'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'POST',
                           'Access-Control-Allow-Headers': 'Content-Type'
                       })

    except Exception as e:
        error_msg = f"Server hatası: {str(e)}"
        print("🔥 Flask hatası:", traceback.format_exc())
        return jsonify({'error': error_msg}), 500


# Belirli bir sohbetin geçmişini sıfırlama endpoint'i
@app.route('/reset', methods=['POST'])
def reset_chat():
    try:
        data = request.get_json()
        chat_id = data.get('chat_id', 'default') if data else 'default'
        
        # Eğer bu sohbet için chatbot varsa geçmişini sıfırla
        if chat_id in chatbot_instances:
            chatbot_instances[chat_id].reset_history()
            print(f"🔄 Sohbet geçmişi sıfırlandı: {chat_id}")
        else:
            # Yoksa yeni bir chatbot oluştur
            chatbot_instances[chat_id] = WebChatbot()
            print(f"🆕 Yeni chatbot oluşturuldu (reset): {chat_id}")

        return jsonify({'status': 'ok', 'message': 'Sohbet geçmişi temizlendi'})
    
    except Exception as e:
        print("🔥 Reset hatası:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# Belirli bir sohbeti tamamen sil (memory'den temizle)
@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        
        if not chat_id:
            return jsonify({'error': 'chat_id gerekli'}), 400
        
        # Eğer bu sohbet için chatbot varsa memory'den sil
        if chat_id in chatbot_instances:
            del chatbot_instances[chat_id]
            print(f"🗑️ Sohbet silindi: {chat_id}")
        
        return jsonify({'status': 'ok', 'message': 'Sohbet silindi'})
    
    except Exception as e:
        print("🔥 Delete hatası:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# Ana çalıştırma bloğu
if __name__ == "__main__":
    print("🚀 Chatbot başlatılıyor...")
    print("🔗 http://127.0.0.1:5000 adresinde çalışacak")

    # API key kontrolü - GEMINI için
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️ GEMINI_API_KEY bulunamadı! .env dosyasını kontrol edin.")

    # Flask uygulamasını başlat (debug mode açık, tüm IP'lerden erişilebilir)
    app.run(debug=True, host="0.0.0.0", port=5000)