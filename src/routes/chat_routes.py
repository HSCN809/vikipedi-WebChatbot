"""
Chat API Route'ları.
Tüm chat ile ilgili endpoint'ler burada tanımlı.
"""

from flask import Blueprint, request, Response, jsonify
import json
import traceback
from typing import Dict, Any

# Blueprint oluştur
chat_bp = Blueprint('chat', __name__)

# Chatbot instance'larını tutan dictionary
chatbot_instances: Dict[str, Any] = {}

# Maksimum instance sayısı
MAX_INSTANCES = 100


def get_chatbot_class():
    """WebChatbot sınıfını lazy import eder."""
    from src.chatbot import WebChatbot
    return WebChatbot


def cleanup_old_instances():
    """
    Eski chatbot instance'larını temizler.
    Memory leak'i önlemek için maksimum instance sayısını kontrol eder.
    """
    global chatbot_instances
    if len(chatbot_instances) > MAX_INSTANCES:
        # En eski instance'ları sil (ilk eklenenler)
        keys_to_remove = list(chatbot_instances.keys())[:len(chatbot_instances) - MAX_INSTANCES]
        for key in keys_to_remove:
            del chatbot_instances[key]
            print(f"🧹 Eski chatbot temizlendi: {key}")


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint'i - kullanıcı mesaj gönderir, SSE ile yanıt döner.
    
    Request Body:
        - message: str - Kullanıcı mesajı
        - chat_id: str - Sohbet kimliği (opsiyonel)
        
    Returns:
        SSE stream veya JSON hata
    """
    try:
        # JSON verisini al
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON verisi bulunamadı'}), 400

        # Kullanıcı mesajını al ve boş mu kontrol et
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Mesaj boş olamaz'}), 400

        # Frontend'den chat_id'yi al
        chat_id = data.get('chat_id', 'default')
        
        # Eski instance'ları temizle
        cleanup_old_instances()
        
        # Bu sohbet için chatbot yoksa yeni bir tane oluştur
        WebChatbot = get_chatbot_class()
        if chat_id not in chatbot_instances:
            chatbot_instances[chat_id] = WebChatbot()
            print(f"🆕 Yeni chatbot oluşturuldu: {chat_id}")
        
        # İlgili sohbetin chatbot'unu al
        chatbot = chatbot_instances[chat_id]
        
        print(f"📝 Kullanıcı mesajı (Chat: {chat_id}): {user_message}")

        # Streaming response generator
        def generate():
            try:
                for chunk in chatbot.chat_stream(user_message):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"

            except Exception as e:
                error_chunk = {
                    'type': 'error',
                    'error': str(e),
                    'trace': traceback.format_exc()
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"

        # SSE response döndür
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )

    except Exception as e:
        error_msg = f"Server hatası: {str(e)}"
        print("🔥 Chat hatası:", traceback.format_exc())
        return jsonify({'error': error_msg}), 500


@chat_bp.route('/reset', methods=['POST'])
def reset_chat():
    """
    Belirli bir sohbetin geçmişini sıfırlar.
    
    Request Body:
        - chat_id: str - Sohbet kimliği
        
    Returns:
        JSON status
    """
    try:
        data = request.get_json()
        chat_id = data.get('chat_id', 'default') if data else 'default'
        
        WebChatbot = get_chatbot_class()
        if chat_id in chatbot_instances:
            chatbot_instances[chat_id].reset_history()
            print(f"🔄 Sohbet geçmişi sıfırlandı: {chat_id}")
        else:
            chatbot_instances[chat_id] = WebChatbot()
            print(f"🆕 Yeni chatbot oluşturuldu (reset): {chat_id}")

        return jsonify({'status': 'ok', 'message': 'Sohbet geçmişi temizlendi'})
    
    except Exception as e:
        print("🔥 Reset hatası:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/delete_chat', methods=['POST'])
def delete_chat():
    """
    Belirli bir sohbeti tamamen siler (memory'den temizle).
    
    Request Body:
        - chat_id: str - Sohbet kimliği
        
    Returns:
        JSON status
    """
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        
        if not chat_id:
            return jsonify({'error': 'chat_id gerekli'}), 400
        
        if chat_id in chatbot_instances:
            del chatbot_instances[chat_id]
            print(f"🗑️ Sohbet silindi: {chat_id}")
        
        return jsonify({'status': 'ok', 'message': 'Sohbet silindi'})
    
    except Exception as e:
        print("🔥 Delete hatası:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Aktif sohbet istatistiklerini döndürür.
    
    Returns:
        JSON: Aktif sohbet sayısı ve diğer istatistikler
    """
    return jsonify({
        'active_chats': len(chatbot_instances),
        'max_instances': MAX_INSTANCES,
        'chat_ids': list(chatbot_instances.keys())
    })
