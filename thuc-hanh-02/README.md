# Bài thực hành số 02 - RabbitMQ và UDP multicast

Dự án cài đặt đầy đủ hai nội dung của đề bài bằng Python 3.10:

- Producer - Queue - Consumer với RabbitMQ;
- UDP multicast với một sender và nhiều receiver.

## 1. Cài đặt nhanh

Mở PowerShell tại thư mục này:

```powershell
python -m pip install -r requirements.txt
docker compose up -d
docker compose ps
```

Mở giao diện RabbitMQ tại <http://localhost:15672>, đăng nhập `guest` / `guest`.

Dự án pin RabbitMQ 3.13 vì đề bài yêu cầu queue `durable=False`. RabbitMQ 4 mặc định chặn loại transient non-exclusive queue này do tính năng đã bị đánh dấu deprecated.

## 2. Bài 1 - RabbitMQ

### KB1 - Persistent

Tạo mới queue bền bỉ:

```powershell
python -m rabbitmq.queue_manager --mode persistent --delete-first
```

Không chạy consumer, gửi 5 thông điệp:

```powershell
python -m rabbitmq.producer --mode persistent --count 5
docker compose restart rabbitmq
```

Chờ RabbitMQ khỏe lại rồi chạy consumer:

```powershell
docker compose ps
python -m rabbitmq.consumer --name consumer-1 --mode persistent --max-messages 5
```

Kết quả mong đợi: consumer nhận đủ 5 thông điệp sau khi broker restart.

### KB2 - Transient

Phải xóa queue persistent trước khi đổi thuộc tính `durable`:

```powershell
python -m rabbitmq.queue_manager --mode transient --delete-first
python -m rabbitmq.producer --mode transient --count 5
docker compose restart rabbitmq
```

Sau khi RabbitMQ khỏe lại:

```powershell
python -m rabbitmq.queue_manager --mode transient
python -m rabbitmq.consumer --name consumer-1 --mode transient
```

Kết quả mong đợi: queue cũ và 5 thông điệp transient bị mất sau restart; queue vừa tạo lại rỗng.

### KB3 - Bất đồng bộ

Terminal 1:

```powershell
python -m rabbitmq.queue_manager --mode persistent --delete-first
python -m rabbitmq.consumer --name consumer-1 --mode persistent --max-messages 20
```

Terminal 2:

```powershell
python -m rabbitmq.producer --mode persistent --count 20
```

So sánh dòng `[XONG]` của producer với tổng thời gian xử lý trong log consumer. Producer hoàn tất gửi gần như ngay lập tức, còn consumer cần khoảng 20-60 giây.

### KB4 - Ba consumer cân bằng tải

```powershell
python -m rabbitmq.queue_manager --mode persistent --delete-first
.\scripts\start-3-consumers.ps1 -Mode persistent
python -m rabbitmq.producer --mode persistent --count 15
```

Nhờ `prefetch_count=1`, RabbitMQ chỉ giao thêm việc khi consumer đã ack. Mỗi cửa sổ hiển thị số đơn mà consumer tương ứng xử lý.

## 3. Bài 2 - UDP multicast

Mở ba receiver trong ba cửa sổ:

```powershell
.\scripts\start-3-receivers.ps1
```

Sau đó gửi 10 bản tin:

```powershell
python -m multicast.sender --count 10 --interval 2
```

Cả ba receiver bind cùng cổng `5007`, join cùng group `224.1.1.1` và nhận nội dung giống nhau. Đây là cấu hình đúng khi thử trên một máy.

Kiểm tra receiver tham gia muộn:

```powershell
python -m multicast.sender --count 20 --interval 2
```

Đợi khoảng 20 giây rồi mở terminal khác:

```powershell
python -m multicast.receiver --name receiver-late --count 5
```

Receiver mới không nhận lại các sequence đã phát trước lúc join.

## 4. Log, ảnh và kiểm thử

- Log JSON Lines được lưu trong `logs/`.
- Lưu ảnh minh chứng vào `screenshots/`.
- Khung báo cáo nằm ở `BAO_CAO_MAU.md`.
- Xóa log cũ bằng `.\scripts\clean-logs.ps1`.

Chạy kiểm thử mã nguồn:

```powershell
python -m pytest -q
```

## 5. Lỗi thường gặp

- `PRECONDITION_FAILED - inequivalent arg 'durable'`: phải chạy `queue_manager --delete-first` trước khi đổi persistent/transient.
- Không kết nối được `localhost:5672`: kiểm tra `docker compose ps` và chờ health status là `healthy`.
- Multicast không nhận được trên máy khác: cho phép UDP 5007 qua firewall và đảm bảo các máy ở cùng LAN hỗ trợ multicast.
- Trên máy có nhiều card mạng/VPN, truyền địa chỉ IPv4 LAN cho receiver bằng `--interface 192.168.x.x`.

