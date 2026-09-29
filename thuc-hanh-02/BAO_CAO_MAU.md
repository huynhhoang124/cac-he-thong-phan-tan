# BÁO CÁO BÀI THỰC HÀNH SỐ 02

**Họ và tên:** …  
**MSSV:** …  
**Lớp:** …  

## 1. Môi trường thực hiện

- Hệ điều hành: …
- Python: …
- RabbitMQ: Docker image `rabbitmq:3.13-management`
- Thư viện: `pika 1.3.2`

## 2. Bài 1 - RabbitMQ

### KB1 - Truyền tin bền bỉ

- Cấu hình: `durable=True`, `delivery_mode=2`.
- Cách chạy: …
- Kết quả trước/sau restart: …
- Ảnh minh chứng: chèn `screenshots/rabbit-kb1-*.png`.
- Nhận xét: …

### KB2 - Truyền tin nhất thời

- Cấu hình: `durable=False`, `delivery_mode=1`.
- Cách chạy: …
- Kết quả trước/sau restart: …
- Ảnh minh chứng: chèn `screenshots/rabbit-kb2-*.png`.
- Nhận xét: …

### KB3 - Truyền tin không đồng bộ

| Đại lượng | Kết quả |
|---|---:|
| Thời gian producer gửi 20 tin | … giây |
| Thời gian consumer xử lý 20 tin | … giây |

Nhận xét: …

### KB4 - Cân bằng tải

| Consumer | Số đơn đã xử lý |
|---|---:|
| consumer-1 | … |
| consumer-2 | … |
| consumer-3 | … |

Nhận xét: …

## 3. Bài 2 - UDP multicast

### KB1 - Ba receiver cùng nhận

- Số bản tin sender gửi: …
- Số bản tin từng receiver nhận: …
- Ảnh minh chứng: …
- Nhận xét: …

### KB2 - Receiver tham gia muộn

- Thời điểm receiver tham gia: …
- Sequence đầu tiên receiver nhận: …
- Receiver có nhận lại bản tin cũ không: Không.
- Nhận xét về tính transient: …

## 4. Kết luận

Tóm tắt sự khác nhau giữa persistent/transient, bất đồng bộ và multicast: …

