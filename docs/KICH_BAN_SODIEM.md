# Kịch bản demo Sổ điểm DS (khoảng 7 phút)

Một người vừa bấm vừa nói. Cột "Bấm" là thao tác, cột "Nói" là lời thuyết trình gợi ý.

## Chuẩn bị (trước khi lên)

1. Chạy `.\run-sodiem.ps1` trong thư mục dự án. Đợi 3 cửa sổ PowerShell hiện "Uvicorn running".
2. Mở 2 tab trình duyệt ở http://localhost:9001:
   - **Tab A (Quản trị):** bấm nút **root**. Trang mở sẵn "Quản trị hệ thống", tự cập nhật 3 giây/lần.
   - **Tab B (Người dùng):** để ở trang đăng nhập.
3. Mở sẵn một cửa sổ PowerShell trống để gõ lệnh tắt node-b ở cảnh 7.
4. Tập lại thì tắt 3 cửa sổ node và chạy lại script để xóa dữ liệu trong RAM.

## Mở đầu (30 giây)

| Bấm | Nói |
|---|---|
| Tab A | "Đây là Sổ điểm môn DS, một phần mềm thật chạy trên 3 node. Mỗi node là một tiến trình riêng, có khóa ký Ed25519 riêng, nhật ký riêng. Bài toán: các node không tin nhau hoàn toàn, nhưng vẫn phải cùng quyết định ai được xem, ai được sửa điểm, và cùng phát hiện tấn công." |
| Chỉ dòng "Khóa ký", "Tin khóa của" | "Node chỉ tin chữ ký của những khóa đã ghim trong keyring. Đó là trust anchor của cluster." |

## Cảnh 1. Xác thực khác phân quyền (1 phút)

| Bấm | Nói |
|---|---|
| Tab B → nút **alice** | "Alice là giảng viên môn DS. Đăng nhập xong, node ký một phiên. Node nào trong cluster cũng tự kiểm được phiên này." |
| Sửa điểm `dave` thành 8 → **Lưu** | "Reference monitor dùng ABAC: giảng viên, cùng khoa, dạy môn DS, nên được sửa." Chỉ dòng thông báo xanh: "Yêu cầu do node-x xử lý, rồi bản cập nhật được ký và gửi sang 2 node còn lại." |
| **Đăng xuất** → nút **mallory** | "Mallory đăng nhập được, tức là xác thực thành công. Nhưng xác thực không phải phân quyền." |
| Chỉ dòng lỗi trong bảng | "MAC chặn: nhãn của Mallory là public, bảng điểm là confidential. Vai trò lấy từ directory phía server, Mallory không tự khai được. Không luật nào cho phép thì mặc định từ chối." |

## Cảnh 2. Ủy quyền chỉ thu hẹp (1 phút 30)

| Bấm | Nói |
|---|---|
| **Đăng xuất** → **alice** → khung Chia sẻ quyền: Người nhận **Bob**, tích **Xem** + **Sửa**, tích **Cho phép chia sẻ tiếp** → **Chia sẻ** | "Bob là trợ giảng, chưa có quyền gì. Alice không đưa mật khẩu cho Bob, mà cấp một capability có chữ ký, có hạn dùng." |
| **Đăng xuất** → **bob** | "Bob giờ thấy bảng điểm nhờ quyền được chia sẻ." Chỉ dòng "bằng quyền được chia sẻ". |
| Chia sẻ cho **Carol**: tích **Xem** + **Xóa** → **Chia sẻ** | "Bob thử cấp thêm quyền Xóa mà chính Bob không có." Chỉ thông báo đỏ: "không được mở rộng quyền: delete". |
| Bỏ **Xóa**, chỉ để **Xem** → **Chia sẻ** | "Chỉ thu hẹp thì được. Vé con có hash của vé cha, hạn không vượt vé cha." |
| **Đăng xuất** → **carol** | "Carol xem được. Node xử lý tự kiểm chữ ký vé, không cần hỏi lại node đã cấp." Chỉ "Quyền được chia sẻ cho bạn: cấp 2, ký bởi node-x". |

## Cảnh 3. Giả mạo danh tính (30 giây, có thể bỏ)

