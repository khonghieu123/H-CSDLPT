# BẢN KẾ HOẠCH TRIỂN KHAI: HỆ THỐNG TÌM KIẾM TIẾNG CHIM (CBAR)

**Chiến lược:** Áp dụng kiến trúc A/B Testing so sánh đối chứng giữa Trích xuất Đặc trưng Toán học (MFCC) và Trí tuệ Nhân tạo (BirdNET).

## Giai đoạn 1: Xây dựng Nền tảng Kho dữ liệu (Pha Offline Chung)
**Mục tiêu:** Thu thập nguyên liệu và chuẩn bị cơ sở hạ tầng lưu trữ hỗ trợ lập chỉ mục đa chiều.

### Bước 1.1: Thu thập Dataset
- Viết script Python dùng thư viện `requests` gọi API từ trang Xeno-canto.
- Tải về 500 files `.wav` đại diện cho khoảng 10-20 loài chim phổ biến. Lưu vào thư mục `data/raw/`.

### Bước 1.2: Thiết kế Database Schema
- Cài đặt PostgreSQL và kích hoạt extension `pgvector`.
- Tạo bảng `bird_songs` tích hợp sẵn 2 không gian lưu trữ cho 2 kịch bản.
- Đánh chỉ mục HNSW độc lập cho cả 2 cột vector để tối ưu tốc độ rà soát lân cận.

## Giai đoạn 2: Thực thi Kịch bản 1 - Xử lý theo Cơ bản (MFCC Pipeline)
**Mục tiêu:** Hoàn thiện luồng xử lý tín hiệu số truyền thống, tạo baseline cho hệ thống.

### Bước 2.1: Tiền xử lý âm thanh
- Sử dụng thư viện `librosa`.
- **Chuẩn hóa:** Đưa toàn bộ 500 files về Mono, Sample Rate 22050 Hz.
- **Cắt khoảng lặng (Silence Trimming):** Ở đầu và cuối file để loại bỏ khung nhiễu.

### Bước 2.2: Trích xuất Vector 20 chiều
- Áp dụng thuật toán Mel-Frequency Cepstral Coefficients (MFCC).
- Tính trung bình cộng (Mean) theo trục thời gian của ma trận đầu ra để chốt lại thành 1 vector 20 chiều.

### Bước 2.3: Đổ dữ liệu vào DB
- Lưu vector 20 chiều này vào cột `mfcc_vector` của 500 records tương ứng trong PostgreSQL.

## Giai đoạn 3: Thực thi Kịch bản 2 - Xử lý theo AI Nâng cao (BirdNET Pipeline)
**Mục tiêu:** Tích hợp Deep Learning để khai thác đặc trưng ngữ nghĩa, nâng cao khả năng chống nhiễu.

### Bước 3.1: Tiền xử lý theo chuẩn mạng Nơ-ron
- Giữ nguyên khoảng lặng. Chuẩn hóa về 48000 Hz.
- **Áp dụng kỹ thuật Cửa sổ trượt (Sliding Window):** Cắt file thành các chunks dài đúng 3 giây.

### Bước 3.2: Trích xuất Vector 1024 chiều ("Chặt đầu mô hình")
- Đẩy lần lượt các chunks 3s qua mạng CNN BirdNET.
- Can thiệp vào luồng truyền tiến (Forward pass), hứng dữ liệu tại Lớp áp chót (Penultimate/Global Average Pooling Layer) để lấy ma trận các vector 1024 chiều.

### Bước 3.3: Gom cụm (Pooling) và Đổ vào DB
- **Áp dụng Mean Pooling:** Tính trung bình cộng các vector 1024 chiều của các chunks để ra 1 vector 1024 chiều duy nhất đại diện cho toàn bộ file gốc.
- Lưu vector này vào cột `birdnet_vector` trong PostgreSQL.

## Giai đoạn 4: Tích hợp Giao diện và Luồng Truy vấn (Pha Online Chung)
**Mục tiêu:** Cho phép người dùng (giám khảo) tương tác thời gian thực với CSDL.

### Bước 4.1: Xây dựng Backend Controller
- Sử dụng framework nhẹ như Flask hoặc FastAPI.
- Tạo API endpoint `/search` nhận đầu vào là 1 file `query.wav` và tham số `method` (chọn MFCC hoặc BirdNET).

### Bước 4.2: Cơ chế So khớp (Distance Matching)
- Dịch file query thành Vector Q (chiều dài phụ thuộc vào method).
- Dùng toán tử Cosine Distance (`<=>`) trong truy vấn SQL để tìm Top 5 kết quả có khoảng cách không gian ngắn nhất.

### Bước 4.3: Giao diện Demo (UI)
- Tạo giao diện HTML/CSS/JS đơn giản có nút Upload.
- Tích hợp một nút gạt (Toggle) "Chế độ Cơ bản (MFCC)" và "Chế độ Nâng cao (BirdNET AI)".
- Hiển thị danh sách Top 5 kết quả kèm nút Play để phát lại âm thanh trực tiếp trên trình duyệt.

## Giai đoạn 5: Đánh giá và Lập Báo cáo Đồ án
**Mục tiêu:** Đo lường bằng số liệu thực tế để chứng minh năng lực thiết kế hệ thống.

### Bước 5.1: Xây dựng tập thử nghiệm (Test Set)
- Chuẩn bị 20 files âm thanh tiếng chim mới hoàn toàn (có lẫn tạp âm) để làm truy vấn.

### Bước 5.2: Đo lường Độ chính xác (Precision)
- Chạy 20 files qua Kịch bản 1 (MFCC). Tính điểm Precision@5.
- Chạy 20 files qua Kịch bản 2 (BirdNET). Tính điểm Precision@5.

### Bước 5.3: Đo lường Hiệu năng (Latency)
- Ghi log thời gian từ lúc bắt đầu gọi truy vấn SQL đến lúc DB trả về Top 5 (Query Time) của cả 2 kịch bản.

### Bước 5.4: Hoàn thiện báo cáo
- Vẽ biểu đồ so sánh trực quan và kết luận về sự đánh đổi (trade-off) giữa tốc độ, dung lượng lưu trữ và độ chính xác của 2 phương pháp.