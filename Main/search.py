import os
import sys
import time
import numpy as np
from database import get_connection
from feature_extraction import extract_mfcc_vector
from update_ai_vectors import extract_birdnet_vector

# Ép hệ thống dùng UTF-8 cho print để tránh lỗi charmap trên Windows
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN HỆ THỐNG
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

def search_similar_birds(query_file_path, top_k=5):
    """
    Hàm tìm kiếm Top K file âm thanh giống nhất trong CSDL.
    """
    print(f"\n[*] BƯỚC 1: Đang phân tích file truy vấn: {os.path.basename(query_file_path)}")
    # 1. Ép file truy vấn thành Vector 20 chiều
    query_vector = extract_mfcc_vector(query_file_path)
    
    if query_vector is None:
        print("[!] Lỗi: Không thể trích xuất đặc trưng từ file truy vấn.")
        return []

    print("[*] BƯỚC 2: Đang quét không gian Vector trong PostgreSQL...")
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        
        # 2. Lệnh SQL tìm kiếm siêu tốc bằng pgvector
        # Toán tử <=> dùng để tính khoảng cách Cosine (Cosine Distance).
        search_query = """
            SELECT species_name, file_path, (mfcc_vector <=> %s) as cosine_distance
            FROM bird_songs
            WHERE mfcc_vector IS NOT NULL
            ORDER BY cosine_distance ASC
            LIMIT %s;
        """
        
        # Đóng gói vector thành Numpy Array để driver chuyển xuống DB
        query_np = np.array(query_vector)
        
        # Thực thi truy vấn
        cursor.execute(search_query, (query_np, top_k))
        results = cursor.fetchall()
        
        output_data = []
        
        # 3. Hiển thị và trả về kết quả
        print(f"\n=== KẾT QUẢ TÌM KIẾM (TOP {top_k}) ===")
        for idx, row in enumerate(results, 1):
            species = row[0]
            path = row[1]
            distance = row[2]
            
            # Khoảng cách Cosine chạy từ 0 đến 2. 0 là giống hệt nhau.
            # Chuyển đổi thành % độ tương đồng (Similarity) cho dễ nhìn
            similarity = (1 - distance) * 100
            filename = os.path.basename(path)
            
            # Tách ID từ tên file (Ví dụ: acridotheres_grandis_133769.mp3 -> XC133769)
            parts = filename.replace('.mp3', '').split('_')
            bird_id = f"XC{parts[-1]}" if parts[-1].isdigit() else f"XC{idx}"
            
            # Format tên khoa học
            formatted_species = species.replace('_', ' ').capitalize()
            
            # Tạo dictionary kết quả khớp với Frontend
            item = {
                "id": bird_id,
                "species": formatted_species,
                "common_name": formatted_species, # Tạm dùng tên khoa học làm tên thông thường
                "similarity": round(similarity, 1),
                "audio_url": f"/audio/{filename}" # Đường dẫn để Frontend gọi xuống Backend lấy file
            }
            output_data.append(item)
            
            print(f"{idx}. Loài: {species:<25} | Độ giống: {similarity:>5.2f}% | File: {filename}")
            
        return output_data
            
    except Exception as e:
        print(f"[!] Lỗi khi truy vấn CSDL: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# ==========================================
# TÌM KIẾM NÂNG CAO BẰNG BIRDNET AI (1024 CHIỀU)
# Dựa trên cấu trúc từ test_ai.py
# ==========================================
def search_birdnet(query_file_path, top_k=5):
    """
    Hàm tìm kiếm Top K file âm thanh giống nhất bằng BirdNET Deep Learning.
    Sử dụng vector 1024 chiều từ mô hình BirdNET_GLOBAL_6K_V2.4.
    """
    print(f"\n[*] BIRDNET - BƯỚC 1: Đang ép AI cho file truy vấn: {os.path.basename(query_file_path)}")
    
    start_ext = time.time()
    
    # 1. Ép file MP3 thành 1 vector 1024 chiều qua mô hình BirdNET
    query_vector = extract_birdnet_vector(query_file_path)
    
    extraction_time = time.time() - start_ext
    
    if query_vector is None:
        print("[!] Lỗi: Không thể trích xuất đặc trưng BirdNET từ file truy vấn.")
        return {"extraction_time_ms": 0, "search_time_ms": 0, "results": []}
    
    print(f"[v] Ép xong! (Thời gian: {extraction_time:.2f}s)")
    
    # 2. Gửi lệnh xuống DB qua đường cao tốc HNSW
    print("[*] BIRDNET - BƯỚC 2: Đang quét không gian Vector 1024 chiều trong PostgreSQL...")
    
    conn = get_connection()
    if not conn:
        return {"extraction_time_ms": 0, "search_time_ms": 0, "results": []}
    
    try:
        cursor = conn.cursor()
        
        # Truy vấn SQL giống hệt test_ai.py:
        # Dùng toán tử <=> (Cosine Distance) trên cột birdnet_vector
        # Tính similarity = (1 - cosine_distance) * 100
        sql = """
            SELECT id, file_path, species_name,
                   (1 - (birdnet_vector <=> %s::vector)) * 100 AS similarity
            FROM bird_songs
            WHERE birdnet_vector IS NOT NULL
            ORDER BY birdnet_vector <=> %s::vector ASC
            LIMIT %s;
        """
        
        start_search = time.time()
        # Truyền query_vector 2 lần vì trong SQL có 2 dấu %s cho vector
        cursor.execute(sql, (query_vector, query_vector, top_k))
        results = cursor.fetchall()
        search_time = time.time() - start_search
        
        # 3. Format kết quả cho Frontend (cùng cấu trúc với search_similar_birds)
        output_data = []
        
        print(f"\n=== KẾT QUẢ TÌM KIẾM BIRDNET (1024 Chiều) ===")
        print(f"Thời gian ép AI: {extraction_time*1000:.2f} ms")
        print(f"Thời gian quét DB: {search_time*1000:.2f} ms\n")
        
        for rank, row in enumerate(results, 1):
            record_id = row[0]
            file_path = row[1]
            species = row[2] if row[2] else "Unknown"
            similarity = row[3]
            
            filename = os.path.basename(file_path)
            
            # Tách ID từ tên file (Ví dụ: acridotheres_grandis_133769.mp3 -> XC133769)
            parts = filename.replace('.mp3', '').split('_')
            bird_id = f"XC{parts[-1]}" if parts[-1].isdigit() else f"XC{record_id}"
            
            # Format tên khoa học
            formatted_species = species.replace('_', ' ').capitalize()
            
            item = {
                "id": bird_id,
                "species": formatted_species,
                "common_name": formatted_species,  # Tạm dùng tên khoa học
                "similarity": round(similarity, 2),
                "audio_url": f"/audio/{filename}"
            }
            output_data.append(item)
            
            print(f"Top #{rank} | Độ tương đồng: {similarity:.2f}% | File: {filename}")
        
        return {
            "extraction_time_ms": int(extraction_time * 1000),
            "search_time_ms": int(search_time * 1000),
            "latency": int((extraction_time + search_time) * 1000),
            "results": output_data
        }
        
    except Exception as e:
        print(f"[!] Lỗi khi truy vấn BirdNET trong CSDL: {e}")
        return {"extraction_time_ms": 0, "search_time_ms": 0, "latency": 0, "results": []}
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_query_file = os.path.join(PROJECT_ROOT, "data", "raw", "acridotheres_grandis_133769.mp3")
    
    if os.path.exists(test_query_file):
        search_similar_birds(test_query_file)
    else:
        print(f"[!] Không tìm thấy file test tại: {test_query_file}")