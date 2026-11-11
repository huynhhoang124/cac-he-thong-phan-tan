# Sổ điểm DS

Phần mềm quản lý điểm môn Hệ phân tán, chạy trên 3 node TrustMesh. Người dùng đăng nhập, xem và sửa điểm, chia sẻ quyền. Bảo mật nằm bên dưới: phiên có chữ ký, phân quyền nhiều mô hình, sensor cộng tác, nhật ký hash chain, dữ liệu nhân bản có ký.

## Chạy

```powershell
.\run-sodiem.ps1
```

Mở http://localhost:9001 (node-a). 9002, 9003 cũng mở được; mọi node phục vụ như nhau.

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
| 1. Ba node độc lập | Đăng nhập `root`, tab Quản trị. Mở `/health`, `/identity` ở 9001–9003 | Mỗi node có khóa ký riêng, nhật ký, số liệu riêng. Dòng "xử lý bởi node-x" đổi theo từng yêu cầu |
| 2. Alice được, Mallory bị chặn | Đăng nhập `alice` rồi `mallory` | Alice thấy bảng (ABAC). Mallory: "MAC: nhãn public < confidential". Vai trò lấy từ directory theo phiên đã ký; sửa phiên để thành admin → 401 |
| 3. Thu hẹp quyền | `alice` chia sẻ Xem + Sửa cho Bob, bật "chia sẻ tiếp". `bob` chia sẻ Xem + Xóa cho Carol, rồi chỉ Xem | Lần đầu bị chặn: "không được mở rộng quyền: delete". Carol xem được, sửa bị chặn |
| 4. Vé đánh cắp/giả | Quyền chia sẻ không rời server; mỗi yêu cầu gắn với người đã đăng nhập | Không dùng được vé của người khác; phiên sửa tay bị từ chối vì chữ ký không khớp khóa node |
| 5. Cảnh báo và sự cố | `mallory` bấm Tải lại khoảng 10 lần (hoặc đăng nhập sai nhiều lần). Xem Quản trị | Yêu cầu chia vòng qua các node; mỗi node chạm ngưỡng 3 lần/30 giây thì ký cảnh báo. Đủ 2 node báo mới thành sự cố |
| 6. Sửa nhật ký | Quản trị → "Diễn tập: sửa một bản ghi" ở một node | Node đó báo "đứt tại #i", bản ghi bị sửa tô đỏ; 2 node kia vẫn hợp lệ |
| 7. Tắt một node | Đóng cửa sổ PowerShell của node-b, dùng app tiếp | App vẫn chạy qua node-a/node-c; ghi điểm báo node-b "không phản hồi"; Quản trị hiện node-b mất. Mở lại bằng lệnh trong `run-sodiem.ps1`, khóa cũ giữ ở `.data-sodiem\` |

## Mã nguồn

| File | Vai trò |
|---|---|
| `gradebook.py` | Đăng nhập, phân quyền, chia sẻ, chia vòng giữa node, nhân bản `/peer/grade`, `/peer/ticket`, diễn tập |
| `main.py` | Gateway (firewall), `/health`, `/identity`, `/status`, nhận cảnh báo từ peer |
| `crypto.py`, `trust.py`, `authz.py`, `monitor.py`, `node.py` | Lõi TrustMesh (bản sao từ `demo/`) |
| `static/` | Giao diện |

Test: `python -m pytest tests/test_sodiem.py`.

## Giới hạn

Dữ liệu trong bộ nhớ, tắt hết node là mất. Ghi đồng thời ở hai node thì bản đến sau thắng. Không TLS; `/status` và header `x-hop` giữa các node chưa xác thực. Chưa chịu lỗi Byzantine (cần n ≥ 3k+1).
