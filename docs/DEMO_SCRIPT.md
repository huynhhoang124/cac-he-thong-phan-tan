# Kịch bản demo 7 phút

## 0:00-0:40 — Kiến trúc

Mở dashboard tại `http://localhost:8001`. Chỉ vào ba node và nhấn mạnh mỗi node là một container, có khóa ký, policy engine, sensor và audit chain riêng. Các node chỉ trao đổi HTTP.

## 0:40-2:10 — Authorization và delegation

Chạy **ABAC + delegation**.

- Alice là teacher của đúng course và có clearance phù hợp nên được đọc bảng điểm.
- Mallory là guest, khác department và thiếu clearance nên bị từ chối.
- Alice cấp capability `read` cho Bob trong năm phút.
- Bob đọc được nhưng không ghi được. Capability áp dụng nguyên tắc attenuation: quyền con không thể mạnh hơn quyền cha.

Liên hệ sách: reference monitor, ABAC, capabilities và delegation ở 9.5.

## 2:10-3:15 — Sybil attack

Chạy **Sybil attack**.

- Admission ngây thơ chấp nhận toàn bộ identity giả.
- Admission resistant yêu cầu fingerprint vật lý duy nhất và stake tối thiểu.
- Giải thích đây là mô hình minh họa ý tưởng PoW/PoS: tạo identity phải gắn với chi phí. Nó không phải giải pháp Sybil hoàn chỉnh.

Liên hệ sách: 9.4.2.

## 3:15-4:50 — Collaborative IDS

Chạy **Collaborative IDS**.

- Chuỗi truy cập bị từ chối và nhiều tên `sybil-*` tạo cảnh báo tại từng sensor.
- Một cảnh báo riêng lẻ chưa đủ kết luận.
- Khi ít nhất hai reporter độc lập cùng báo một fingerprint, hệ thống tạo incident.
- Chỉ vào Accuracy, Precision, TP và FP. Nhắc đến đánh đổi false negative và false positive trong 9.6.

## 4:50-5:45 — Tamper evidence

Chạy **Tamper audit log**.

- Mỗi record chứa hash của record trước.
- Sửa record đầu làm toàn bộ phần nối sau mất tính nhất quán.
- Đây là bằng chứng chỉnh sửa, không tự động đồng nghĩa toàn bộ hệ thống đáng tin.

Liên hệ sách: 9.4.3 và append-only storage trong ví dụ WAVE.

## 5:45-6:40 — Partial failure

Trong terminal:

```bash
docker compose stop node-b
```

Nhấn **Làm mới trạng thái**. Node B chuyển sang `unreachable`, nhưng Node A và C vẫn hoạt động. Chạy lại authorization để chứng minh dịch vụ còn phục vụ.

Khôi phục:

```bash
docker compose start node-b
```

## 6:40-7:00 — Kết luận

TrustMesh không yêu cầu tin một cảnh báo đơn lẻ, mặc định từ chối khi policy không cho phép, hạn chế quyền được ủy quyền và giữ bằng chứng kiểm toán. Đây là cách các cơ chế 9.4-9.6 phối hợp thay vì hoạt động độc lập.
