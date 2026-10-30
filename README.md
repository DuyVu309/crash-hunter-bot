# 🎯 Crash Hunter 2.0 — Antigravity QA & Stress Engine

Hệ thống kiểm thử tự động toàn diện dành cho Android (Dual-Engine QA Automation): Kết hợp **Maestro Semantic UI Testing** và **Dynamic ADB Chaos/Monkey Fuzzing** nhằm săn lùng và triệt tiêu các lỗi tử huyệt: **Crash (FATAL/ANR)**, **RAM Leak (PSS Delta)**, **Navigation Backstack Leak**, và **State/Coroutine Race Conditions**.

---

## ⚡ Tính Năng Đột Phá Trên Crash Hunter 2.0

1. **Kiến Trúc Dual-Engine Mạnh Mẽ**:
   - **Engine 1 (Maestro Semantic UI)**: Tự động phát hiện các luồng `.maestro/*.yaml` trong dự án và thực thi kịch bản UI ngữ nghĩa mượt mà, đo lường RAM PSS và rò rỉ Backstack trước/sau mỗi flow.
   - **Engine 2 (Dynamic ADB Chaos Fuzzing)**: 16 kịch bản dội bom phần cứng, giật xoay màn hình, ngắt mạng, kill process, và 5000 sự kiện Monkey ngẫu nhiên.
2. **100% Dynamic Coordinates (Nội Suy Tọa Độ Tỷ Lệ)**:
   - Tự động lấy độ phân giải thực tế của thiết bị qua `adb shell wm size`.
   - Tính toán tọa độ tương đối (`$X_CENTER`, `$X_LEFT`, `$X_RIGHT`, `$Y_TOP`, `$Y_CENTER`, `$Y_BOTTOM_BAR`), loại bỏ hoàn toàn tình trạng toạ độ mù/lệch màn hình trên các thiết bị gập, máy tính bảng hoặc flagship độ phân giải cao.
3. **Auto-Discovery Thông Minh (Zero-Config)**:
   - Tự động quét và nhận diện **Application ID** từ `build.gradle.kts`, `build.gradle`, hoặc `AndroidManifest.xml`.
   - Tự động phát hiện **Thiết bị ADB** đang kết nối.
   - Tự động phát hiện **DeepLink schemes** từ `AndroidManifest.xml` để tự động sinh test case DeepLink Fuzzing.
   - Tự động định vị binary **Maestro CLI**.
4. **Chỉ Điểm Tận Gốc (Line-Level Traceability)**:
   - Tự động bóc tách log Timber dạng `(FileName.kt:LineNumber)` để dev click thẳng vào dòng code gây lỗi trên Android Studio.
5. **Báo Cáo Nghiệm Thu Hợp Nhất (`CRASH_REPORT_FINAL.md`)**:
   - Tự động đo lường độ chênh lệch RAM PSS (Delta MB), cảnh báo rò rỉ RAM khi vượt ngưỡng 100MB.
   - Đếm số lượng Activity trong Backstack để phát hiện trùng lặp Activity khi điều hướng (Navigation Leak).

---

## 🚀 Cách Dùng Nhanh (1-Touch CLI Runner)

### Cách 1: Chạy Độc Lập Từ Repo Này (Khuyến nghị cho Dev)

Clone repo này về máy, cắm máy ảo/máy thật qua ADB và chạy:

```bash
# 1. Chạy quét và test toàn bộ trên dự án Android chỉ định:
./hunt.sh -d /path/to/your/AndroidProject

# 2. Hoặc cd vào dự án Android và chạy:
/path/to/crash-hunter-bot/hunt.sh

# 3. Chỉ chạy kịch bản Maestro Semantic UI:
./hunt.sh -d /path/to/your/AndroidProject -m maestro

# 4. Chỉ chạy bộ ADB Chaos/Monkey Fuzzing:
./hunt.sh -d /path/to/your/AndroidProject -m adb
```

### Cách 2: Tích Hợp Làm Skill Cho Antigravity AI / Subagent

1. Copy toàn bộ thư mục này vào `.agents/skills/crash-hunter-bot/` trong repo dự án của bạn.
2. Mở Antigravity IDE, chat:
   > *"Chạy skill crash-hunter-bot để kiểm tra độ ổn định của app"*
3. AI sẽ tự động kích hoạt subagent, chạy kiểm thử ngầm và phân tích báo cáo `CRASH_REPORT_FINAL.md` gửi lại cho bạn.

