# vì khong có mã nguồn gốc nên phải tải thông qua 1 bản sao của 1 lập trình viên, người viết mã nguồn cho ứng dụng whoBird, cũng dùng mã nguồn của BirdNet
import os
import urllib.request

def download_birdnet_model():
    # 1. Tự động tìm đường dẫn gốc và tạo thư mục
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
    model_dir = os.path.join(PROJECT_ROOT, "models")
    
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        
    model_filename = "BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite"
    model_path = os.path.join(model_dir, model_filename)
    
    # 2. URL trực tiếp dẫn đến file nhị phân lõi
    url = "https://github.com/woheller69/whoBIRD-TFlite/raw/master/BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite"
    
    print(f"[*] Đang tải 'Bộ não' BirdNET ({model_filename})...")
    print("    Dữ liệu khoảng 60MB, em đợi một chút nhé.")
    
    try:
        # 3. Thực thi kéo file từ mạng về ổ cứng
        urllib.request.urlretrieve(url, model_path)
        print(f"\n[v] TẢI THÀNH CÔNG! File đã nằm gọn tại:\n{model_path}")
    except Exception as e:
        print(f"\n[!] Lỗi khi tải file: {e}")
        print("Cách dự phòng: Em có thể copy link URL trong code, dán vào trình duyệt để tải thủ công.")

if __name__ == "__main__":
    download_birdnet_model()