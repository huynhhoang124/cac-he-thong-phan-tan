# Kết quả kiểm thử đã chạy

Thời điểm kiểm thử: 28/09/2026, trên Windows với Python 3.10.11, Docker Desktop và RabbitMQ 3.13.

## RabbitMQ

### KB1 - Persistent

- Đã tạo queue `don_hang` với `durable=True`.
- Đã gửi 5 thông điệp với `delivery_mode=2` khi không có consumer.
- Trước restart: `message_count=5`.
- Sau restart RabbitMQ: `message_count=5`.
- Consumer sau đó nhận và manual ack đủ 5/5 thông điệp.

Kết luận: queue và thông điệp persistent tồn tại sau khi broker khởi động lại.

### KB2 - Transient

- Đã tạo queue `don_hang` với `durable=False`.
- Đã gửi 5 thông điệp transient.
- Trước restart: `message_count=5`.
- Sau restart, queue được tạo lại với `message_count=0`.

Kết luận: queue và thông điệp transient không tồn tại sau khi broker khởi động lại.

### KB3 - Không đồng bộ

- Phần publish bên trong producer gửi 20 thông điệp trong **0,127 giây**.
- Một consumer xử lý đủ 20 thông điệp trong **42,860 giây** với thời gian xử lý ngẫu nhiên 1-3 giây/đơn.
- Log: `logs/kb3-producer.jsonl` và `logs/kb3-consumer.jsonl`.

Kết luận: producer không chờ từng đơn được xử lý; thời gian gửi nhỏ hơn nhiều thời gian xử lý toàn bộ queue.

### KB4 - Cân bằng tải

Đã chạy đồng thời ba consumer, dùng manual ack và `prefetch_count=1`, sau đó gửi 15 thông điệp:

| Consumer | Số đơn xử lý |
|---|---:|
| kb4-consumer-1 | 5 |
| kb4-consumer-2 | 5 |
| kb4-consumer-3 | 5 |

Kết luận: 15 đơn được phân phối đều 5-5-5 giữa ba consumer.

## UDP multicast

### KB1 - Nhiều receiver cùng nhận

- Sender gửi đúng 5 gói tới `224.1.1.1:5007`.
- `smoke-receiver-1`: nhận 5/5 gói.
- `smoke-receiver-2`: nhận 5/5 gói.
- `smoke-receiver-3`: nhận 5/5 gói.

Kết luận: một lần gửi của sender được cả ba tiến trình trong group nhận.

### KB2 - Receiver tham gia muộn

- Sender bắt đầu từ `seq=0`.
- Receiver được mở sau khoảng một giây.
- Sequence đầu tiên receiver nhận được là `seq=5`, sau đó nhận `6` và `7`.
- Receiver không nhận lại các sequence `0-4` đã phát trước khi tham gia.

Kết luận: UDP multicast mang tính transient, không lưu bản tin cũ cho thành viên tham gia muộn.

### KB3 - Quan sát bằng Wireshark

- Đã cài Wireshark 4.6.8 và driver Npcap.
- TShark ghi lưu lượng từ loopback, Wi-Fi và Ethernet vào `captures/multicast-kb3.pcapng` trong lúc sender phát 5 bản tin.
- Display filter: `ip.dst == 224.1.1.1 && udp.dstport == 5007 && frame.interface_id == 1`.
- Trên giao diện Wi-Fi có đúng 5 gói, tại các frame `22`, `69`, `76`, `118`, `179`.
- Cả 5 gói có nguồn `172.16.9.226`, đích `224.1.1.1`, cổng UDP đích `5007`; payload chứa JSON với `seq`, `sentAt`, `sentEpoch`.
- Ảnh bằng chứng: `screenshots/08-wireshark-multicast.png`.

Kết luận: sender phát một luồng multicast gồm đúng 5 datagram; không tạo một bản sao gửi riêng cho từng receiver.

## Kiểm thử mã nguồn

```text
5 passed in 0.08s
```

Các log JSON Lines trong `logs/` có thể dùng để lập bảng và chụp bằng chứng cho báo cáo.

