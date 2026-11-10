# TrustMesh

Demo cho Chương 9, mục 9.4–9.7 của *Distributed Systems, 4th Edition*: ba node độc lập, không hoàn toàn tin nhau, vẫn kiểm soát được quyền truy cập và phát hiện tấn công.

Mỗi node là một tiến trình FastAPI riêng, có khóa Ed25519, policy engine, sensor và audit chain riêng. Các node chỉ trao đổi qua HTTP.

## Chạy bằng Docker

```bash
docker compose up --build
```

Mở <http://localhost:8001>. Ba node dùng cổng `8001`, `8002`, `8003`.

Trên Windows, nếu thư mục có dấu tiếng Việt, BuildKit báo lỗi `x-docker-expose-session-sharedkey ... non-printable ASCII`. Gán ổ ảo rồi build từ đó:

```powershell
cmd /c 'subst T: "C:\Các hệ thống phân tán"'; Set-Location T:\; docker compose -p trustmesh up --build -d
```

## Chạy không cần Docker

```powershell
python -m pip install -r requirements.txt
.\run-local.ps1
```

Script mở 3 cửa sổ, mỗi cửa sổ là một node; khóa lưu ở `.data/`. Đóng cửa sổ `node-b` để thử partial failure.

## Câu chuyện trên dashboard

"Mallory muốn sửa bảng điểm": 4 màn, bấm `→` (hoặc phím `1`–`4`) để chạy. Phím `R` để reset cả cluster. Các màn dùng chung trạng thái, và mọi quyết định truy cập đồng thời là sự kiện cho sensor của node đó.

| Màn | Nội dung | Mục sách |
|---|---|---|
| 1 | Alice đọc được (ABAC), Mallory bị chặn (MAC), tự khai `admin` bị bỏ qua. 3 lần bị từ chối làm sensor node-a phát cảnh báo, nhưng 1 node chưa thành incident | 9.5.1–9.5.2 |
| 2 | node-a ký vé cho Bob, Bob ủy cho Carol ở node-b, Carol đọc ở node-c. Không node nào hỏi lại node cấp vé; mở rộng quyền bị chặn | 9.5.1, 9.5.3–9.5.4 |
| 3 | Mallory dùng vé đánh cắp, vé giả chữ ký, vé tự ký đều bị từ chối (trust anchor). Sensor các node bắn AIDS/SIDS, đủ quorum thành incident | 9.4, 9.6.2–9.6.3 |
| 4 | Mallory chiếm node-a và sửa audit log, chuỗi hash đứt. node-b, node-c vẫn giữ bằng chứng | 9.4.3 |

Partial failure: `docker compose stop node-b`, bấm `R`, chạy lại 1 → 4. Bob ủy quyền qua node khác, A và C vẫn đủ quorum. Khôi phục bằng `docker compose start node-b`.

Lời dẫn theo phút: `docs/DEMO_SCRIPT.md`.

## Kiểm thử

```bash
python -m pytest -q
```

## Cấu trúc

| File | Nội dung |
|---|---|
| `demo/crypto.py` | Khóa Ed25519 của node, ký/kiểm, canonical JSON |
| `demo/trust.py` | 9.4: keyring (trust anchor), audit hash chain |
| `demo/authz.py` | 9.5: attribute directory, reference monitor, capability, delegation |
| `demo/monitor.py` | 9.6: application gateway, sensor SIDS/AIDS, ghép cảnh báo theo quorum |
| `demo/node.py` | Trạng thái node, gọi peer qua HTTP (peer chết thì trả `down`, không ném lỗi) |
| `demo/main.py` | API thật của node |
| `demo/scenarios.py` | Câu chuyện 4 màn `/demo/act/{1..4}`, điều phối các node |
| `demo/static/` | Dashboard |

## Lưu ý bảo mật

Đây là demo học thuật. Danh tính người dùng và lưu lượng tấn công là dữ liệu mô phỏng. Attribute directory nằm cứng trong code; hệ thật lấy thuộc tính từ token có chữ ký. `/admin/reset` và `/peer/*` không xác thực để tiện tập dượt; trường `source` của `/access/check` cho client tự khai IP để mô phỏng nhiều máy tấn công. Production cần TLS, quản lý khóa, xác thực thật, lưu trữ bền và cô lập mạng.
