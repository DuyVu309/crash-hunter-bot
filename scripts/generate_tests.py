import os
import glob
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

BASE_TEMPLATE = r"""#!/bin/bash
# __CASE_NAME__
APP_PKG="__APP_PKG__"
LOG_DIR="logs/subagent"
CASE_ID="__CASE_ID__"

echo "Starting $CASE_ID: __CASE_NAME__"
adb logcat -c
adb shell am start -n $APP_PKG/.MainActivity
sleep 2
adb shell dumpsys meminfo $APP_PKG > $LOG_DIR/${CASE_ID}_mem_before.txt
adb shell dumpsys gfxinfo $APP_PKG reset

# === TEST LOGIC START ===
__LOGIC__
# === TEST LOGIC END ===

echo "Dumping logs for $CASE_ID..."
adb logcat -d > $LOG_DIR/${CASE_ID}_full_logcat.txt
adb shell dumpsys meminfo $APP_PKG > $LOG_DIR/${CASE_ID}_mem_after.txt
adb shell dumpsys gfxinfo $APP_PKG > $LOG_DIR/${CASE_ID}_gfx.txt
adb shell dumpsys activity activities | grep "Hist" > $LOG_DIR/${CASE_ID}_backstack.txt

# Filter logs (Tóm gọn Timber_ để truy vết tới từng dòng code File.kt:Line)
grep -i "Timber_\|FATAL EXCEPTION\|ANR\|OutOfMemory\|SQLite\|StrictMode\|CancellationException\|MediaCodec\|AudioRecord\|AudioCaptureManager\|NavController\|IllegalArgument\|IllegalState" $LOG_DIR/${CASE_ID}_full_logcat.txt > $LOG_DIR/${CASE_ID}_filtered.txt

adb shell am force-stop $APP_PKG
echo "$CASE_ID complete."
"""

scripts = {
    "01_lifecycle": ("App Lifecycle & Screen Rotation Stress", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
for i in {1..15}; do
  adb shell input keyevent KEYCODE_HOME
  sleep 1
  adb shell input keyevent KEYCODE_APP_SWITCH
  sleep 1
  adb shell monkey -p $APP_PKG -c android.intent.category.LAUNCHER 1
  sleep 2
  adb shell settings put system accelerometer_rotation 0
  adb shell settings put system user_rotation 1
  sleep 1
  adb shell settings put system user_rotation 0
  sleep 1
done"""),
    "02_monkey_stress": ("Native ADB Monkey Crash Hunting", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
adb shell monkey -p $APP_PKG \\
  --pct-touch 40 \\
  --pct-motion 25 \\
  --pct-appswitch 15 \\
  --pct-syskeys 5 \\
  --pct-nav 10 \\
  --pct-majornav 5 \\
  --ignore-crashes \\
  --ignore-timeouts \\
  --throttle 100 \\
  -v 5000"""),
    "03_recording_service_stress": ("AudioRecordingService Foreground Service Stress", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
adb shell pm grant $APP_PKG android.permission.RECORD_AUDIO 2>/dev/null || true
adb shell pm grant $APP_PKG android.permission.POST_NOTIFICATIONS 2>/dev/null || true

for i in {1..10}; do
  # Tap Record button
  adb shell input tap 540 2100
  sleep 2
  # Tap Pause button
  adb shell input tap 400 2100
  sleep 1
  # Tap Resume button
  adb shell input tap 400 2100
  sleep 2
  # Background app while recording service is running
  adb shell input keyevent KEYCODE_HOME
  sleep 2
  # Reopen app
  adb shell monkey -p $APP_PKG -c android.intent.category.LAUNCHER 1
  sleep 1
  # Tap Stop/Save button
  adb shell input tap 680 2100
  sleep 2
done"""),
    "04_network_toggle_workmanager": ("Network Drop during AI Processing", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..8}; do
  adb shell cmd connectivity airplane-mode enable 2>/dev/null || adb shell svc wifi disable
  sleep 2
  adb shell cmd connectivity airplane-mode disable 2>/dev/null || adb shell svc wifi enable
  sleep 4
done"""),
    "05_folder_db_io_stress": ("Room Database Folder & Note Rapid Mutations", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..15}; do
  # Tap New Folder
  adb shell input tap 950 150
  sleep 0.5
  adb shell input text "Stress_Folder_$i"
  sleep 0.3
  adb shell input tap 800 1200
  sleep 0.5
done"""),
    "06_search_ime_stress": ("Search Input & IME Keyboard Stress", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
adb shell input tap 540 200
sleep 1
for i in {1..5}; do
  adb shell input text "Ghi_am_cuoc_hop_AI_stress_test_$i"
  sleep 0.5
  for j in {1..25}; do adb shell input keyevent 67; done
  sleep 0.2
done
adb shell input keyevent KEYCODE_BACK"""),
    "07_navigation_backstack_spam": ("Compose Navigation & Fast Backstack Pop", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..30}; do
  adb shell input tap 540 800
  sleep 0.3
  adb shell input keyevent KEYCODE_BACK
  sleep 0.2
  adb shell input tap 950 120
  sleep 0.3
  adb shell input keyevent KEYCODE_BACK
  sleep 0.2
