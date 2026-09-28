# Crash Hunter Bot (Antigravity Agent Skill)

Skill tự động dội bom kiểm thử (Stress Test / Monkey / Fuzzing) để săn các lỗi tử huyệt như Crash, RAM Leak, Navigation Leak, và API DDOS.

## Tự Động Hóa 100% (Auto-Discovery)
Phiên bản mới nhất của Bot đã được trang bị thuật toán nội suy thông minh:
- **Tự động nhận diện Package ID** từ `build.gradle.kts` hoặc `AndroidManifest.xml`.
- **Tự động quét DeepLink Schemes** để tự động đẻ ra kịch bản Fuzzing DeepLink.
- **Tự động bóc tách số dòng code** (File:Line) từ Logcat khi dự án sử dụng Timber.

## Cách Cài Đặt (Cho anh em Dev)

1. Copy toàn bộ thư mục này (`SKILL.md` và `scripts/`) vào trong thư mục `.agents/skills/crash-hunter-bot/` của project hiện tại của anh em. (Tạo thư mục nếu chưa có).
2. Mở IDE, chat với Antigravity AI: *"Chạy skill crash-hunter-bot"*.
3. Đi pha ly cà phê, đợi Bot tự động tạo script và chạy test. Khi xong, quay lại xem file báo cáo `CRASH_REPORT_FINAL.md` kèm chỉ định chính xác dòng code gây lỗi!
