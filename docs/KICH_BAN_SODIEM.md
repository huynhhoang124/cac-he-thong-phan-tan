# Demo Sổ điểm DS: 6 bước

## Hiểu trước khi demo

**Sổ điểm DS** là app quản lý điểm môn Hệ phân tán. Người dùng đăng nhập, xem điểm, sửa điểm, chia sẻ quyền cho người khác.

**Node** là một máy chủ chạy app này. Nhóm chạy 3 máy chủ giống nhau, gọi là node-a, node-b, node-c. Trong demo cả 3 chạy trên một laptop, mỗi cái ở một cổng:

| Node | Mở trên trình duyệt |
|---|---|
| node-a | http://localhost:9001 |
| node-b | http://localhost:9002 |
| node-c | http://localhost:9003 |

Mỗi node có 4 thứ riêng:
- **Bản sao dữ liệu**: bảng điểm và các vé chia sẻ. Sửa ở một node thì node đó gửi bản sao sang 2 node kia.
- **Con dấu** (khóa ký): đóng lên mọi thứ node gửi đi, để node khác biết thật hay giả.
- **Nhật ký**: ghi ai làm gì ở node đó.
- **Camera** (bộ phát hiện xâm nhập): chỉ thấy người đang dùng chính node đó.

**Nhân vật:**

| Tài khoản | Là ai | Quyền |
|---|---|---|
| `alice` | Giảng viên môn DS | Xem, sửa, chia sẻ |
| `bob` | Trợ giảng | Chỉ có quyền khi Alice chia sẻ |
| `carol` | Sinh viên | Chỉ có quyền khi được chia sẻ |
| `mallory` | Người lạ, kẻ xấu | Không có quyền |
| `root` | Quản trị hệ thống | Xem trang Quản trị |

Mật khẩu là tên + `123`. Trang đăng nhập có nút đăng nhập nhanh, bấm là vào.

**Câu chuyện 6 bước:** Alice xem điểm và chia quyền cho Bob. Bob chia tiếp cho Carol. Mallory tìm cách xem trộm, bị chặn, và bị phát hiện. Quản trị thấy sự cố. Cuối cùng một máy chủ chết mà hệ thống vẫn chạy.

