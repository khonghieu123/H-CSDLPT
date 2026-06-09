# Báo cáo Chi tiết: Kiến trúc và Cấu trúc Mã nguồn Backend (Thư mục Main)

Dự án **CBAR (Bird Song Retrieval System)** là một hệ thống tìm kiếm thông tin đa phương tiện (Multimedia Information Retrieval) áp dụng kỹ thuật so khớp vector đặc trưng (Vector Matching) để nhận diện tiếng chim.

Dưới đây là mô tả cấu trúc chi tiết từng phần, từng dòng code quan trọng của các file trong thư mục `Main`.

---

## 1. database.py (Nền tảng Quản trị và Kết nối Cơ sở dữ liệu)

File này chịu trách nhiệm giao tiếp trực tiếp với hệ quản trị cơ sở dữ liệu PostgreSQL.

### A. Các thành phần cấu trúc chính
* **`DB_PARAMS` (Biến cấu hình):** Lưu trữ thông tin kết nối gồm `host`, `port`, `user`, `password` và tên cơ sở dữ liệu `bird_retrieval`. Các thông số này phải trùng khớp với khai báo trong file `docker-compose.yml`.
* **`get_connection()` (Hàm kết nối):**
  * Thiết lập kết nối vật lý thông qua thư viện `psycopg2`.
  * **Đoạn code quan trọng nhất:**
    ```python
    register_vector(conn)
    ```
    *Ý nghĩa:* PostgreSQL mặc định không hiểu kiểu dữ liệu mảng số thực (Vector) từ thư viện `pgvector`. Lệnh này đăng ký kiểu dữ liệu Vector với driver `psycopg2` để tự động chuyển đổi mảng NumPy trong Python thành kiểu dữ liệu `VECTOR` trong database và ngược lại.
* **`insert_bird_record()` (Hàm nạp dữ liệu):**
  * Nhận các tham số: Tên loài, đường dẫn file, vector MFCC (20 chiều) và vector BirdNET (1024 chiều).
  * Sử dụng câu lệnh SQL an toàn chống SQL Injection:
    ```sql
    INSERT INTO bird_songs (species_name, file_path, mfcc_vector, birdnet_vector)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (file_path) DO NOTHING;
    ```
    *Ý nghĩa:* Từ khóa `ON CONFLICT (file_path) DO NOTHING` dựa trên ràng buộc `UNIQUE` của cột `file_path` trong Database để đảm bảo khi bạn chạy lại file trích xuất nhiều lần, dữ liệu đã tồn tại sẽ được bỏ qua, không bị ghi đè hay lỗi trùng khóa.

---

## 2. crawler.py (Tải dữ liệu âm thanh từ Xeno-canto API)

File này chạy trong pha offline nhằm xây dựng tập dữ liệu (dataset) ban đầu gồm 500 files âm thanh.

### A. Các thành phần cấu trúc chính
* **`BIRD_SPECIES` (Danh sách cấu hình):** Mảng chứa tên khoa học của 50 loài chim phổ biến (ví dụ: `Pycnonotus jocosus` - Chào mào, `Passer montanus` - Sẻ ngô,...).
* **`download_bird_audio()` (Hàm thu thập chính):**
  * Gửi request HTTP GET tới API Xeno-canto với cú pháp tìm kiếm chuẩn hóa: `sp:"Tên loài" type:song` để chỉ lấy âm thanh tiếng hót chất lượng cao của loài chim đó.
  * **Cơ chế tải file và xử lý chuỗi:**
    ```python
    safe_species_name = species.replace(' ', '_').lower()
    file_name = f"{safe_species_name}_{record['id']}.mp3"
    ```
    *Ý nghĩa:* Chuyển đổi tên khoa học của chim thành chữ thường, thay khoảng trắng bằng dấu gạch dưới để tránh lỗi đường dẫn file trên hệ điều hành Windows khi đọc/ghi file.
  * **Cơ chế Rate Limiting (Tránh quá tải API):**
    ```python
    time.sleep(1)
    ```
    *Ý nghĩa:* Giãn cách 1 giây giữa các lần tải để tránh bị API chặn (IP Block) vì gửi yêu cầu quá dồn dập.

---

## 3. download_model.py (Tải Mô hình Trí tuệ Nhân tạo)

Tải file mô hình nhị phân học sâu chạy ngoại tuyến.

