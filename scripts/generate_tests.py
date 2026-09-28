import os
import re

# ==============================================================================
# 1. TỰ ĐỘNG KHÁM PHÁ (AUTO-DISCOVERY)
# ==============================================================================

def get_application_id():
    # Tìm kiếm linh hoạt trong build.gradle hoặc build.gradle.kts
    gradle_paths = ["app/build.gradle.kts", "app/build.gradle"]
    for path in gradle_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read()
                # Match: applicationId = "com.example.app" hoặc applicationId "com.example.app"
                match = re.search(r'applicationId\s*=?\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
    
    # Dự phòng: đọc từ AndroidManifest.xml (các project cũ)
    manifest_path = "app/src/main/AndroidManifest.xml"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            content = f.read()
            match = re.search(r'package=["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
                
    print("WARNING: Không thể tự động tìm thấy Package ID. Vui lòng cấu hình thủ công.")
    return "com.example.app"

def get_deep_links():
    links = []
    manifest_path = "app/src/main/AndroidManifest.xml"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            content = f.read()
            # Tìm tất cả các thẻ <data scheme="..." host="..." />
            matches = re.finditer(r'<data[^>]*android:scheme=["\']([^"\']+)["\'][^>]*android:host=["\']([^"\']+)["\']', content)
            for match in matches:
                scheme = match.group(1)
                host = match.group(2)
                links.append(f"{scheme}://{host}")
    return links

APP_PKG = get_application_id()
print(f"[*] Đã tự động phát hiện Package: {APP_PKG}")

discovered_links = get_deep_links()
if discovered_links:
    print(f"[*] Đã tự động phát hiện DeepLinks: {', '.join(discovered_links)}")

# ==============================================================================
# 2. KHỞI TẠO TEST CASES
# ==============================================================================

BASE_TEMPLATE = """#!/bin/bash
# __CASE_NAME__
APP_PKG="__APP_PKG__"
LOG_DIR="logs/subagent"
CASE_ID="__CASE_ID__"

echo "Starting $CASE_ID: __CASE_NAME__"
adb logcat -c
adb shell dumpsys meminfo $APP_PKG > $LOG_DIR/${CASE_ID}_mem_before.txt
adb shell dumpsys gfxinfo $APP_PKG reset

# === TEST LOGIC START ===
__LOGIC__
# === TEST LOGIC END ===

echo "Dumping logs for $CASE_ID..."
# Nâng cấp: Tóm gọn mọi log có chữ Timber_ để truy vết tới từng dòng code!
adb logcat -d > $LOG_DIR/${CASE_ID}_full_logcat.txt
grep -E -i "Timber_|FATAL EXCEPTION|ANR|OutOfMemory|SQLite|StrictMode|CancellationException|AdError|DownloadService|WebView|NavController|IllegalArgument|IllegalState" $LOG_DIR/${CASE_ID}_full_logcat.txt > $LOG_DIR/${CASE_ID}_filtered.txt

adb shell dumpsys meminfo $APP_PKG > $LOG_DIR/${CASE_ID}_mem_after.txt
adb shell dumpsys activity activities | grep "Hist" > $LOG_DIR/${CASE_ID}_backstack.txt

adb shell am force-stop $APP_PKG
echo "$CASE_ID complete."
"""

scripts = {
    "01_universal_chaos": ("Universal Chaos Fuzzing", """# Tự động gõ phím ngẫu nhiên, xoay màn hình, tắt mạng
for i in {1..10}; do
  adb shell monkey -p $APP_PKG -c android.intent.category.LAUNCHER 100
  sleep 1
  adb shell settings put system user_rotation 1
  sleep 0.5
  adb shell settings put system user_rotation 0
  sleep 0.5
done"""),
}

# Tự động sinh kịch bản ném bom DeepLink
if discovered_links:
    deeplink_logic = ""
    for link in discovered_links:
        deeplink_logic += f'adb shell am start -W -a android.intent.action.VIEW -d "{link}?id=test_123" $APP_PKG\nsleep 1\n'
    scripts["02_auto_deeplink_bom"] = ("Auto DeepLink Fuzzing", deeplink_logic)
else:
    scripts["02_auto_deeplink_bom"] = ("Auto DeepLink Fuzzing", "echo 'No deeplinks found.'")

master = "#!/bin/bash\n"
os.makedirs("scripts/subagent", exist_ok=True)
for case_id, (name, logic) in scripts.items():
    content = BASE_TEMPLATE.replace("__CASE_NAME__", name).replace("__CASE_ID__", case_id).replace("__LOGIC__", logic).replace("__APP_PKG__", APP_PKG)
    path = f"scripts/subagent/{case_id}.sh"
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)
    master += f"bash {path}\n"

with open("scripts/subagent/run_all.sh", "w") as f:
    f.write(master)
os.chmod("scripts/subagent/run_all.sh", 0o755)
print("[*] Đã sinh xong kịch bản test tự động!")
