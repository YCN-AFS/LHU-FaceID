# LHU FaceID - Student Face Recognition System

Hệ thống nhận diện và truy xuất thông tin sinh viên nội bộ với độ chính xác cao.

## 🎯 Tổng quan

LHU FaceID là hệ thống nhận diện khuôn mặt sinh viên sử dụng:
- **MTCNN**: Phát hiện khuôn mặt
- **ArcFace**: Trích xuất embedding khuôn mặt 512 chiều
- **Cosine Similarity**: So khớp embedding
- **FastAPI**: Backend RESTful API
- **Cassandra**: Database lưu trữ dữ liệu sinh viên

## 📋 Yêu cầu hệ thống

- Python 3.8+
- Cassandra 3.11+
- 8GB RAM trở lên (recommended)
- GPU (optional, để tăng tốc xử lý)

## 🚀 Cài đặt

### 1. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Cài đặt và cấu hình Cassandra

**Ubuntu/Debian:**
```bash
echo "deb http://www.apache.org/dist/cassandra/debian 40x main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
curl https://downloads.apache.org/cassandra/KEYS | sudo apt-key add -
sudo apt update
sudo apt install cassandra
```

**Hoặc sử dụng Docker:**
```bash
docker run -d \
  --name cassandra \
  -p 9042:9042 \
  cassandra:latest
```

### 3. Tạo thư mục logs

```bash
mkdir -p logs
```

## ⚙️ Cấu hình

Chỉnh sửa file `config.yaml` để cấu hình:

- **Threshold**: Điều chỉnh ngưỡng nhận diện
  - `match`: ≥ 0.45 → MATCH
  - `uncertain`: 0.35-0.45 → UNCERTAIN
  - < 0.35 → NO_MATCH

- **Cassandra**: Cấu hình kết nối database

- **API**: Cấu hình host, port

## 🏃 Chạy ứng dụng

```bash
python main.py
```

API sẽ chạy tại: `http://localhost:8000`

## 📡 API Endpoints

### 1. Đăng ký khuôn mặt sinh viên

**POST** `/register_face`

```bash
curl -X POST "http://localhost:8000/register_face?student_id=S001&name=Nguyen%20Van%20A&class=K50" \
  -F "file=@student_photo.jpg"
```

**Response:**
```json
{
  "status": "success",
  "message": "Student S001 registered successfully",
  "student_id": "S001",
  "name": "Nguyen Van A",
  "class": "K50"
}
```

### 2. Xác thực khuôn mặt

**POST** `/verify_face`

```bash
curl -X POST "http://localhost:8000/verify_face" \
  -F "file=@face_to_verify.jpg"
```

**Response (MATCH):**
```json
{
  "status": "MATCH",
  "message": "Face matched with similarity 0.8234",
  "student_info": {
    "student_id": "S001",
    "name": "Nguyen Van A",
    "class": "K50"
  },
  "similarity": 0.8234
}
```

**Response (UNCERTAIN):**
```json
{
  "status": "UNCERTAIN",
  "message": "Face matched with similarity 0.4023",
  "student_info": {
    "student_id": "S001",
    "name": "Nguyen Van A",
    "class": "K50"
  },
  "similarity": 0.4023
}
```

**Response (NO_MATCH):**
```json
{
  "status": "NO_MATCH",
  "message": "No match found",
  "student_info": null,
  "similarity": 0.2456
}
```

### 3. Lấy thông tin sinh viên

**GET** `/get_student_info/{student_id}`

```bash
curl "http://localhost:8000/get_student_info/S001"
```

**Response:**
```json
{
  "status": "success",
  "student_info": {
    "student_id": "S001",
    "name": "Nguyen Van A",
    "class": "K50",
    "last_checkin_time": "2024-01-15T10:30:00",
    "created_at": "2024-01-10T09:00:00"
  }
}
```

### 4. Health check

**GET** `/health`

```bash
curl "http://localhost:8000/health"
```

## 🎛️ Điều chỉnh Threshold

Chỉnh sửa `config.yaml`:

```yaml
threshold:
  match: 0.45      # Tăng để yêu cầu độ chính xác cao hơn
  uncertain: 0.35  # Giảm để tăng độ nhạy
```

**Khuyến nghị:**
- Môi trường an ninh cao: `match: 0.60`
- Môi trường thông thường: `match: 0.45`
- Môi trường cần độ nhạy cao: `match: 0.40`

## 📊 Hiệu suất

- **Độ chính xác**: ≥98% (với threshold phù hợp)
- **Thời gian xử lý**: ~100-300ms/image (CPU)
- **Thời gian xử lý**: ~50-100ms/image (GPU)

## 🔍 Cấu trúc dự án

```
LHU-FaceID/
├── main.py              # FastAPI application
├── database.py          # Cassandra database operations
├── face_utils.py        # Face detection & embedding utilities
├── config.py            # Configuration management
├── config.yaml          # Configuration file
├── logger_setup.py      # Logger configuration
├── requirements.txt     # Python dependencies
├── README.md            # Documentation
├── .gitignore          # Git ignore file
└── logs/               # Log files directory
```

## 📝 Logs

Logs được lưu tại thư mục `logs/`:
- `app_{time}.log`: General logs
- `error_{time}.log`: Error logs only

## 🛠️ Gỡ lỗi

### Không kết nối được Cassandra
```bash
# Kiểm tra Cassandra đang chạy
systemctl status cassandra

# Khởi động Cassandra
systemctl start cassandra
```

### Lỗi import MTCNN
```bash
# Cài đặt lại MTCNN
pip install --upgrade mtcnn
```

### Lỗi load ArcFace model
```bash
# Kiểm tra model file tồn tại
ls models/
```

## 📄 License

MIT License

## 👥 Tác giả

LHU FaceID Team

## 🙏 Cảm ơn

Sử dụng các thư viện:
- [InsightFace](https://github.com/deepinsight/insightface)
- [MTCNN](https://github.com/ipazc/mtcnn)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Cassandra](https://cassandra.apache.org/)

# LHU-FaceID
