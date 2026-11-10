# Kịch bản demo TrustMesh: "Mallory muốn sửa bảng điểm" (~5 phút)

Một câu chuyện, 4 màn. Mỗi màn thể hiện vài ý của sách, và các màn nối vào nhau: vé ở màn 2 bị Mallory đánh cắp ở màn 3, lần bị từ chối ở màn 1 là bản ghi Mallory muốn xóa ở màn 4.

Trước khi bắt đầu: `docker compose up -d` (hoặc `.\run-local.ps1`), mở `http://localhost:8001`, bấm **R** để reset. Bấm **→** để sang màn tiếp theo.

| Màn | Thời gian | Người | Ý thể hiện | Mục sách |
|---|---|---|---|---|
| 0 | 0:30 | Hùng | Kiến trúc 3 node | — |
| 1 | 1:00 | Huynh | ABAC, MAC, fail-safe, AuthN ≠ AuthZ, quyết định là dữ liệu cho sensor | 9.5.1–9.5.2 |
| 2 | 1:00 | Huynh | Capability ký số, tự kiểm tại chỗ, delegation chỉ thu hẹp, WAVE | 9.5.1, 9.5.3–9.5.4 |
| 3 | 1:00 | Huynh → Hùng | Trust anchor, SIDS/AIDS, cảnh báo ký số, quorum | 9.4, 9.6.2–9.6.3 |
| 4 | 0:45 | Hùng | Hash chain, bằng chứng nằm trên nhiều node | 9.4.3 |
| 5 | 0:45 | Hùng | Partial failure | — |

Sybil (9.4.2), Byzantine n ≥ 3k + 1 (9.4.1) và Firewall (9.6.1) chỉ nói trên slide.

## 0 — Kiến trúc

Chỉ vào 3 node. Mỗi node có khóa riêng (`key`), audit chain riêng (`chain`) và danh sách incident riêng. Trình duyệt chỉ nói chuyện với node-a; node-a điều phối các node khác qua HTTP.

## Màn 1 — Ai được đọc bảng điểm? (9.5.1–9.5.2)

Mọi request đều đi vào node-a.

- Alice là giảng viên môn DS, đang ở campus, nên được đọc (ABAC).
- Mallory là guest, bị từ chối vì nhãn public < confidential (MAC).
- Mallory tự khai `role=admin`. Node bỏ qua thuộc tính tự khai và tra directory, nên vẫn từ chối. Đây là điểm AuthN ≠ AuthZ.
- Mallory thử sửa điểm và tiếp tục bị từ chối.
- **Dòng cảnh báo vàng:** sensor của node-a thấy 3 lần từ chối trong 30 giây, nên ký và gửi cảnh báo AIDS cho B và C. B và C mới thấy 1 reporter, nên chưa thành incident.

Câu chốt: quyết định truy cập cũng là dữ liệu cho monitoring. Nhưng một node nghi ngờ thì chưa đủ.

## Màn 2 — Ủy quyền đi qua ba node (9.5.1, 9.5.3)

- node-a ký vé: Alice cho Bob quyền [read, write] và cho phép ủy tiếp.
- Bob mang vé sang node-b và ủy cho Carol quyền [read]. **node-b tự kiểm vé của node-a, không hỏi lại.** Vé con có depth 1, có `parent` và hạn ngắn hơn.
- Bob thử ủy [read, delete]: bị chặn vì không được mở rộng quyền.
- Carol đọc ở node-c thì được, ghi thì không.
- Chỉ vào chuỗi vé ở bên phải. Các vé nối nhau bằng parent-hash, giống một đường đi chứng minh quyền trong WAVE.

## Màn 3 — Mallory đổi chiến thuật (9.4 + 9.6.2–9.6.3)

Mallory chuyển sang node-c.

- Dùng lại vé đánh cắp của Carol: bị từ chối vì vé cấp cho carol.
- Sửa vé thành của mình và giả chữ ký node-b: bị từ chối vì chữ ký không khớp khóa đã ghim của node-b.
- Tự phát vé bằng khóa riêng: bị từ chối vì khóa không thuộc cluster. Đây là **trust anchor**, nối với 9.4.
- Sensor của node-c bắn AIDS. Lúc này node-a thấy 2 reporter, nên thành **INCIDENT**.
- Ở node-b, Mallory dò `../../etc/passwd`. Sensor bắn **SIDS** (khớp mẫu đã biết), khác với AIDS (bất thường so với ngưỡng).
- Kết quả: incident được cả 3 node xác nhận.

Câu chốt: chữ ký chỉ có giá trị khi khóa thuộc cluster. Từng node chỉ thấy một phần; khi nhiều node độc lập cùng báo, cảnh báo mới thành incident. Cảnh báo được ghép theo thời điểm node nhận, không cần đồng hồ chung.

## Màn 4 — Xóa dấu vết (9.4.3)

- Mallory chiếm node-a và sửa bản ghi "mallory bị từ chối" thành được phép.
- node-a kiểm chuỗi: đứt đúng tại bản ghi đó. Bên phải, khối bị sửa có màu đỏ.
- node-b và node-c vẫn giữ chuỗi hợp lệ và incident về Mallory.

Câu chốt: hash chain không ngăn được việc sửa, nó làm việc sửa bị lộ. Bằng chứng nằm trên nhiều node, nên chiếm một node không xóa được hết.

## 5 — Partial failure

```bash
docker compose stop node-b
```

Bấm **R**, rồi chạy lại 1 → 4:

- Màn 2: node-b không phản hồi, nên Bob ủy quyền qua node-c.
- Màn 3: incident vẫn đạt quorum nhờ node-a và node-c.
- Màn 4: node-c vẫn giữ bằng chứng.

```bash
docker compose start node-b
```

## Kết luận

Không cơ chế nào đứng một mình. Trust cho biết tin khóa nào. Authorization dùng khóa đó để kiểm vé tại chỗ. Monitoring ghép góc nhìn của nhiều node. Audit chain giữ lại bằng chứng.
