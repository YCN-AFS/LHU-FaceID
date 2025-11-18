# Hướng Dẫn Khởi Chạy Cassandra Database

Tài liệu này mô tả nhanh các bước để chuẩn bị và khởi chạy Cassandra phục vụ cho hệ thống LHU FaceID.

## 1. Yêu Cầu Môi Trường

- Đã cài đặt Docker và Docker Engine đang chạy.
- Cổng `9042` chưa bị ứng dụng khác sử dụng (cổng mặc định của Cassandra).
- Thư mục dự án: `/home/foxcode/Documents/projects/LHU-FaceID`.

## 2. Khởi Chạy Nhanh Với Docker (Khuyến Nghị)

### 2.1. Khởi tạo mới

```bash
docker run -d --name cassandra-lhu -p 9042:9042 cassandra:latest
```

### 2.2. Khởi động lại container đã tồn tại

```bash
docker start cassandra-lhu
```

### 2.3. Kiểm tra trạng thái

```bash
docker ps --filter name=cassandra-lhu
```

- Cột `STATUS` hiển thị `Up ...` nghĩa là container đang chạy.
- Cột `PORTS` phải có `0.0.0.0:9042->9042/tcp`.

## 3. Kiểm Tra Kết Nối Từ Ứng Dụng

> Thực hiện trong thư mục dự án `/home/foxcode/Documents/projects/LHU-FaceID`.

```bash
python3 -c "from cassandra.cluster import Cluster; Cluster(['127.0.0.1']).connect()"
```

- Không có thông báo lỗi nghĩa là Cassandra đã sẵn sàng.
- Nếu gặp lỗi `NoHostAvailable` hoặc `Connection refused`, kiểm tra lại container.

## 4. Khởi Động Ứng Dụng FastAPI

```bash
python3 main.py
```

- Khi server chạy, log sẽ hiển thị `Connected to Cassandra cluster`.
- Kiểm tra endpoint `http://localhost:8000/health` để đảm bảo `database: connected`.

## 5. Một Số Lệnh Cassandra Hữu Ích

Mở console CQL:

```bash
docker exec -it cassandra-lhu cqlsh
```

Trong CQL:

```sql
DESCRIBE KEYSPACES;
USE lhu_faceid;
DESCRIBE TABLES;
SELECT * FROM attendance_logs LIMIT 10;
```

## 6. Khắc Phục Sự Cố

- **Container không khởi động được**: chạy `docker logs cassandra-lhu` để xem thông tin chi tiết.
- **Xung đột cổng 9042**: dùng `sudo lsof -i :9042` để kiểm tra ứng dụng khác đang chiếm cổng và dừng ứng dụng đó.
- **Không có dữ liệu điểm danh**: xác minh:
  - Endpoint `/get_today_attendance` trả về danh sách rỗng có thể do chưa có bản ghi mới trong ngày.
  - Thời gian hệ thống và thời gian trong Cassandra phải khớp múi giờ.
  - Dữ liệu nằm trong bảng `attendance_logs` nhưng `checkin_time` khác ngày hiện tại.

## 7. Dọn Dẹp (Tùy Chọn)

```bash
docker stop cassandra-lhu          # Dừng container
docker rm cassandra-lhu            # Xóa container
docker volume prune                # Xóa volume (nếu muốn làm sạch hoàn toàn)
```

Lưu ý: xóa container/volume sẽ làm mất dữ liệu Cassandra.

