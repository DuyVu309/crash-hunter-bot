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

## 💡 Bí Kíp Tối Ưu Với Timber & Log Extension (Tùy chọn)

Để CrashHunterBot có thể quét Logcat và nhặt ra **CHÍNH XÁC số dòng code** bị lỗi, anh em hãy thiết lập hệ thống **Log Extension** thông minh sau:

### Bước 1: Trồng cây Timber (Hiển thị số dòng)
Vào file `Application` của dự án (ví dụ `MyApplication.kt`), thêm đoạn sau vào `onCreate()`:

```kotlin
if (BuildConfig.DEBUG) {
    Timber.plant(object : Timber.DebugTree() {
        override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
            // Lấy stackTrace (index = 5 do dùng qua Extension)
            val element = Throwable().stackTrace.getOrNull(5)
            val customMessage = if (element != null) {
                // Định dạng (FileName.kt:LineNumber) giúp Android Studio click được
                "(${element.fileName}:${element.lineNumber}) $message"
            } else message
            super.log(priority, tag, customMessage, t)
        }
    })
}
```

### Bước 2: Tạo file `LogExt.kt` (Tái sử dụng)
Thay vì gọi `Timber` thủ công, hãy tạo một file `LogExt.kt` tiện ích để tự động lấy tên Class làm Tag:

```kotlin
import timber.log.Timber

fun Any.logd(tag: String, message: Any?) {
    val newMes = message ?: "null"
    Timber.tag(this::class.java.simpleName).d("$tag ---- $newMes")
}

fun Any.logw(tag: String, message: Any?) {
    val newMes = message ?: "null"
    Timber.tag(this::class.java.simpleName).w("$tag ---- $newMes")
}

fun Any.logi(tag: String, message: Any?) {
    val newMes = message ?: "null"
    Timber.tag(this::class.java.simpleName).i("$tag ---- $newMes")
}
```

### Bước 3: "Đặt Mìn" bắt lỗi
Bây giờ ở bất cứ đâu trong dự án, anh em chỉ cần gọi hàm extension ngắn gọn này ở các "điểm nóng":

- **Bẫy API Spam** (đặt ở các hàm gọi mạng/Ktor):
  ```kotlin
  logw("CrashHunter", "API_SPAM_TRAP: Đang gọi API...")
  ```
- **Bẫy MVI Intent Spam** (đặt khi nhận action từ user):
  ```kotlin
  logd("CrashHunter", "INTENT_TRAP: OnTabSelected")
  ```
- **Bẫy Rò Rỉ UI** (đặt ở LaunchedEffect / DisposableEffect của Composable nặng):
  ```kotlin
  logi("CrashHunter", "UI_LEAK_TRAP: Khởi tạo Video Player")
  ```

Log bắn ra sẽ có dạng:
`D/Timber_HomeViewModel: (HomeViewModel.kt:145) CrashHunter ---- INTENT_TRAP: OnTabSelected`

CrashHunterBot sẽ quét các tag `_TRAP` này, và nếu thấy nổ >10 lần/giây, nó sẽ bế thẳng dòng `(HomeViewModel.kt:145)` lên báo cáo cho anh em xử lý!
