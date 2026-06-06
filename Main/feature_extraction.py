import os
import sys
import glob
import librosa
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

from database import insert_bird_record

# ==========================================
# 1. CẤU HÌNH ĐƯỜNG DẪN HỆ THỐNG
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

def extract_mfcc_vector(file_path, n_mfcc=20):
    """
    Hàm ép 1 file âm thanh (độ dài bất kỳ) thành vector 20 chiều bằng MFCC.
    """
    try:
        # Load file âm thanh, tự động ép về Mono (1 kênh) và tần số 22050 Hz chuẩn
        y, sr = librosa.load(file_path, sr=22050, mono=True)
        
        # Cắt bỏ khoảng lặng vô nghĩa ở đầu và cuối file
        y_trimmed, _ = librosa.effects.trim(y)
        
        if len(y_trimmed) == 0:
            return None
            
        # Tính toán ma trận đặc trưng MFCC
        mfcc_matrix = librosa.feature.mfcc(y=y_trimmed, sr=sr, n_mfcc=n_mfcc)
        
        # Gộp trung bình theo trục thời gian (đập bẹp ma trận thành 1 mảng 20 chiều)
        mfcc_vector = np.mean(mfcc_matrix, axis=1)
        
        return mfcc_vector.tolist()
        
    except Exception as e:
        print(f"  [!] Lỗi trích xuất MFCC file {file_path}: {e}")
        return None

def process_offline_data():
    """
    Quét toàn bộ thư mục data/raw, tính toán và đẩy vào PostgreSQL
    """
    # Lấy danh sách toàn bộ file .mp3
    search_pattern = os.path.join(RAW_DATA_DIR, "*.mp3")
    audio_files = glob.glob(search_pattern)
    
    total_files = len(audio_files)
    if total_files == 0:
        print("[!] Không tìm thấy file âm thanh nào trong data/raw/")
        return

    print(f"[*] Đã tìm thấy {total_files} files trong kho chứa. Bắt đầu ép vector...")
    success_count = 0
    
    for idx, file_path in enumerate(audio_files, 1):
        file_name = os.path.basename(file_path)
        
        # Tách tên loài từ tên file (Ví dụ: pycnonotus_jocosus_123.mp3 -> pycnonotus_jocosus)
        species_name = "_".join(file_name.split('_')[:-1])
        
        print(f"[{idx}/{total_files}] Đang xử lý: {file_name}")
        
        # Gọi máy ép toán học MFCC (20 chiều)
        mfcc_vec = extract_mfcc_vector(file_path)
        
        # Máy ép AI BirdNET (1024 chiều) - Để trống None, chúng ta sẽ Update ở bước sau
        birdnet_vec = None 
        
        if mfcc_vec is not None:
            # Lưu đường dẫn tương đối để dễ quản lý
            relative_path = os.path.join("data", "raw", file_name)
            
            # Đẩy qua "băng chuyền" database.py
            is_inserted = insert_bird_record(
                species_name=species_name, 
                file_path=relative_path, 
                mfcc_vector=mfcc_vec, 
                birdnet_vector=birdnet_vec
            )
            
            if is_inserted:
                success_count += 1
                
    print(f"\n[HOÀN THÀNH] Đã trích xuất và lưu thành công {success_count}/{total_files} records vào PostgreSQL.")

if __name__ == "__main__":
    process_offline_data()