### A. Các thành phần cấu trúc chính
* **`download_birdnet_model()` (Hàm tải):**
  * Tự động xác định đường dẫn thư mục gốc và tạo thư mục `models/` nếu chưa có.
  * Sử dụng thư viện `urllib.request.urlretrieve` để tải trực tiếp file mô hình có kích thước khoảng ~51.7MB từ repository GitHub lưu trữ bộ mô hình TFLite về ổ cứng local.

---

## 4. feature_extraction.py (Trích xuất Vector Đặc trưng Toán học - Kịch bản 1)

Xử lý tín hiệu số truyền thống bằng thuật toán MFCC để tạo vector baseline.

### A. Các thành phần cấu trúc chính
* **`extract_mfcc_vector()` (Hàm lõi trích xuất):**
  * Sử dụng thư viện xử lý âm thanh chuyên dụng `librosa`.
  * **BƯỚC 1: Đọc và Resample:**
    ```python
    y, sr = librosa.load(file_path, sr=22050, mono=True)
    ```
    *Ý nghĩa:* Tự động chuẩn hóa âm thanh về dạng đơn kênh (Mono) và tần số lấy mẫu cố định 22050 Hz để đảm bảo mọi file âm thanh đầu vào đều có cùng một hệ quy chiếu.
  * **BƯỚC 2: Cắt khoảng lặng:**
    ```python
    y_trimmed, _ = librosa.effects.trim(y)
    ```
    *Ý nghĩa:* Loại bỏ tạp âm/khoảng tĩnh vô nghĩa ở đầu và cuối file để vector đặc trưng tập trung vào phần tiếng chim hót thực tế.
  * **BƯỚC 3: Tính toán MFCC:**
    ```python
    mfcc_matrix = librosa.feature.mfcc(y=y_trimmed, sr=sr, n_mfcc=20)
    ```
    *Ý nghĩa:* Tính toán 20 hệ số MFCC cho từng khung thời gian ngắn, kết quả trả về là một ma trận 2D `(20, số_khung_thời_gian)`.
  * **BƯỚC 4: Bình quân hóa (Mean Pooling):**
    ```python
    mfcc_vector = np.mean(mfcc_matrix, axis=1)
    ```
    *Ý nghĩa:* Lấy trung bình cộng của các cột theo trục thời gian để nén ma trận 2D thành một vector 1D duy nhất chứa đúng **20 chiều**, đại diện cho đặc trưng phổ âm thanh của toàn bộ file.
* **`process_offline_data()` (Vòng lặp nạp dữ liệu):**
  * Quét toàn bộ thư mục `data/raw/` bằng hàm `glob.glob`.
  * Trích xuất vector MFCC của từng file và gọi hàm `insert_bird_record` để đẩy bản ghi xuống database.

---

## 5. update_ai_vectors.py (Trích xuất Vector Đặc trưng Học sâu AI - Kịch bản 2)

Sử dụng mạng nơ-ron CNN BirdNET để lấy đặc trưng ngữ nghĩa phức tạp.

### A. Các thành phần cấu trúc chính
* **Nạp mô hình thông qua Bytes (Giải pháp sửa lỗi hệ thống):**
  ```python
  with open(MODEL_PATH, "rb") as f:
      model_bytes = f.read()
  interpreter = tf.lite.Interpreter(model_content=model_bytes, ...)
  ```
  *Ý nghĩa:* Tránh việc truyền trực tiếp đường dẫn file chứa tiếng Việt (`d:\Hệ CSDLDPT\...`) vào nhân C++ của TensorFlow Lite vốn rất nhạy cảm với ký tự Unicode, hạn chế tối đa lỗi crash đường dẫn.
* **`extract_birdnet_vector()` (Hàm trích xuất AI):**
  * Chuẩn hóa âm thanh về tần số **48000 Hz** (Mono) theo bắt buộc của mô hình BirdNET.
  * **Thuật toán Cửa sổ trượt (Sliding Window):**
    ```python
    chunk_length = 3 * 48000
    for i in range(0, len(y_trimmed), chunk_length):
        chunk = y_trimmed[i : i + chunk_length]
        if len(chunk) < chunk_length:
            chunk = np.pad(chunk, (0, chunk_length - len(chunk)))
    ```
    *Ý nghĩa:* BirdNET nhận dữ liệu đầu vào cố định dài đúng 3 giây (144.000 điểm mẫu). Đoạn code thực hiện cắt nhỏ file âm thanh dài thành các khúc 3 giây xếp liên tiếp. Khúc cuối nếu thiếu sẽ được bù thêm các số `0` (Zero-Padding) cho đủ kích thước.
  * **Trích xuất đặc trưng tại Lớp Áp chót (Feature Embedding Extraction):**
    ```python
    embedding_index = output_details[0]['index'] - 1
    vector_1024 = interpreter.get_tensor(embedding_index)[0]
    ```
    *Ý nghĩa:* Thay vì lấy kết quả phân loại loài chim ở lớp cuối cùng (Output layer), thuật toán chọc sâu vào lớp ẩn áp chót (Penultimate layer) để thu được vector biểu diễn đặc trưng ngữ nghĩa gồm **1024 chiều**.
  * **Mean Pooling:** Cộng trung bình cộng các vector 1024 chiều của các đoạn 3 giây để ra 1 vector 1024 chiều duy nhất đại diện cho cả file.
