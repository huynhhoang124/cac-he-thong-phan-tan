# Lời thoại gợi ý

## Slide 1 — Trust, Authorization và Monitoring

Nhóm trình bày nửa sau Chương 9. Câu hỏi xuyên suốt là: khi các node không hoàn toàn tin nhau, hệ thống dựa vào cơ chế nào để cấp quyền và nhận biết tấn công?

## Slide 2 — Phạm vi 9.4-9.7

Ba phần liên kết theo một chuỗi. Trust xác định bằng chứng nào được chấp nhận. Authorization quyết định hành động nào được phép. Monitoring kiểm tra các giả định và chính sách có thực sự hoạt động hay không.

## Slide 3 — Trust khi có Byzantine behavior

Một process có thể gửi kết quả sai, không phản hồi hoặc cố tình mâu thuẫn. Với nhóm n process, Byzantine consensus thường cần giới hạn số node xấu k không vượt quá (n-1)/3. Ý chính là không cần tin từng node, nhưng phải tin giả định về cả nhóm.

## Slide 4 — Identity và Sybil attack

Sybil phá vỡ giả định một identity tương ứng một thực thể. Một attacker tạo nhiều node giả để tăng quyền biểu quyết hoặc cô lập node trung thực. CA tập trung có thể ràng buộc identity; hệ phi tập trung thường làm identity trở nên tốn kém bằng PoW, PoS hoặc reputation accounting.

## Slide 5 — Trusting a system

Hash chain giúp phát hiện thay đổi dữ liệu cũ. Replication khiến việc sửa đồng thời mọi bản sao khó hơn. Tuy nhiên người dùng vẫn phải tin implementation, consensus, smart contract và các dịch vụ trung gian.

## Slide 6 — Mô hình authorization

Subject yêu cầu operation trên object. Reference monitor chặn mọi đường truy cập và tra policy trước khi cho phép. Reference monitor phải chống sửa đổi và fail-safe default.

## Slide 7 — MAC, DAC, RBAC và ABAC

MAC dùng nhãn bảo mật do quản trị trung tâm đặt. DAC trao quyền cho chủ sở hữu. RBAC gắn quyền với vai trò. ABAC xét đồng thời thuộc tính người dùng, tài nguyên, môi trường và kết nối nên chi tiết hơn nhưng policy phức tạp hơn.

## Slide 8 — ACL và capability

ACL lưu quyền theo object. Capability lưu bằng chứng quyền ở phía subject. Capability phù hợp phân tán vì server có thể xác minh token, nhưng phải chống sửa, ràng buộc holder, giới hạn thời gian và xử lý thu hồi.

## Slide 9 — Delegation

Delegation cho ứng dụng hành động thay người dùng mà không nhận mật khẩu. Quyền được chuyển phải thu hẹp hoặc giữ nguyên, không mở rộng. OAuth là ví dụ thực tế; WAVE biểu diễn chuỗi delegation bằng đồ thị attestation.

## Slide 10 — Monitoring và firewall

Firewall lọc packet hoặc message tại biên nhưng không thay thế authorization. Nếu tài khoản hợp lệ bị chiếm, firewall có thể xem lưu lượng là bình thường. Hệ thống vẫn cần audit và intrusion detection phía trong.

## Slide 11 — SIDS và AIDS

SIDS khớp mẫu tấn công đã biết, giải thích dễ nhưng yếu với zero-day. AIDS học hành vi bình thường và tìm bất thường, nhưng có thể tạo nhiều false positive. Cần theo dõi accuracy và precision thay vì chỉ đếm alert.

## Slide 12 — Collaborative IDS

Một sensor không quan sát được toàn bộ hệ thống. CIDS chia sensor thành communities, mỗi community có head và chia sẻ detection. Centralized CIDS thường chính xác hơn nhưng dễ nghẽn; distributed CIDS mở rộng tốt hơn và tránh một điểm lỗi.

## Slide 13 — Kiến trúc TrustMesh

Ba node tự thực thi policy, audit và detection. Alert được ký. Hai reporter độc lập tạo quorum. Tắt một node chỉ tạo partial failure; hai node còn lại tiếp tục phục vụ.

## Slide 14 — Kịch bản demo

Chạy lần lượt authorization, Sybil, CIDS, tamper evidence và partial failure. Mỗi bước phải nói rõ cơ chế nào trong sách đang được thể hiện.

## Slide 15 — Kết luận

Trust không loại bỏ nhu cầu kiểm chứng. Authorization phải mặc định từ chối và giới hạn delegation. Monitoring phải kết hợp nhiều điểm quan sát. Một cơ chế đơn lẻ không đủ bảo vệ hệ thống phân tán.
