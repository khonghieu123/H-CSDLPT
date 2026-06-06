import os

# 0. TẮT CẢNH BÁO RÁC CỦA HỆ THỐNG
# Giúp màn hình Terminal của em sạch sẽ và chuyên nghiệp khi báo cáo
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

import numpy as np
import librosa
import tensorflow as tf
from database import get_connection

# ==========================================
# 1. CẤU HÌNH ĐƯỜNG DẪN & TẢI MÔ HÌNH (ĐÃ FIX LỖI TIẾNG VIỆT)
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite")

if not os.path.exists(MODEL_PATH):
    print(f"[!] LỖI CHÍ MẠNG: Không tìm thấy file tại {MODEL_PATH}")
    exit()

print("[*] Đang khởi động lõi AI BirdNET...")

# Đọc file thành Byte để che mắt lõi C++ của TensorFlow, tránh lỗi thư mục "Hệ CSDLDPT"
with open(MODEL_PATH, "rb") as f:
    model_bytes = f.read()
     

interpreter = tf.lite.Interpreter(
    model_content=model_bytes, 
    experimental_preserve_all_tensors=True
)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# ==========================================
# 2. CỖ MÁY ÉP CỬA SỔ TRƯỢT (SLIDING WINDOW)
# ==========================================
def extract_birdnet_vector(file_path):
    """Băm file thành các đoạn 3s, ép qua BirdNET và đập bẹp thành 1024 chiều"""
    try:
        # BirdNET khắt khe: Bắt buộc 48000 Hz, 1 Kênh
        y, sr = librosa.load(file_path, sr=48000, mono=True)
        y_trimmed, _ = librosa.effects.trim(y)
        
        if len(y_trimmed) == 0: 
            return None
            
        chunk_length = 3 * 48000  # 3 giây = 144.000 tọa độ sóng âm
        embeddings_list = []
        
        # Băm thịt: Trượt từ đầu đến cuối file âm thanh
        for i in range(0, len(y_trimmed), chunk_length):
            chunk = y_trimmed[i : i + chunk_length]
            
            # Bù số 0 nếu khúc cuối cùng ngắn hơn 3 giây
            if len(chunk) < chunk_length:
                chunk = np.pad(chunk, (0, chunk_length - len(chunk)))
                
            # Ép khúc 3s này qua mạng nơ-ron
            input_data = np.array([chunk], dtype=np.float32)
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()
            
            # Chọc vào index áp chót để rút vector ngữ nghĩa 1024 chiều
            embedding_index = output_details[0]['index'] - 1
            vector_1024 = interpreter.get_tensor(embedding_index)[0]
            
            embeddings_list.append(vector_1024)
            
        # Gộp trung bình toàn bộ các khúc lại thành 1 mảng 1024 duy nhất
        final_vector = np.mean(embeddings_list, axis=0)
        return final_vector.tolist()

    except Exception as e:
        print(f"  [!] Lỗi trích xuất file {file_path}: {e}")
        return None

# ==========================================
# 3. QUÉT DATABASE VÀ UPDATE
# ==========================================
def run_ai_ingestion():
    conn = get_connection()
    if not conn: return
    
    try:
        cursor = conn.cursor()
        
        # Chỉ lấy những file chưa được AI xử lý (birdnet_vector = NULL)
        cursor.execute("SELECT id, file_path FROM bird_songs WHERE birdnet_vector IS NULL ORDER BY id ASC;")
        rows = cursor.fetchall()
        total_files = len(rows)
        
        if total_files == 0:
            print("[v] Kho dữ liệu đã cập nhật đầy đủ Vector AI 1024 chiều!")
            return
            
        print(f"[*] Tìm thấy {total_files} files cần ép AI. Bắt đầu xử lý...")
        success_count = 0
        
        for idx, row in enumerate(rows, 1):
            record_id = row[0]
            file_path = os.path.join(PROJECT_ROOT, row[1])
            
            print(f"[{idx}/{total_files}] Đang chạy Deep Learning: {os.path.basename(file_path)}")
            
            birdnet_vec = extract_birdnet_vector(file_path)
            
            if birdnet_vec is not None:
                # Update mảng 1024 số ngược lại vào dòng chứa file đó
                update_query = "UPDATE bird_songs SET birdnet_vector = %s WHERE id = %s;"
                cursor.execute(update_query, (birdnet_vec, record_id))
                conn.commit()
                success_count += 1
                
        print(f"\n[HOÀN THÀNH] Đã luyện thành công {success_count}/{total_files} vector 1024 chiều vào PostgreSQL.")
        
    except Exception as e:
        print(f"[!] Lỗi cơ sở dữ liệu: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_ai_ingestion()