| Bấm | Nói |
|---|---|
| Đang là Carol, F12 → Console, dán đoạn code dưới → Enter | "Carol sửa phiên của mình thành root." |
| Bị đưa về trang đăng nhập | "Chữ ký phiên không còn khớp khóa của node, nên bị từ chối. Quyền luôn gắn với danh tính đã được xác thực." |

```js
const t=JSON.parse(atob(sessionStorage.getItem('sodiem-token').replace(/-/g,'+').replace(/_/g,'/')));t.payload.user='root';sessionStorage.setItem('sodiem-token',btoa(JSON.stringify(t)).replace(/\+/g,'-').replace(/\//g,'_'));location.reload()
```

## Cảnh 4. Phát hiện tấn công cộng tác (1 phút)

| Bấm | Nói |
|---|---|
| Tab B → **mallory** → bấm **Tải lại** khoảng 10 lần | "Mallory cố mở bảng điểm nhiều lần. Các yêu cầu được chia vòng qua 3 node, nên mỗi node chỉ thấy một phần." |
| Sang Tab A, chỉ "Cảnh báo" của từng node | "Node nào thấy 3 lần bị từ chối trong 30 giây thì sensor AIDS ký một cảnh báo và gửi cho node khác." |
| Chỉ "Sự cố đã xác nhận" | "Một node nghi ngờ thì chưa đủ. Phải có ít nhất 2 node độc lập cùng báo một nguồn mới thành sự cố. Đó là collaborative IDS. Chữ ký chỉ chứng minh ai báo, không chứng minh báo đúng, nên cần quorum." |

## Cảnh 5. Xóa dấu vết (1 phút)

| Bấm | Nói |
|---|---|
| Tab A → khung **node-b** → **Diễn tập: sửa một bản ghi** | "Giả sử Mallory chiếm được node-b và sửa nhật ký, đổi một lần bị từ chối thành được phép." |
| Chỉ "Nhật ký: đứt tại #i", dòng đỏ | "Mỗi bản ghi chứa hash của bản trước. Sửa nội dung mà không tính lại hash thì chuỗi đứt ngay chỗ đó. Hash chain không ngăn được việc sửa, nhưng làm nó lộ ra." |
| Chỉ node-a, node-c vẫn "hợp lệ" | "Hai node kia vẫn giữ nhật ký riêng của mình. Chiếm một node không xóa được hết bằng chứng. Đây là ý tưởng nhân bản sổ cái của blockchain, nhưng ở đây chưa có đồng thuận." |

## Cảnh 6. Một node chết (1 phút)

| Bấm | Nói |
|---|---|
| Cửa sổ PowerShell trống, chạy lệnh dưới | "Giờ tắt hẳn node-b." |
| Tab A: node-b thành "không phản hồi" | |
| Tab B → **Đăng xuất** → **alice** → sửa một điểm → **Lưu** | "Hệ thống vẫn chạy. Yêu cầu tự chuyển sang node-a và node-c, thông báo ghi node-b không phản hồi." |

```powershell
Stop-Process -Id (Get-NetTCPConnection -LocalPort 9002 -State Listen).OwningProcess
```

## Kết (30 giây)

"Đây là chịu lỗi dừng, không phải chịu lỗi Byzantine: muốn chịu k node gian lận cần ít nhất 3k+1 node. Bản này còn là bản học thuật: chưa có TLS, dữ liệu trong RAM, AIDS chỉ dựa trên ngưỡng. Nhưng nó cho thấy đủ ba lớp của chương 9: trust, authorization và monitoring phối hợp với nhau."

## Nếu có sự cố khi diễn

- Mallory bấm 10 lần chưa có sự cố: bấm thêm vài lần nữa. Mỗi node cần 3 lần bị từ chối trong 30 giây.
- Đã diễn cảnh 4 một lần rồi: phải khởi động lại các node mới thấy lại cảnh báo, vì mỗi nguồn chỉ được báo một lần.
- Bật lại node-b: chạy lại `.\run-sodiem.ps1`, đóng 2 cửa sổ báo port bận. node-b lên lại với khóa cũ.
