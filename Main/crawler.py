import os
import requests
import time

# ==========================================
# 1. CẤU HÌNH ĐƯỜNG DẪN HỆ THỐNG
# ==========================================
# Quản lý đường dẫn tuyệt đối (Absolute Path)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

# Tự động tạo cây thư mục nếu chưa tồn tại
os.makedirs(RAW_DATA_DIR, exist_ok=True)


# ==========================================
# 2. CẤU HÌNH API & DỮ LIỆU CRAWL
# ==========================================
# API Key hợp lệ của hệ thống
XENO_CANTO_API_KEY = "7d570e60a8be48194e01733d64edea0bfe77d831"

# Danh sách 50 loài chim phổ biến (Tên khoa học)
BIRD_SPECIES = [
    "Pycnonotus jocosus", "Copsychus saularis", "Streptopelia chinensis", "Passer montanus", "Acridotheres tristis",
    "Dicrurus macrocercus", "Gracupica nigricollis", "Garrulax canorus", "Zosterops palpebrosus", "Prinia inornata",
    "Orthotomus sutorius", "Pycnonotus aurigaster", "Copsychus malabaricus", "Cinnyris jugularis", "Aethopyga siparaja",
    "Dicaeum cruentatum", "Ploceus philippinus", "Lonchura punctulata", "Hirundo rustica", "Merops orientalis",
    "Halcyon smyrnensis", "Alcedo atthis", "Megalaima haemacephala", "Centropus sinensis", "Eudynamys scolopaceus",
    "Columba livia", "Spilopelia senegalensis", "Gallinula chloropus", "Amaurornis phoenicurus", "Ardeola bacchus",
    "Egretta garzetta", "Nycticorax nycticorax", "Phalacrocorax carbo", "Tachybaptus ruficollis", "Motacilla alba",
    "Lanius cristatus", "Oriolus chinensis", "Sturnia sinensis", "Acridotheres javanicus", "Acridotheres grandis",
    "Garrulus glandarius", "Urocissa erythroryncha", "Parus minor", "Pycnonotus finlaysoni", "Pycnonotus goiavier",
    "Aegithina tiphia", "Lacedo pulchella", "Coracias affinis", "Upupa epops", "Pitta sordida"
]

# Số lượng file cần tải cho mỗi loài (Tổng: 50 * 10 = 500 files)
TARGET_FILES_PER_SPECIES = 10 


# ==========================================
# 3. HÀM XỬ LÝ CHÍNH
# ==========================================
def download_bird_audio():
    total_downloaded = 0
    # Endpoint API v3
    base_url = "https://xeno-canto.org/api/3/recordings"
    
    for species in BIRD_SPECIES:
        print(f"\n[*] Đang tìm kiếm: {species}...")
        
        # Cú pháp Query chuẩn API v3: sp:"Tên loài" và đính kèm API Key
        query_params = {
            "query": f'sp:"{species}" type:song',
            "key": XENO_CANTO_API_KEY
        }
        
        try:
            # Gửi request với tham số params tự động mã hóa URL
            response = requests.get(base_url, params=query_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                recordings = data.get('recordings', [])
                
                downloaded_for_species = 0
                
                for record in recordings:
                    if downloaded_for_species >= TARGET_FILES_PER_SPECIES:
                        break
                        
                    file_url = record.get('file')
                    if not file_url:
                        continue
                        
                    # Chuẩn hóa tên file để tránh lỗi hệ điều hành
                    safe_species_name = species.replace(' ', '_').lower()
                    file_name = f"{safe_species_name}_{record['id']}.mp3"
                    file_path = os.path.join(RAW_DATA_DIR, file_name)
                    
                    # Cơ chế bỏ qua nếu file đã tồn tại
                    if os.path.exists(file_path):
                        downloaded_for_species += 1
                        total_downloaded += 1
                        continue
                        
                    try:
                        print(f"  -> Đang tải: {file_name}")
                        audio_res = requests.get(file_url, timeout=15)
                        
                        with open(file_path, 'wb') as f:
                            f.write(audio_res.content)
                            
                        downloaded_for_species += 1
                        total_downloaded += 1
                        
                        # Giãn cách các request để tránh quá tải server
                        time.sleep(1) 
                        
                    except Exception as e:
                        print(f"  [!] Lỗi khi tải file {file_name}: {e}")
                        
                print(f"[v] Đã tải {downloaded_for_species}/{TARGET_FILES_PER_SPECIES} files cho {species}.")
            else:
                print(f"[!] Lỗi API cho {species}. Mã lỗi: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"[!] Lỗi kết nối HTTP cho {species}: {e}")

    print(f"\n[HOÀN THÀNH] Tổng số file trong CSDL thô: {total_downloaded} files tại '{RAW_DATA_DIR}'.")

if __name__ == "__main__":
    print("=== KHỞI ĐỘNG CRAWLER DỮ LIỆU ĐA PHƯƠNG TIỆN (API V3) ===")
    download_bird_audio()