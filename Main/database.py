import psycopg2
from pgvector.psycopg2 import register_vector
import sys

sys.stdout.reconfigure(encoding='utf-8')
import numpy as np

# ==========================================
# 1. CẤU HÌNH KẾT NỐI (CONNECTION STRING)
# ==========================================
DB_PARAMS = {
    "dbname": "bird_retrieval",
    "user": "admin",
    "password": "123",
    "host": "localhost",
    "port": "5432"
}

def get_connection():
    """
    Tạo và trả về đối tượng kết nối đến PostgreSQL.
    Đồng thời đăng ký kiểu dữ liệu VECTOR cho session này.
    """
    try:
        # Khởi tạo kết nối
        conn = psycopg2.connect(**DB_PARAMS)
        
        # BẮT BUỘC: Đăng ký pgvector với thư viện psycopg2 để nó hiểu mảng Numpy
        register_vector(conn)
        
        return conn
    except Exception as e:
        print(f"[!] Lỗi không thể kết nối Database: {e}")
        return None

def insert_bird_record(species_name, file_path, mfcc_vector, birdnet_vector):
    """
    Hàm đẩy 1 record (gồm thông tin và 2 vector) xuống CSDL.
    """
    conn = get_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        
        # Câu lệnh SQL INSERT. Dùng cú pháp ON CONFLICT để bỏ qua nếu file đã tồn tại.
        insert_query = """
            INSERT INTO bird_songs (species_name, file_path, mfcc_vector, birdnet_vector)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (file_path) DO NOTHING;
        """
        
        # Ép kiểu dữ liệu về Numpy Array trước khi đẩy xuống DB để pgvector tự động dịch
        mfcc_np = np.array(mfcc_vector) if mfcc_vector is not None else None
        birdnet_np = np.array(birdnet_vector) if birdnet_vector is not None else None
        
        cursor.execute(insert_query, (species_name, file_path, mfcc_np, birdnet_np))
        conn.commit()
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"[!] Lỗi khi INSERT file {file_path}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ==========================================
# 3. CHẠY THỬ NGHIỆM KẾT NỐI
# ==========================================
if __name__ == "__main__":
    print("=== KIỂM TRA KẾT NỐI CSDL VECTOR ===")
    test_conn = get_connection()
    if test_conn:
        print("[v] KẾT NỐI THÀNH CÔNG! Driver psycopg2 và pgvector đã hoạt động.")
        test_conn.close()
    else:
        print("[x] KẾT NỐI THẤT BẠI. Hãy kiểm tra lại Docker.")