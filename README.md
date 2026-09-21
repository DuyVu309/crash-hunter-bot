# Crash Hunter Bot (Antigravity Agent Skill)

Skill tự động dội bom kiểm thử (Stress Test / Monkey) để săn các lỗi tử huyệt như Crash, RAM Leak, Navigation Leak, và API DDOS.

## Cách Cài Đặt (Cho anh em Dev)

1. Copy toàn bộ thư mục này (`SKILL.md` và `scripts/`) vào trong thư mục `.agents/skills/crash-hunter-bot/` của project hiện tại của anh em. (Tạo thư mục nếu chưa có).
2. **CỰC KỲ QUAN TRỌNG:** Mở file `scripts/generate_tests.py` và sửa biến `APP_PKG` thành Package ID của ứng dụng mà anh em đang làm!
   ```python
   # TODO(Devs): Sửa cái APP_PKG này thành Package Name của App mà anh em đang làm nhé!
   APP_PKG="com.your.package.name"
   ```
3. Mở IDE, chat với Antigravity AI: *"Chạy skill crash-hunter-bot"*.
4. Đi pha ly cà phê, đợi 1.5 tiếng và quay lại xem file báo cáo `CRASH_REPORT_FINAL.md`.
