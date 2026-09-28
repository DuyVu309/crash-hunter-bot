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

## 💡 Bí Kíp Tối Ưu Với Timber (Tùy chọn)

Nếu dự án của anh em chưa dùng `Timber`, hoặc chưa cấu hình log hiển thị số dòng, hãy làm theo 2 bước sau để CrashHunterBot có thể chỉ ra chính xác dòng code gây lỗi:

### Bước 1: Trồng cây Timber (Cấu hình hiển thị số dòng)
Vào file `Application` của dự án (ví dụ `MyApplication.kt`), thêm đoạn code sau vào hàm `onCreate()`:

```kotlin
if (BuildConfig.DEBUG) {
    Timber.plant(object : Timber.DebugTree() {
        override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
            // Tự động tìm số dòng gọi log
            val element = Throwable().stackTrace.getOrNull(5)
            val customMessage = if (element != null) {
                // Định dạng (FileName.kt:LineNumber) giúp Android Studio tạo link click được
                "(${element.fileName}:${element.lineNumber}) $message"
            } else message
            super.log(priority, tag, customMessage, t)
        }
    })
}
```

### Bước 2: "Đặt Mìn" (Bẫy Lỗi)
Để Bot bắt chính xác các lỗi quá tải API hoặc rò rỉ UI, anh em hãy đặt các dòng log ở những "điểm nóng" bằng các từ khóa sau:

- **Bẫy API Spam** (đặt ở các hàm fetch data):
  ```kotlin
  Timber.tag("CrashHunter").w("API_SPAM_TRAP: Đang gọi API lấy danh sách video")
  ```
- **Bẫy Rò Rỉ UI** (đặt ở các khối khởi tạo/hủy Composable nặng như Video Player):
  ```kotlin
  Timber.tag("CrashHunter").i("UI_LEAK_TRAP: Khởi tạo Video Player")
  ```

Khi Bot quét Logcat, nếu nó thấy `API_SPAM_TRAP` nổ liên tục >10 lần/giây, nó sẽ tóm ngay định dạng `(FileName.kt:LineNumber)` và ném thẳng vào báo cáo để anh em click vào sửa ngay lập tức!
