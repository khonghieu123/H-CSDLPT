import os
import time
from database import get_connection
# Lấy lại "Cỗ máy ép AI" mà em vừa viết
from update_ai_vectors import extract_birdnet_vector 

def test_birdnet_search(file_path):
    print(f"[*] Đang ép AI cho file truy vấn: {os.path.basename(file_path)}")
    start_ext = time.time()
    
    # 1. Ép file MP3 thành 1 vector 1024 chiều
    query_vector = extract_birdnet_vector(file_path)
    if not query_vector:
        print("[!] Không ép được file.")
        return
        2
    print(f"[v] Ép xong! (Thời gian: {time.time() - start_ext:.2f}s)")
    
    # 2. Gửi lệnh xuống DB qua đường cao tốc HNSW
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ép kiểu dữ liệu sang ::vector để PostgreSQL hiểu
    sql = """
        SELECT id, file_path, (1 - (birdnet_vector <=> %s::vector)) * 100 AS similarity
        FROM bird_songs
        WHERE birdnet_vector IS NOT NULL
        ORDER BY birdnet_vector <=> %s::vector ASC
        LIMIT 5;
    """
    
    start_search = time.time()
    # Truyền query_vector 2 lần vì trong SQL có 2 dấu %s
    cursor.execute(sql, (query_vector, query_vector))
    results = cursor.fetchall()
    search_time = time.time() - start_search
    
    # 3. In kết quả
    print(f"\n=== KẾT QUẢ TÌM KIẾM BIRDNET (1024 Chiều) ===")
    print(f"Thời gian quét DB: {search_time*1000:.2f} ms\n")
    
    for rank, row in enumerate(results, 1):
        print(f"Top #{rank} | Độ tương đồng: {row[2]:.2f}% | File: {row[1]}")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # Thay đường dẫn này bằng đường dẫn tới file Hút mật đỏ lúc nãy em đã test trên giao diện
    test_file = "d:/Hệ CSDLDPT/data/raw/aethopyga_siparaja_845232.mp3" 
    test_birdnet_search(test_file)