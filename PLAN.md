# Kế hoạch Chương 9: Trust, Authorization và Monitoring

## 1. Phạm vi

Nhóm trình bày từ mục 9.4 đến hết Chương 9 của *Distributed Systems, 4th Edition*:

- 9.4 Trust in distributed systems
- 9.5 Authorization
- 9.6 Monitoring
- 9.7 Summary

Sản phẩm minh họa là **TrustMesh**, một hệ thống phân tán ba node mô phỏng kiểm soát truy cập và phát hiện xâm nhập cộng tác.

## 2. Mục tiêu đầu ra

1. Slide PowerPoint khoảng 15 trang, phù hợp bài nói 20-25 phút.
2. Demo chạy bằng Docker Compose với ba node FastAPI.
3. Kịch bản trình diễn 6-8 phút, có cả trường hợp bình thường và lỗi.
4. Mã nguồn, kiểm thử, hướng dẫn chạy và bảng đối chiếu với đặc trưng hệ thống phân tán.

## 3. Câu hỏi trung tâm

> Làm thế nào một hệ thống gồm nhiều node, không hoàn toàn tin tưởng nhau, vẫn kiểm soát được quyền truy cập và phát hiện tấn công trên toàn hệ thống?

## 4. Kiến trúc demo

```text
                           Người trình diễn
                                  |
                         http://localhost:8001
                                  |
              +---------------- Node A ----------------+
              | ABAC | capability | sensor | audit log |
              +----------+-------------------+----------+
                         /                     \
                        / signed alerts         \
           +--------- Node B --------+   +--------- Node C --------+
           | policy | sensor | audit |   | policy | sensor | audit |
           +-------------------------+   +-------------------------+
```

Mỗi node là một tiến trình/container độc lập, có khóa Ed25519 riêng, trạng thái riêng và giao tiếp bằng HTTP. Không node nào đọc trực tiếp bộ nhớ của node khác.

## 5. Chức năng phải hoàn thành

| Nội dung sách | Chức năng demo | Minh chứng |
|---|---|---|
| Byzantine trust | Cảnh báo chỉ được xác nhận khi có từ hai node báo cáo | Một node báo sai chưa tạo incident |
| Sybil attack | So sánh admission ngây thơ và admission có ràng buộc danh tính/stake | Nhiều identity giả bị giảm ảnh hưởng |
| Trusting a system | Nhật ký append-only liên kết bằng SHA-256 | Sửa bản ghi cũ làm kiểm tra integrity thất bại |
| ABAC | Quyết định dựa trên thuộc tính chủ thể, tài nguyên và môi trường | Teacher đúng course được đọc; guest bị từ chối |
| Delegation | Capability ký số, có phạm vi, hạn dùng và giới hạn ủy quyền tiếp | Không thể mở rộng quyền khi delegate |
| Firewall | Middleware giới hạn kích thước, host, CORS và tần suất yêu cầu | Burst request bị chặn 429 |
| SIDS/AIDS | Luật chữ ký và luật bất thường theo cửa sổ thời gian | Phân biệt known pattern và hành vi bất thường |
| CIDS | Node chia sẻ cảnh báo ký số và hợp nhất theo quorum | Hai cộng đồng độc lập cùng xác nhận tấn công |

## 6. Kịch bản demo

1. **ABAC bình thường**: Alice là giảng viên môn Distributed Systems đọc bảng điểm của đúng môn học. Hệ thống cho phép.
2. **ABAC từ chối**: Mallory có vai trò guest yêu cầu cùng tài nguyên. Hệ thống từ chối và ghi audit log.
3. **Delegation**: Alice cấp cho Bob quyền `read` có hạn dùng. Bob dùng capability thành công; thử `write` bị từ chối.
4. **Sybil**: tạo nhiều identity từ cùng một tác nhân. Chế độ ngây thơ nhận tất cả; chế độ resistant loại identity trùng fingerprint hoặc không đủ stake.
5. **Collaborative IDS**: gửi chuỗi truy cập bị từ chối tới hai node. Cảnh báo cục bộ trở thành incident khi quorum đạt 2.
6. **Partial failure**: tắt Node B. Node A và Node C vẫn kiểm tra quyền và ghi log; dashboard báo Node B không khả dụng.
7. **Tamper evidence**: sửa một audit record trong bộ nhớ demo. `/audit/verify` phát hiện chuỗi hash bị hỏng.

## 7. Phân công

### Nhóm ba người

- **Người 1**: 9.4, phần Sybil/trust, kiến trúc tổng thể, dẫn demo Sybil.
- **Người 2**: 9.5, ABAC/capability/delegation, dẫn demo authorization.
- **Người 3**: 9.6-9.7, firewall/CIDS/metrics, dẫn demo failure và monitoring.

### Nhóm hai người

- **Người 1**: 9.4 và demo trust/Sybil/hash-chain.
- **Người 2**: 9.5-9.7 và demo ABAC/delegation/CIDS.
- Cả hai cùng thực hiện mở đầu, kiến trúc và kết luận.

## 8. Tiến độ đề xuất

| Ngày | Công việc | Tiêu chí hoàn thành |
|---|---|---|
| 1 | Đọc 9.4-9.7, thống nhất thuật ngữ | Có outline và câu hỏi trung tâm |
| 2 | Chạy bộ khung ba node | Ba cổng trả health độc lập |
| 3 | Hoàn thành ABAC và audit chain | Test allow/deny và integrity đạt |
| 4 | Hoàn thành capability/delegation | Không thể tăng quyền hoặc hạn dùng |
| 5 | Hoàn thành sensor và CIDS | Quorum tạo incident đúng |
| 6 | Hoàn thành dashboard và kịch bản lỗi | Demo không cần sửa mã trực tiếp |
| 7 | Hoàn thiện slide, tập nói và quay dự phòng | Tổng thời gian dưới 25 phút |

## 9. Tiêu chí nghiệm thu

- Có ít nhất ba process/container chạy độc lập.
- Node chỉ phối hợp qua message HTTP.
- Tắt một node không làm toàn hệ thống dừng.
- Quyết định authorization mặc định là từ chối.
- Capability có chữ ký, scope, expiry và attenuation.
- Audit chain phát hiện chỉnh sửa dữ liệu cũ.
- Cảnh báo CIDS cần báo cáo từ ít nhất hai node.
- Có test tự động cho các luật quan trọng.
- Slide và lời nói liên kết từng chức năng demo với đúng mục trong sách.

## 10. Giới hạn được công bố

TrustMesh là sản phẩm học tập chạy cục bộ. Danh tính người dùng trong các scenario là dữ liệu mô phỏng; hệ thống không thay thế OAuth, WAVE, firewall mạng hoặc IDS sản xuất. TLS thuộc phạm vi hạ tầng triển khai và không được giả lập trong demo localhost.
