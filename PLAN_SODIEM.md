# Plan: Sổ điểm DS, phần mềm riêng chạy trên TrustMesh

Mục tiêu: phần mềm quản lý điểm thật (không phải màn trình diễn), tách khỏi `demo/`, trả lời được 7 câu hỏi demo trong `Cau_hoi_TrustMesh_dap_an_rut_gon.docx`. Bảng đối chiếu câu hỏi → thao tác: `sodiem/README.md`.

## Backend `sodiem/`

- [x] Lõi TrustMesh tách riêng (bản sao `crypto`, `trust`, `authz`, `monitor`, `node`); `sense()` chuyển vào `node.py`.
- [x] `main.py`: chỉ gateway, `/health`, `/identity`, `/status`, `/peer/alert`. Bỏ các API cho client tự khai danh tính (`/access/check`, `/capabilities/*`, `/audit/tamper`, reset).
- [x] `gradebook.py`: đăng nhập (pbkdf2) → phiên ký Ed25519, node nào cũng kiểm được; mỗi cổng một node tự xử lý (không chia vòng, để vai trò từng node đúng lý thuyết); thêm `/app/grades/ticket` dùng vé tự trình; quyết định = directory rồi quyền được chia sẻ; audit + sensor (`user@ip`); điểm và quyền chia sẻ ký rồi nhân bản; trang quản trị và diễn tập sửa nhật ký chỉ cho admin.
- [x] `tests/test_sodiem.py`: sai mật khẩu, giảng viên đọc/ghi, MAC chặn khách, phiên giả bị 401, chuỗi chia sẻ thu hẹp (delete bị chặn), AIDS, chữ ký nhân bản, admin + diễn tập.

## Frontend `sodiem/static/`

- [x] Đăng nhập, Bảng điểm (sửa nếu có quyền), Chia sẻ quyền, Quyền được chia sẻ / đã chia sẻ, Quản trị (3 node, khóa, keyring, nhật ký, sự cố, diễn tập).
- [x] `run-sodiem.ps1` (9001–9003, khóa ở `.data-sodiem/`).

## Kiểm tra

- [x] 24 test pass.
- [x] Chạy thật 3 node: câu 2, 3, 5, 6, 7 qua API; tắt node-b app vẫn chạy.
- [x] Browser: đăng nhập, chia sẻ, trang quản trị ở 722px và 1366px.
- [ ] Máy chiếu thật.