**Chuẩn bị:** chạy `.\run-sodiem.ps1`, mở 3 tab 9001, 9002, 9003. Dán sẵn (chưa Enter) lệnh tắt node-b vào một cửa sổ PowerShell:

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ? CommandLine -match "sodiem.main:app --port 9002" | % { Stop-Process -Id $_.ProcessId -Force }
```

## Bước 1. Giới thiệu 3 node

**Chuyện gì:** cho người xem thấy có 3 máy chủ riêng, mỗi máy một con dấu riêng.

**Bấm:** chỉ 3 tab. Mở thêm `localhost:9001/identity` và `localhost:9003/identity`.

**Thấy:** trang đăng nhập 3 tab ghi `node-a · cổng 9001`, `node-b · cổng 9002`, `node-c · cổng 9003`. Hai trang identity có hai dãy `fingerprint` khác nhau.

**Tại sao:**
- `fingerprint` là mã nhận diện con dấu. Khác nhau nghĩa là mỗi node có con dấu riêng.
- Node chỉ tin những gì có con dấu của node trong nhóm. Các bước sau đều dựa vào điều này.

**Nói:** "Đây là 3 máy chủ chạy riêng. Mỗi máy có con dấu riêng, fingerprint là mã của con dấu. Các máy chỉ tin nhau qua con dấu."

## Bước 2. Alice được xem, Mallory bị chặn

**Chuyện gì:** giảng viên xem được điểm; người lạ thì không.

**Bấm:**
1. Tab 9001, đăng nhập `alice`.
2. Khung "Chia sẻ quyền": người nhận Bob, tick Xem + Sửa, tick "Cho phép chia sẻ tiếp", bấm Chia sẻ.
3. Đăng xuất, đăng nhập `mallory`, bấm "Tải lại" 2 lần.

**Thấy:**
- Alice: bảng điểm có ô sửa. Thông báo "Đã chia sẻ ... Ký bởi node-a".
- Mallory: "Bạn không có quyền này (MAC: nhãn public < confidential)".

**Tại sao:**
- Bảng điểm được đánh dấu "mật" (confidential). Mallory chỉ có mức "công khai" (public), thấp hơn, nên bị chặn. Đây là luật MAC.
- Alice là giảng viên đúng môn DS nên được phép. Đây là luật ABAC: xét thuộc tính người dùng.
- Không khớp luật nào thì mặc định chặn.
- Quyền tra ở server, không tin trình duyệt. Mallory tự sửa mình thành admin cũng bị phát hiện, vì phiên đăng nhập có con dấu.
- Mallory bị chặn 3 lần liền, camera node-a phát cảnh báo. Nhưng mới một node nghi thì chưa thành sự cố.

**Nói:** "Alice là giảng viên đúng môn nên được xem. Mallory mức bảo mật thấp nên bị chặn. Mallory thử 3 lần, node-a nghi ngờ, nhưng một node chưa đủ để kết luận."

## Bước 3. Bob chia quyền cho Carol

**Chuyện gì:** quyền được chia tiếp, nhưng chỉ nhỏ đi, không lớn thêm.

**Bấm:**
1. Tab 9002, đăng nhập `bob`. Chia sẻ cho Carol: tick Xem + Xóa, bấm Chia sẻ.
2. Bỏ tick Xóa, chỉ Xem, bấm Chia sẻ.
3. Tab 9003, đăng nhập `carol`.
4. Bấm "Sao chép vé" (dùng ở bước 4).

**Thấy:**
- Lần 1: "không được mở rộng quyền: ['delete'] không có trong vé cha".
- Lần 2: "Ký bởi node-b".
- Carol: bảng điểm không có ô sửa; dòng "xử lý bởi node-c · bằng quyền được chia sẻ".

**Tại sao:**
- Chia sẻ quyền là cấp một **vé** có đóng dấu. Vé ghi: ai cho, cho ai, được làm gì, hết hạn lúc nào.
- Alice cho Bob Xem + Sửa. Bob không có Xóa, nên không thể cho Carol Xóa. Vé con không được nhiều quyền hơn vé cha.
- Carol chỉ được Xem, nên không có ô sửa.
- Vé Carol do node-b đóng dấu, nhưng Carol dùng ở node-c. Node-c tự kiểm con dấu, không cần hỏi node-a.
- Chia quyền bằng vé thì không phải đưa mật khẩu, giống "Đăng nhập bằng Google".

**Nói:** "Chia sẻ là cấp vé có đóng dấu. Vé con chỉ được ít quyền hơn hoặc bằng vé cha, nên Bob không cho Carol quyền Xóa được. Node-c tự kiểm vé, không cần hỏi lại node khác."

## Bước 4. Mallory dùng vé của Carol

**Chuyện gì:** vé của Carol bị lộ. Mallory thử dùng 3 cách, cách nào cũng bị chặn.

**Bấm:**
1. Tab 9003, đăng xuất, đăng nhập `mallory`.
2. Ctrl+V vé vào ô "Mở bảng điểm bằng vé", bấm "Dùng vé".
3. Trong ô vé, sửa `"subject": "carol"` thành `"subject": "mallory"`, bấm "Dùng vé".
4. Sửa `"node": "node-b"` thành `"node": "mallory-laptop"`, bấm "Dùng vé".

**Thấy:**
- Lần 1: "vé cấp cho carol, không phải mallory".
- Lần 2: "chữ ký không khớp khóa của node-b".
- Lần 3: "khóa ký 'mallory-laptop' không thuộc cluster".

**Tại sao:**
- Lần 1, dùng nguyên vé: vé ghi tên Carol, người đang dùng là Mallory. Sai tên.
- Lần 2, sửa tên trên vé: con dấu được tính trên toàn bộ nội dung vé. Sửa một chữ là con dấu không khớp.
- Lần 3, tự đóng dấu: con dấu của máy Mallory không thuộc nhóm 3 node. Không tin.
- Mallory bị chặn liên tục, nên camera node-c cũng phát cảnh báo.

**Nói:** "Dùng nguyên vé thì sai tên. Sửa tên thì con dấu không khớp. Tự đóng dấu thì con dấu lạ. Ba cách, ba lớp kiểm."

## Bước 5. Quản trị thấy sự cố, thử sửa nhật ký

**Chuyện gì:** quản trị xem hệ thống đã phát hiện gì, và thử xem nhật ký có sửa lén được không.

**Bấm:**
1. Tab 9001, đăng xuất, đăng nhập `root`. Trang Quản trị tự mở, có 3 thẻ node.
2. Chỉ mục "Sự cố đã xác nhận".
3. Bấm "Diễn tập: sửa một bản ghi" ở thẻ node-a.

**Thấy:**
- Sự cố: "AIDS · mallory@127.0.0.1 ... báo bởi node-a, node-c".
- Thẻ node-a: "đứt tại bản ghi #...", một dòng tô đỏ. Thẻ node-b, node-c: "hợp lệ".

**Tại sao:**
- Node-a thấy Mallory ở bước 2. Node-c thấy ở bước 4. Mỗi camera chỉ thấy một phần.
- Hệ thống chỉ ghi sự cố khi ít nhất 2 node khác nhau cùng báo một người, trong 10 phút. Một node có thể bị chiếm và báo sai, nên cần node thứ hai xác nhận.
- Nhật ký như cuốn sổ, mỗi dòng ghi mã kiểm tra của dòng trước (hash chain). Nút diễn tập giả làm kẻ xấu sửa dòng "bị chặn" thành "cho phép". Mã không còn khớp, nên chuỗi đứt ngay dòng đó.
- Node-b, node-c có sổ riêng, vẫn nguyên, làm bằng chứng.

**Nói:** "Hai node cùng thấy Mallory nên mới thành sự cố. Ai sửa lén nhật ký node-a thì chuỗi đứt ngay, còn node-b, node-c vẫn giữ bằng chứng."

## Bước 6. Tắt node-b

**Chuyện gì:** một máy chủ chết, hệ thống vẫn chạy.

**Bấm:**
1. Bấm Enter ở cửa sổ PowerShell đã dán lệnh tắt node-b.
2. Nhìn trang Quản trị (tự cập nhật 3 giây một lần).
3. Tab 9003, đăng xuất, đăng nhập `bob`, chia sẻ Xem cho Carol.

**Thấy:**
- "2/3 node hoạt động", thẻ node-b "không phản hồi".
- Thông báo "Ký bởi node-c".

**Tại sao:**
- Node-b chết, nhưng dữ liệu đã có bản sao ở node-a, node-c. Bob vào node-c vẫn làm được việc, node-c đóng dấu thay.
- Bật lại node-b bằng `.\run-sodiem.ps1`: node-b dùng lại con dấu cũ và tự lấy dữ liệu mới từ node khác.
- Hệ thống chịu được máy **chết**. Chưa chịu được máy **còn chạy nhưng nói dối** (lỗi Byzantine).

**Nói:** "Node-b chết nhưng hệ thống vẫn chạy, node-c làm thay. Hệ thống chịu được máy chết, chưa chịu được máy nói dối."

## Kết luận

"App có ba lớp bảo vệ phối hợp. Một: các máy chỉ tin nhau qua con dấu. Hai: mặc định chặn, chỉ cho quyền tối thiểu, chia quyền chỉ được nhỏ đi. Ba: nhiều máy cùng xác nhận mới thành sự cố, nhật ký không sửa lén được. Giới hạn: chưa chịu được máy nói dối, chưa mã hóa đường truyền, dữ liệu chưa lưu xuống ổ đĩa."