---

## 📋 Danh Mục 16 Kịch Bản ADB Chaos Fuzzing

| Mã Case | Tên Kịch Bản | Mục Tiêu & Cơ Chế Kiểm Thử |
|---|---|---|
| `01_lifecycle` | App Lifecycle & Rotation | Xoay màn hình 0°/90° liên tục, giật Home/App Switch kiểm tra rò rỉ Activity |
| `02_monkey_stress` | Native ADB Monkey | 5000 random touch/gesture events (throttle 100ms) |
| `03_recording_service` | Foreground Service Stress | Kích hoạt và kiểm tra Service chạy nền, tương tác MediaCodec & Notification |
| `04_network_toggle` | Network Drop & WorkManager | Bật/tắt WiFi và Data khi Worker nền đang đồng bộ hoặc xử lý AI |
| `05_folder_db_io` | Room Database Rapid Mutations | Thao tác ghi/sửa/xoá nhanh để phát hiện khóa DB hoặc SQLiteBusyException |
| `06_search_ime` | Search IME & Keyboard Stress | Gõ spam Unicode, Emoji, ký tự lạ và Backspace liên tục |
| `07_nav_backstack` | Navigation Backstack Spam | Nhấn Back cực nhanh kiểm tra Duplicate Activity / ViewModel leak |
| `08_audio_player` | Player Timeline Seekbar | Kéo thanh Seekbar liên tục để kiểm tra High-Frequency State Recomposition |
| `09_bottom_sheet` | BottomSheet & Dialog Spam | Đóng mở liên tục BottomSheet/Dialog để bắt lỗi WindowManager leak |
| `10_upload_worker` | Upload Worker Kill & Restore | Ép dừng tiến trình khi đang upload, kiểm tra khôi phục trạng thái |
| `11_tab_switch_fury` | Multi-Tab Fast Switching | Chuyển tab liên tục ở Bottom Navigation |
| `12_oom_large_note` | Long List Fling & PSS Memory | Cuộn danh sách cực nhanh với quán tính lớn, đo lường RAM PSS |
| `13_paywall_back` | Paywall Navigation Race | Mở Paywall rồi bấm Back tức thì để bắt lỗi Race Condition |
| `14_locale_config` | Theme & Font Scale Stress | Đổi Dark Mode, thay đổi tỷ lệ chữ hệ thống khi UI đang mở |
| `15_full_chaos` | Memory Trimming & Monkey | Kích hoạt `am send-trim-memory RUNNING_CRITICAL` kết hợp Monkey |
| `16_auto_deeplink` | DeepLink Bomb | Tự động sinh nếu phát hiện DeepLink scheme trong AndroidManifest |

---

## 💡 Bí Kíp Tối Ưu Với Timber (Truy Vết Đến Từng Dòng Code)

Để Crash Hunter nhặt ra **CHÍNH XÁC dòng code gây lỗi** `(FileName.kt:LineNumber)` trên báo cáo Markdown:

### Bước 1: Cấu hình Timber trong `Application.kt`
```kotlin
if (BuildConfig.DEBUG) {
    Timber.plant(object : Timber.DebugTree() {
        override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {
            // Lấy stackTrace ở index = 5 (nếu gọi qua Extension)
            val element = Throwable().stackTrace.getOrNull(5)
            val customMessage = if (element != null) {
                "(${element.fileName}:${element.lineNumber}) $message"
            } else message
            super.log(priority, tag, customMessage, t)
        }
    })
}
```

### Bước 2: Tạo Extension `LogExt.kt`
```kotlin
import timber.log.Timber

fun Any.logd(tag: String, message: Any?) {
    Timber.tag(this::class.java.simpleName).d("$tag ---- ${message ?: "null"}")
}

fun Any.logw(tag: String, message: Any?) {
    Timber.tag(this::class.java.simpleName).w("$tag ---- ${message ?: "null"}")
}

fun Any.loge(tag: String, message: Any?, throwable: Throwable? = null) {
    Timber.tag(this::class.java.simpleName).e(throwable, "$tag ---- ${message ?: "null"}")
}
```

Bất cứ khi nào app xảy ra crash hoặc warning, bot sẽ tự động bắt định dạng:
`D/Timber_SearchViewModel: (SearchViewModel.kt:157) CrashHunter ---- INTENT_TRAP: OnQueryChange`
và xuất thẳng link `(SearchViewModel.kt:157)` lên báo cáo nghiệm thu!
