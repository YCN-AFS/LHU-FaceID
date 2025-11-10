# Hướng dẫn cài đặt và sử dụng LHU FaceID

## 📦 Cài đặt

### Bước 1: Cài đặt Python dependencies

```bash
# Tạo virtual environment (khuyến nghị)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 2: Cài đặt Cassandra

**Option A: Sử dụng Docker (Khuyến nghị)**

```bash
docker run -d \
  --name cassandra-lhu \
  -p 9042:9042 \
  cassandra:latest
```

**Option B: Cài đặt trực tiếp**

**Ubuntu/Debian:**
```bash
echo "deb http://www.apache.org/dist/cassandra/debian 40x main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
curl https://downloads.apache.org/cassandra/KEYS | sudo apt-key add -
sudo apt update
sudo apt install cassandra
sudo systemctl start cassandra
```

**Kiểm tra Cassandra:**
```bash
cqlsh
```

Nếu vào được prompt `cqlsh:system>`, Cassandra đã hoạt động.

### Bước 3: Tạo thư mục logs

```bash
mkdir -p logs
```

## 🚀 Chạy ứng dụng

```bash
python main.py
```

Hoặc sử dụng script:

```bash
./start.sh
```

API sẽ chạy tại: `http://localhost:8000`

## 📚 Sử dụng API

### 1. API Documentation

Truy cập Swagger UI tại: `http://localhost:8000/docs`

### 2. Đăng ký sinh viên

**Sử dụng curl:**
```bash
curl -X POST "http://localhost:8000/register_face?student_id=S001&name=Nguyen%20Van%20A&class=K50" \
  -F "file=@student_photo.jpg"
```

**Sử dụng Python:**
```python
import requests

url = "http://localhost:8000/register_face"
params = {
    "student_id": "S001",
    "name": "Nguyen Van A",
    "class": "K50"
}
files = {'file': open('student_photo.jpg', 'rb')}

response = requests.post(url, params=params, files=files)
print(response.json())
```

### 3. Xác thực khuôn mặt

**Sử dụng curl:**
```bash
curl -X POST "http://localhost:8000/verify_face" \
  -F "file=@face_to_verify.jpg"
```

**Sử dụng Python:**
```python
import requests

url = "http://localhost:8000/verify_face"
files = {'file': open('face_to_verify.jpg', 'rb')}

response = requests.post(url, files=files)
print(response.json())
```

### 4. Lấy thông tin sinh viên

```bash
curl "http://localhost:8000/get_student_info/S001"
```

## ⚙️ Cấu hình Threshold

Chỉnh sửa file `config.yaml` để điều chỉnh ngưỡng nhận diện:

```yaml
threshold:
  match: 0.45      # Ngưỡng MATCH (≥0.45)
  uncertain: 0.35  # Ngưỡng UNCERTAIN (0.35-0.45)
```

**Khuyến nghị:**
- Môi trường an ninh cao: `match: 0.60`
- Môi trường thông thường: `match: 0.45` (mặc định)
- Môi trường cần độ nhạy cao: `match: 0.40`

## 🧪 Testing

Chạy script test:

```bash
python test_api.py
```

## 🐛 Xử lý lỗi thường gặp

### Lỗi: "No module named 'cv2'"

```bash
pip install opencv-python
```

### Lỗi: "Could not connect to Cassandra"

Đảm bảo Cassandra đang chạy:
```bash
systemctl status cassandra
# hoặc
docker ps | grep cassandra
```

### Lỗi: "No face detected in image"

- Kiểm tra ảnh có khuôn mặt rõ ràng
- Đảm bảo khuôn mặt chiếm ít nhất 40x40 pixels
- Sử dụng ảnh có độ phân giải đủ cao

### Lỗi: "Failed to extract face embedding"

- Kiểm tra model ArcFace đã tải thành công
- Xem logs tại `logs/app_*.log`

## 📊 Giám sát

Xem logs:
```bash
tail -f logs/app_*.log
```

Xem error logs:
```bash
tail -f logs/error_*.log
```

## 🔒 Bảo mật

Khuyến nghị cho production:
1. Sử dụng HTTPS
2. Thêm authentication cho API
3. Giới hạn rate limiting
4. Backup database thường xuyên

## 📞 Hỗ trợ

Nếu gặp vấn đề, xem logs hoặc liên hệ team phát triển.

