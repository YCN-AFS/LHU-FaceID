# 🚀 Khởi động Cassandra Database

## ⚠️ Lỗi: Connection refused

Ứng dụng không thể kết nối đến Cassandra. Cần khởi động Cassandra trước.

## ✅ Giải pháp nhanh

### Option 1: Docker (Khuyến nghị)

```bash
docker run -d --name cassandra-lhu -p 9042:9042 cassandra:latest
```

Kiểm tra:
```bash
docker ps | grep cassandra
```

### Option 2: Kiểm tra nếu đã cài

```bash
# Kiểm tra Cassandra
systemctl status cassandra

# Nếu chưa chạy, start
sudo systemctl start cassandra

# Auto-start on boot
sudo systemctl enable cassandra
```

## 📝 Kiểm tra kết nối

```bash
# Test connection
python -c "from cassandra.cluster import Cluster; Cluster(['127.0.0.1']).connect()"
```

Nếu không lỗi → Cassandra đã chạy!

## 🎯 Sau khi start Cassandra

Restart ứng dụng:
```bash
python main.py
```

Ứng dụng sẽ kết nối thành công với database.

## 💡 Tips

- **Docker**: Dễ dàng, portable, tự động setup
- **Native install**: Yêu cầu cấu hình nhưng nhanh hơn
- **Cloud**: Có thể dùng Cassandra-as-a-service

## 🔗 More info

- Cassandra docs: https://cassandra.apache.org/
- Docker hub: https://hub.docker.com/_/cassandra









