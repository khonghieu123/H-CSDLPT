# Cấu Trúc và Chức Năng Các File Trong Thư Mục Main (Hệ CSDLDPT)

Dự án này là hệ thống tìm kiếm tiếng chim **CBAR (Bird Song Retrieval System)**, được chia làm 2 pha hoạt động chính: **Offline** (Thu thập dữ liệu, trích xuất đặc trưng) và **Online** (Web Server, truy vấn tìm kiếm).

---

## 1. database.py
* **Chức năng:** Quản lý kết nối PostgreSQL và các câu lệnh tương tác cơ sở dữ liệu.
* **Chi tiết:**
  * Định nghĩa cấu hình kết nối DB (`DB_PARAMS`).
  * Hàm `get_connection()` thực hiện kết nối và bắt buộc gọi lệnh `register_vector()` từ thư viện `pgvector.psycopg2` để driver Python hiểu và chuyển đổi được định dạng vector đặc trưng của các file.
  * Hàm `insert_bird_record()` hỗ trợ lưu bản ghi đầu tiên vào bảng `bird_songs` kèm cơ chế tránh trùng lặp dữ liệu (`ON CONFLICT (file_path) DO NOTHING`).

## 2. crawler.py
* **Chức năng:** Tự động hóa quá trình thu thập dữ liệu thô (Audio Crawler).
* **Chi tiết:**
  * Sử dụng thư viện `requests` gọi API Xeno-canto v3.
  * Chứa danh sách 50 loài chim phổ biến (`BIRD_SPECIES`).
  * Thực hiện tải về tối đa 10 file `.mp3` chất lượng cao cho mỗi loài (Tổng cộng ~500 files), lưu trữ tại thư mục `data/raw/`.

## 3. download_model.py
* **Chức năng:** Tải về "bộ não" AI (Model Weight).
* **Chi tiết:**
  * Thực hiện tải file mô hình TensorFlow Lite của BirdNET v2.4 (`BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite` dung lượng khoảng 60MB).
  * Mô hình này được huấn luyện sẵn để trích xuất đặc trưng tiếng chim chất lượng cao, giúp hệ thống không cần tự huấn luyện mô hình học máy từ đầu.

## 4. feature_extraction.py
* **Chức năng:** Xử lý tín hiệu số truyền thống (Kịch bản 1 - MFCC).
* **Chi tiết:**
  * Quét toàn bộ thư mục `data/raw/` để tìm các file `.mp3`.
  * Hàm `extract_mfcc_vector()` thực hiện:
    1. Đưa tần số lấy mẫu (sample rate) về 22050 Hz chuẩn và chuyển về Mono.
    2. Cắt khoảng lặng vô nghĩa ở đầu và cuối file (`librosa.effects.trim`).
    3. Tính ma trận đặc trưng Mel-Frequency Cepstral Coefficients (MFCC) 20 dòng.
    4. Gom trung bình theo trục thời gian thành vector **20 chiều**.
  * Lưu thông tin loài chim cùng vector 20 chiều này vào CSDL PostgreSQL.

## 5. update_ai_vectors.py
* **Chức năng:** Xử lý trích xuất vector đặc trưng học sâu (Kịch bản 2 - BirdNET AI).
* **Chi tiết:**
  * Load mô hình TFLite bằng Byte để tránh lỗi đường dẫn chứa tiếng Việt trên hệ điều hành Windows.
  * Băm nhỏ file âm thanh (định dạng khắt khe 48000 Hz) thành các đoạn 3 giây bằng kỹ thuật **Sliding Window**.
  * Ép từng đoạn 3s qua mạng nơ-ron BirdNET, "chọc" vào lớp áp chót để rút ra vector ngữ nghĩa **1024 chiều**.
  * Thực hiện gom trung bình (Mean Pooling) tất cả các đoạn để có 1 vector 1024 chiều duy nhất đại diện cho file âm thanh gốc.
  * Lọc các bản ghi trong DB chưa có Vector AI (`birdnet_vector IS NULL`) và chạy cập nhật (UPDATE) bổ sung.

## 6. search.py
* **Chức năng:** Core Engine xử lý tìm kiếm và xếp hạng (Ranking).
* **Chi tiết:**
  * Hàm `search_similar_birds()`: Nhận file truy vấn `.wav`/`.mp3` tải lên từ UI, trích xuất vector MFCC 20 chiều, sau đó thực hiện lệnh SQL so khớp Cosine Distance (`<=>`) trên cột `mfcc_vector` để lấy ra Top 5 file tương đồng nhất.
  * Hàm `search_birdnet()`: Tương tự như trên nhưng chạy trích xuất vector 1024 chiều và truy vấn khớp trên cột `birdnet_vector`.
  * Tính toán thời gian phản hồi (Latency), độ giống nhau bằng phần trăm (`similarity = (1 - distance) * 100`) và đóng gói dữ liệu JSON trả về cho giao diện.

## 7. app.py
* **Chức năng:** Web Server Backend (Flask Framework).
* **Chi tiết:**
  * Cung cấp các static route để phục vụ giao diện người dùng (phục vụ thư mục `Frontend/index.html`, CSS, JS và Audio).
  * API Route `/search` nhận file âm thanh query upload và tham số phương pháp (`method` = `mfcc` hoặc `birdnet`) để điều hướng gọi hàm trong file `search.py` tương ứng.

## 8. test_ai.py
* **Chức năng:** Script kiểm tra nhanh (Testing).
* **Chi tiết:**
  * Cho phép lập trình viên kiểm tra độc lập thuật toán tìm kiếm AI bằng dòng lệnh trực tiếp trên console mà không cần khởi động Web Server của Flask.
