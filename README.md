# TrustMesh

Demo cho Chương 9, mục 9.4-9.7 của *Distributed Systems, 4th Edition*.

TrustMesh minh họa cách nhiều node độc lập phối hợp để:

- đánh giá trust và giảm ảnh hưởng của Sybil identities;
- thực thi ABAC và capability delegation;
- duy trì audit log liên kết bằng hash;
- phát hiện xâm nhập cục bộ và xác nhận sự cố theo quorum.

## Chạy nhanh bằng Docker

Yêu cầu: Docker Desktop và Docker Compose.

```bash
docker compose up --build
```

Mở <http://localhost:8001>. Ba node lần lượt dùng cổng `8001`, `8002`, `8003`.

Lưu ý Windows: nếu thư mục có dấu tiếng Việt (vd. `C:\Các hệ thống phân tán`), BuildKit báo lỗi `x-docker-expose-session-sharedkey ... non-printable ASCII`. Gán ổ ảo rồi build từ đó:

```powershell
cmd /c 'subst T: "C:\Các hệ thống phân tán"'; Set-Location T:\; docker compose -p trustmesh up --build -d
```

Đã chạy thật 3 container ngày 29/09/2026: 3/3 online, incident được cả node-a/b/c xác nhận, tắt node-b thì dashboard báo `2/3 node online` và node-a/c vẫn phục vụ. Ảnh: `output/3node/`.

Kiểm tra trạng thái:

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## Kịch bản trình diễn

Dashboard có các nút chạy scenario. Trình tự khuyến nghị:

1. `ABAC + delegation`
2. `Sybil attack`
3. `Collaborative IDS`
4. `Tamper audit log`
5. Tắt một node bằng `docker compose stop node-b`, sau đó kiểm tra cluster.

Khôi phục node:

```bash
docker compose start node-b
```

## Chạy kiểm thử

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

## Cấu trúc

- `PLAN.md`: phạm vi, tiến độ, phân công và tiêu chí nghiệm thu.
- `demo/`: dịch vụ FastAPI và dashboard.
- `tests/`: kiểm thử ABAC, capability, audit chain và monitoring.
- `slides/`: bài thuyết trình PowerPoint.
- `docs/DEMO_SCRIPT.md`: lời dẫn demo theo phút.
- `docs/SPEAKER_NOTES.md`: lời thoại gợi ý cho từng slide.

## Lưu ý bảo mật

Đây là demo học thuật, không phải hệ thống xác thực sản xuất. API scenario dùng danh tính giả lập để người xem quan sát quyết định chính sách. Các node ký capability và alert bằng khóa Ed25519 tạo lúc khởi động; khóa riêng không nằm trong mã nguồn. Cấu hình production cần bổ sung TLS, quản lý khóa chuyên dụng, authentication thực, persistence và network isolation.