done"""),
    "08_audio_player_timeline_seek": ("Audio Player Seekbar Dragging & High-Frequency State", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
adb shell input tap 540 600
sleep 2
for i in {1..20}; do
  adb shell input tap 540 2100
  sleep 0.2
  adb shell input swipe 100 2000 900 2000 50
  sleep 0.1
  adb shell input swipe 900 2000 200 2000 50
  sleep 0.1
done"""),
    "09_bottom_sheet_modal_spam": ("Compose ModalBottomSheet & Dialog Stress", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..25}; do
  adb shell input tap 980 600
  sleep 0.3
  adb shell input tap 540 200
  sleep 0.2
done"""),
    "10_upload_worker_kill_restore": ("Universal Upload WorkManager Kill & Recovery", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
adb shell input tap 900 2100
sleep 1
adb shell am force-stop $APP_PKG
sleep 2
adb shell am start -n $APP_PKG/.MainActivity
sleep 2"""),
    "11_tab_switch_fury": ("Multi-Tab Fast Switching", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
adb shell input tap 540 600
sleep 2
for i in {1..20}; do
  adb shell input tap 200 350
  sleep 0.05
  adb shell input tap 400 350
  sleep 0.05
  adb shell input tap 600 350
  sleep 0.05
  adb shell input tap 800 350
  sleep 0.05
  adb shell input tap 950 350
  sleep 0.05
done"""),
    "12_oom_large_note_stress": ("Long Transcript Fling & PSS Memory Check", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
adb shell input tap 540 600
sleep 2
for i in {1..30}; do
  adb shell input swipe 540 1800 540 300 50
  sleep 0.1
  adb shell input swipe 540 300 540 1800 50
  sleep 0.1
done"""),
    "13_paywall_back_race": ("Paywall Activity Navigation Race", """for i in {1..10}; do
  adb shell am start -n $APP_PKG/com.vio.paywall.presentation.ui.PaywallActivity 2>/dev/null || adb shell am start -n $APP_PKG/.MainActivity
  sleep 0.5
  adb shell input keyevent KEYCODE_BACK
  sleep 0.2
  adb shell input keyevent KEYCODE_BACK
  sleep 0.3
done"""),
    "14_locale_config_change": ("Theme & Font Scale Configuration Stress", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..8}; do
  adb shell settings put system font_scale 1.3
  sleep 1
  adb shell cmd uimode night yes
  sleep 1
  adb shell settings put system font_scale 1.0
  sleep 1
  adb shell cmd uimode night no
  sleep 1
done"""),
    "15_full_chaos_monkey": ("Low Memory Killer + Chaos Monkey", """adb shell am start -n $APP_PKG/.MainActivity
sleep 2
adb shell am send-trim-memory $APP_PKG RUNNING_CRITICAL
sleep 1
adb shell monkey -p $APP_PKG \\
  --pct-touch 40 \\
  --pct-motion 25 \\
  --pct-appswitch 15 \\
  --pct-syskeys 5 \\
  --pct-nav 10 \\
  --pct-majornav 5 \\
  --ignore-crashes \\
  --ignore-timeouts \\
  --throttle 80 \\
  -v 3000""")
}

# Tự động thêm kịch bản ném bom DeepLink nếu phát hiện
if discovered_links:
    deeplink_logic = ""
    for link in discovered_links:
        deeplink_logic += f'adb shell am start -W -a android.intent.action.VIEW -d "{link}?id=stress_123" $APP_PKG\nsleep 1\n'
    scripts["16_auto_deeplink_bom"] = ("Auto DeepLink Fuzzing", deeplink_logic)

def generate():
    os.makedirs("scripts/subagent", exist_ok=True)
    os.makedirs("logs/subagent", exist_ok=True)
    for old_script in glob.glob("scripts/subagent/*.sh"):
        try:
            os.remove(old_script)
        except OSError:
            pass

    master = f"""#!/bin/bash
# Automated ADB Stress Test Master Runner
APP_PKG="{APP_PKG}"
LOG_DIR="logs/subagent"
mkdir -p "$LOG_DIR"

echo "========================================="
echo "ADB Stress Test Run: $(date)"
echo "Target Package: $APP_PKG"
echo "========================================="

