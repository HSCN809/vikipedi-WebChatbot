"""
Flask Web Uygulaması - Vikipedi Chatbot.
SSE streaming destekli Gemini tabanlı sohbet asistanı.
"""

import os
import sys

# src klasörünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, send_from_directory
from flask_cors import CORS

# Route'ları import et
try:
    from src.routes.chat_routes import chat_bp
    from src.config import Config
except ImportError:
    from routes.chat_routes import chat_bp
    from config import Config

# Flask uygulamasını başlat
app = Flask(
    __name__,
    template_folder='../templates',
    static_folder='../static'
)

# CORS ayarları
CORS(app)

# Config ayarları
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Blueprint'leri kaydet
app.register_blueprint(chat_bp)


@app.route('/')
def index():
    """Ana sayfa - index.html'i render eder."""
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


@app.route('/health')
def health_check():
    """Sağlık kontrolü endpoint'i."""
    return {"status": "healthy", "version": "2.0.0"}


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Statik dosyaları serve eder."""
    return send_from_directory(app.static_folder, filename)


# Ana çalıştırma bloğu
if __name__ == "__main__":
    print("🚀 Chatbot başlatılıyor...")
    print(f"🔗 http://{Config.HOST}:{Config.PORT} adresinde çalışacak")
    
    # API key kontrolü
    if not Config.validate():
        print("⚠️ Yapılandırma doğrulaması başarısız!")
    
    # Debug modunda çalıştır
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
