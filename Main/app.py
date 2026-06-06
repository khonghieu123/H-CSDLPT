import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

sys.stdout.reconfigure(encoding='utf-8')

# Import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from search import search_similar_birds, search_birdnet

app = Flask(__name__)
CORS(app)

# Cấu hình thư mục
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "Frontend")
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
TEMP_DIR = os.path.join(PROJECT_ROOT, "temp")

os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/')
def index():
    """Phục vụ file HTML giao diện chính"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_frontend_static(filename):
    """Phục vụ các file tĩnh (CSS, JS) của frontend"""
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Phục vụ các file âm thanh từ thư mục raw data"""
    return send_from_directory(DATA_RAW_DIR, filename)

@app.route('/search', methods=['POST'])
def search():
    """API endpoint xử lý tìm kiếm âm thanh (MFCC + BirdNET)"""
    if 'query_audio' not in request.files:
        return jsonify({"error": "Không tìm thấy file âm thanh"}), 400
        
    file = request.files['query_audio']
    method = request.form.get('method', 'mfcc')
    
    if file.filename == '':
        return jsonify({"error": "Tên file rỗng"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        temp_path = os.path.join(TEMP_DIR, filename)
        file.save(temp_path)
        
        try:
            import time
            start_time = time.time()
            
            if method == 'birdnet':
                # === TÌM KIẾM NÂNG CAO BIRDNET ===
                # Hàm search_birdnet trả về dict có sẵn latency, results,
                # extraction_time_ms, search_time_ms
                result_data = search_birdnet(temp_path, top_k=5)
                return jsonify(result_data)
            else:
                # === TÌM KIẾM CƠ BẢN MFCC ===
                results = search_similar_birds(temp_path, top_k=5)
                latency = int((time.time() - start_time) * 1000)
                return jsonify({
                    "latency": latency,
                    "results": results
                })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Tắt debug=True để server không bị restart khi có file âm thanh mới được upload vào thư mục temp
    app.run(port=5000)