"""
    for case_id, (name, logic) in scripts.items():
        content = BASE_TEMPLATE.replace("__CASE_NAME__", name).replace("__CASE_ID__", case_id).replace("__LOGIC__", logic).replace("__APP_PKG__", APP_PKG)
        path = f"scripts/subagent/{case_id}.sh"
        with open(path, "w") as f:
            f.write(content)
        os.chmod(path, 0o755)
        master += f"echo \"Executing {case_id}: {name}...\"\n"
        master += f"bash scripts/subagent/{case_id}.sh\n\n"

    master += r"""
echo "========================================="
echo "STRESS TEST COMPLETED. ANALYZING LOGS..."
echo "========================================="

REPORT_FILE="CRASH_REPORT_FINAL.md"
echo "# ADB Stress Test Final Report" > "$REPORT_FILE"
echo "**Generated:** $(date)" >> "$REPORT_FILE"
echo "**Package:** $APP_PKG" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| Case ID | Case Name | Status | Crashes | RAM Delta (PSS) | Nav Leaks |" >> "$REPORT_FILE"
echo "| :--- | :--- | :--- | :--- | :--- | :--- |" >> "$REPORT_FILE"

TOTAL_CRASHES=0
TOTAL_LEAKS=0

for case_sh in scripts/subagent/[0-9]*.sh; do
    cid=$(basename "$case_sh" .sh)
    filtered="$LOG_DIR/${cid}_filtered.txt"
    mem_before="$LOG_DIR/${cid}_mem_before.txt"
    mem_after="$LOG_DIR/${cid}_mem_after.txt"
    backstack="$LOG_DIR/${cid}_backstack.txt"
    
    crashes=0
    if [ -f "$filtered" ]; then
        crashes=$(grep -c -i "FATAL EXCEPTION\|OutOfMemory\|MediaCodec.*IllegalState" "$filtered" 2>/dev/null || true)
        crashes=${crashes:-0}
    fi
    TOTAL_CRASHES=$((TOTAL_CRASHES + crashes))
    
    # Calculate RAM delta
    pss_b=0
    pss_a=0
    if [ -f "$mem_before" ]; then
        pss_b=$(grep -i "TOTAL PSS:" "$mem_before" | head -n1 | awk '{print $3}' 2>/dev/null || echo 0)
        pss_b=${pss_b:-0}
    fi
    if [ -f "$mem_after" ]; then
        pss_a=$(grep -i "TOTAL PSS:" "$mem_after" | head -n1 | awk '{print $3}' 2>/dev/null || echo 0)
        pss_a=${pss_a:-0}
    fi
    delta_kb=0
    if [ "$pss_a" -gt 0 ] && [ "$pss_b" -gt 0 ]; then
        delta_kb=$((pss_a - pss_b))
    fi
    delta_mb=$((delta_kb / 1024))
    
    # Nav stack check
    hist_count=0
    if [ -f "$backstack" ]; then
        hist_count=$(grep -c -i "MainActivity" "$backstack" 2>/dev/null || true)
        hist_count=${hist_count:-0}
    fi
    
    status="PASS"
    if [ "$crashes" -gt 0 ]; then
        timber_line=$(grep -E -o "Timber_[a-zA-Z0-9_]+: \([a-zA-Z0-9_]+\.kt:[0-9]+\)" "$filtered" 2>/dev/null | head -n 1 || true)
        if [ -n "$timber_line" ]; then
            status="FAIL ($timber_line)"
        else
            status="FAIL (CRASH)"
        fi
    elif [ "$delta_mb" -gt 100 ]; then
        status="WARN (RAM LEAK)"
        TOTAL_LEAKS=$((TOTAL_LEAKS + 1))
    elif [ "$hist_count" -gt 2 ]; then
        status="WARN (NAV LEAK)"
        TOTAL_LEAKS=$((TOTAL_LEAKS + 1))
    fi
    
    echo "| $cid | $(head -n 2 "$case_sh" | tail -n 1 | sed 's/# //') | $status | $crashes | ${delta_mb}MB | $hist_count inst |" >> "$REPORT_FILE"
done

echo "" >> "$REPORT_FILE"
echo "### Overall Verdict:" >> "$REPORT_FILE"
echo "- Total Crashes: $TOTAL_CRASHES" >> "$REPORT_FILE"
echo "- Total Warnings/Leaks: $TOTAL_LEAKS" >> "$REPORT_FILE"

cat "$REPORT_FILE"
"""

    with open("scripts/subagent/run_all.sh", "w") as f:
        f.write(master)
    os.chmod("scripts/subagent/run_all.sh", 0o755)
    print(f"[*] Đã sinh xong {len(scripts)} kịch bản test và run_all.sh trong scripts/subagent/")

if __name__ == '__main__':
    generate()
