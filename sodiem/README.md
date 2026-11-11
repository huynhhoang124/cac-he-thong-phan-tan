# Sổ điểm DS

Phần mềm quản lý điểm môn Hệ phân tán, chạy trên 3 node TrustMesh. Người dùng đăng nhập, xem và sửa điểm, chia sẻ quyền. Bảo mật nằm bên dưới: phiên có chữ ký, phân quyền nhiều mô hình, sensor cộng tác, nhật ký hash chain, dữ liệu nhân bản có ký.

## Chạy

```powershell
.\run-sodiem.ps1
```

Mỗi cổng là một node: 9001 = node-a, 9002 = node-b, 9003 = node-c. Node nào tự xử lý request nó nhận; điểm và vé được ký rồi nhân bản sang node khác. Kịch bản demo: `docs/KICH_BAN_SODIEM.md`.

| Tài khoản | Mật khẩu | Vai trò |
|---|---|---|
| alice | alice123 | Giảng viên môn DS: xem, sửa, chia sẻ |
| bob | bob123 | Sinh viên, trợ giảng: cần được chia sẻ |
| carol | carol123 | Sinh viên |
| mallory | mallory123 | Khách |
| root | root123 | Quản trị hệ thống: trang Quản trị |

Đổi mật khẩu bằng biến môi trường `PW_ALICE`, `PW_BOB`, ...

## Trả lời câu hỏi demo bằng app

| Câu | Làm gì | Thấy gì |
|---|---|---|
| 1. Ba node độc lập | Đăng nhập `root`, tab Quản trị. Mở `/health`, `/identity` ở 9001–9003 | Mỗi node có khóa ký riêng, nhật ký, số liệu riêng. Tên node hiện trên thanh trên cùng của từng cổng |
| 2. Alice được, Mallory bị chặn | Cổng 9001: `alice`, rồi `mallory` bấm Tải lại 2 lần | Alice thấy bảng (ABAC). Mallory: "MAC: nhãn public < confidential". Vai trò lấy từ directory theo phiên đã ký; sửa phiên để thành admin → 401 |
| 3. Thu hẹp quyền | 9001 `alice` chia sẻ Xem + Sửa cho Bob, bật "chia sẻ tiếp". 9002 `bob` chia sẻ Xem + Xóa cho Carol, rồi chỉ Xem. 9003 `carol` xem | Lần đầu bị chặn: "không được mở rộng quyền: delete". Carol xem được, sửa bị chặn |
| 4. Vé đánh cắp/giả | Carol "Sao chép vé". 9003 `mallory` dán vào "Mở bảng điểm bằng vé": nguyên vé, sửa `subject`, sửa `node` | Lần lượt: vé cấp cho carol; chữ ký không khớp khóa node-b; khóa 'mallory-laptop' không thuộc cluster |
| 5. Cảnh báo và sự cố | 9001 `root`, tab Quản trị | Sau câu 2 chỉ node-a cảnh báo, chưa có sự cố. Sau câu 4 node-c cũng báo: sự cố AIDS do node-a, node-c |
| 6. Sửa nhật ký | Quản trị → "Diễn tập: sửa một bản ghi" ở một node | Node đó báo "đứt tại #i", bản ghi bị sửa tô đỏ; 2 node kia vẫn hợp lệ |
| 7. Tắt một node | Đóng cửa sổ PowerShell của node-b. 9003 `bob` chia sẻ cho Carol | node-c nhận phần ủy quyền; ghi điểm báo node-b "không phản hồi"; Quản trị hiện node-b mất. Mở lại bằng lệnh trong `run-sodiem.ps1`, khóa cũ giữ ở `.data-sodiem\` |

## Mã nguồn

| File | Vai trò |
|---|---|
| `gradebook.py` | Đăng nhập, phân quyền, chia sẻ, dùng vé tự trình, nhân bản `/peer/grade`, `/peer/ticket`, diễn tập |
| `main.py` | Gateway (firewall), `/health`, `/identity`, `/status`, nhận cảnh báo từ peer |
| `crypto.py`, `trust.py`, `authz.py`, `monitor.py`, `node.py` | Lõi TrustMesh (bản sao từ `demo/`) |
| `static/` | Giao diện |

Test:
- `python -m pytest tests/test_sodiem.py`: một node, không cần chạy cluster.
- `python -m sodiem.check_demo`: kiểm 7 câu hỏi demo trên cluster đang chạy (khởi động lại trước cho dữ liệu sạch; câu 7 tự tắt rồi bật lại node-b).

## Giới hạn

Dữ liệu trong bộ nhớ, tắt hết node là mất; node bật lại một mình thì tự kéo trạng thái từ node còn sống. Ghi đồng thời cùng version ở hai node thì bản đến sau thắng. Không TLS; request giữa các node ký bằng khóa node (header `x-hop`, hạn 30 giây, phát lại được trong 30 giây đó). Chưa chịu lỗi Byzantine (cần n ≥ 3k+1).