* **`run_ai_ingestion()` (Tiến trình cập nhật database):**
  * Thực hiện câu lệnh SQL: `SELECT id, file_path FROM bird_songs WHERE birdnet_vector IS NULL;`.
  * Chỉ xử lý những file chưa có vector AI để tối ưu hóa thời gian chạy. 
  * Cập nhật lại cột `birdnet_vector` bằng câu lệnh `UPDATE ... WHERE id = ...`.

---

## 6. search.py (Thuật toán Tìm kiếm và Xếp hạng)

Trái tim của pha online, thực hiện truy vấn so khớp không gian nhiều chiều.

### A. Các thành phần cấu trúc chính
* **`search_similar_birds()` (Tìm kiếm bằng MFCC 20 chiều):**
  * Trích xuất vector MFCC của file ghi âm truy vấn.
  * Thực hiện câu lệnh SQL tính khoảng cách Cosine:
    ```sql
    SELECT species_name, file_path, (mfcc_vector <=> %s) as cosine_distance
    FROM bird_songs
    ORDER BY cosine_distance ASC LIMIT %s;
    ```
    *Ý nghĩa:* Toán tử `<=>` trong pgvector biểu diễn khoảng cách Cosine. Lệnh trên tính toán góc lệch giữa vector truy vấn và toàn bộ vector trong database, sắp xếp khoảng cách từ nhỏ nhất đến lớn nhất (giống nhất lên đầu) để lấy Top K.
  * Chuyển đổi khoảng cách Cosine thành tỉ lệ tương đồng phần trăm hiển thị trực quan:
    ```python
    similarity = (1 - distance) * 100
    ```
* **`search_birdnet()` (Tìm kiếm bằng AI 1024 chiều):**
  * Tương tự như MFCC nhưng thực hiện tìm kiếm trên trường `birdnet_vector` sử dụng index HNSW được khai báo trong file `csdl.sql` để tìm kiếm siêu tốc trong không gian 1024 chiều.
  * Trả về kết quả gồm: Tên khoa học của chim, độ giống nhau (%), đường dẫn file âm thanh gốc và các thông số hiệu năng như thời gian trích xuất AI (`extraction_time_ms`) và thời gian quét DB (`search_time_ms`).

---

## 7. app.py (Web Server Controller)

Điều hướng và xử lý luồng yêu cầu từ trình duyệt.

### A. Các thành phần cấu trúc chính
* **Cấu hình Flask & CORS:** Cho phép frontend gửi request bất đồng bộ tới backend.
* **`serve_frontend_static` và `serve_audio`:** Các hàm phục vụ file giao diện tĩnh (HTML/CSS/JS) và stream file âm thanh gốc trực tiếp qua giao thức HTTP.
* **`search()` (Endpoint `/search` nhận request POST):**
  * Nhận file âm thanh truy vấn tải lên từ người dùng: `request.files['query_audio']`.
  * Lưu tạm thời file âm thanh vào thư mục `temp/`.
  * Điều phối luồng logic tùy thuộc vào giá trị biến `method` gửi lên:
    ```python
    if method == 'birdnet':
        result_data = search_birdnet(temp_path, top_k=5)
    else:
        results = search_similar_birds(temp_path, top_k=5)
    ```
  * Trả về dữ liệu kết quả định dạng JSON cho client.

---

## 8. test_ai.py (Công cụ kiểm tra nhanh)

File độc lập chạy trực tiếp trong terminal dùng cho mục đích kiểm thử và gỡ lỗi (debug) nhanh thuật toán tìm kiếm AI mà không cần khởi động giao diện web.
