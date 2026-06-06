-- 1. Bật lõi pgvector (Chỉ cần chạy 1 lần duy nhất cho DB này)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tạo bảng lưu trữ thông tin và Vector đa chiều
CREATE TABLE bird_songs (
    id SERIAL PRIMARY KEY,
    species_name VARCHAR(100) NOT NULL,
    file_path TEXT UNIQUE NOT NULL,      
    mfcc_vector VECTOR(20),              -- Chứa tọa độ 20 chiều của Toán học
    birdnet_vector VECTOR(1024)          -- Chứa tọa độ 1024 chiều của AI
);

-- 3. Xây dựng cấu trúc Index phân tầng (HNSW) để tìm kiếm siêu tốc
-- vector_cosine_ops yêu cầu DB sử dụng Cosine Similarity để tính góc giữa các tọa độ
CREATE INDEX mfcc_hnsw_idx ON bird_songs USING hnsw (mfcc_vector vector_cosine_ops);
CREATE INDEX birdnet_hnsw_idx ON bird_songs USING hnsw (birdnet_vector vector_cosine_ops);