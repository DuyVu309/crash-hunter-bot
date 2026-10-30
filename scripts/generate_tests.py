#!/usr/bin/env python3
import os
import sys

# Thêm đường dẫn core vào sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
from discovery import ProjectDiscovery

# ==============================================================================
# 1. TỰ ĐỘNG KHÁM PHÁ (AUTO-DISCOVERY)
# ==============================================================================

target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
discovery = ProjectDiscovery(target_dir)
env_info = discovery.discover_all()

APP_PKG = env_info["package_id"] or "com.example.app"
DEVICE_ID = env_info["device_id"]
SCREEN_W = env_info["screen_width"]
SCREEN_H = env_info["screen_height"]
DEEP_LINKS = env_info["deep_links"]

print(f"[*] Đã tự động phát hiện:")
print(f"    - Package ID: {APP_PKG}")
print(f"    - Device: {DEVICE_ID or 'Default ADB Device'}")
print(f"    - Screen Resolution: {SCREEN_W}x{SCREEN_H}")
if DEEP_LINKS:
    print(f"    - DeepLinks: {', '.join(DEEP_LINKS)}")

# ==============================================================================
# 2. KHỞI TẠO TEMPLATE NỘI SUY TỌA ĐỘ THEO TỶ LỆ MÀN HÌNH (ZERO HARDCODE)
# ==============================================================================

DEVICE_PARAM = f"-s {DEVICE_ID}" if DEVICE_ID else ""

BASE_TEMPLATE = r"""#!/bin/bash
# __CASE_NAME__
APP_PKG="__APP_PKG__"
LOG_DIR="logs/subagent"
CASE_ID="__CASE_ID__"
ADB="adb __DEVICE_PARAM__"

# Tự động tính toán tọa độ theo tỷ lệ màn hình thực tế (Chống toạ độ mù)
RAW_SIZE=$($ADB shell wm size 2>/dev/null | awk '{print $3}' | tail -n 1)
SCREEN_W=$(echo "$RAW_SIZE" | cut -d'x' -f1)
SCREEN_H=$(echo "$RAW_SIZE" | cut -d'x' -f2)
SCREEN_W=${SCREEN_W:-__SCREEN_W__}
SCREEN_H=${SCREEN_H:-__SCREEN_H__}

# Dynamic Relative Coordinates
X_CENTER=$((SCREEN_W * 50 / 100))
X_LEFT=$((SCREEN_W * 20 / 100))
X_RIGHT=$((SCREEN_W * 85 / 100))

Y_TOP_BAR=$((SCREEN_H * 8 / 100))
Y_TOP=$((SCREEN_H * 20 / 100))
Y_CENTER=$((SCREEN_H * 50 / 100))
Y_BOTTOM=$((SCREEN_H * 75 / 100))
Y_BOTTOM_BAR=$((SCREEN_H * 90 / 100))

echo "Starting $CASE_ID: __CASE_NAME__ (Target: $SCREEN_W x $SCREEN_H)"
$ADB logcat -c
$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
$ADB shell dumpsys meminfo $APP_PKG > $LOG_DIR/${CASE_ID}_mem_before.txt
$ADB shell dumpsys gfxinfo $APP_PKG reset > /dev/null 2>&1 || true

# === TEST LOGIC START ===
__LOGIC__
# === TEST LOGIC END ===

echo "Dumping diagnostic logs for $CASE_ID..."
$ADB logcat -d > $LOG_DIR/${CASE_ID}_full_logcat.txt
$ADB shell dumpsys meminfo $APP_PKG > $LOG_DIR/${CASE_ID}_mem_after.txt
$ADB shell dumpsys gfxinfo $APP_PKG > $LOG_DIR/${CASE_ID}_gfx.txt
$ADB shell dumpsys activity activities | grep "Hist" > $LOG_DIR/${CASE_ID}_backstack.txt

# Filter logs (Tóm gọn Timber_ để truy vết tới từng dòng code File.kt:Line)
grep -i "Timber_\|FATAL EXCEPTION\|ANR\|OutOfMemory\|SQLite\|StrictMode\|CancellationException\|MediaCodec\|AudioRecord\|AudioCaptureManager\|NavController\|IllegalArgument\|IllegalState" $LOG_DIR/${CASE_ID}_full_logcat.txt > $LOG_DIR/${CASE_ID}_filtered.txt

$ADB shell am force-stop $APP_PKG
echo "$CASE_ID complete."
"""

scripts = {
    "01_lifecycle": ("App Lifecycle & Screen Rotation Stress", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 3
for i in {1..15}; do
  $ADB shell input keyevent KEYCODE_HOME
  sleep 1
  $ADB shell input keyevent KEYCODE_APP_SWITCH
  sleep 1
  $ADB shell monkey -p $APP_PKG -c android.intent.category.LAUNCHER 1
  sleep 2
  $ADB shell settings put system accelerometer_rotation 0
  $ADB shell settings put system user_rotation 1
  sleep 1
  $ADB shell settings put system user_rotation 0
  sleep 1
done"""),
    "02_monkey_stress": ("Native ADB Monkey Chaos Crash Hunting", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
$ADB shell monkey -p $APP_PKG \\
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
    "03_recording_service_stress": ("Foreground Service & Codec Stress", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
$ADB shell pm grant $APP_PKG android.permission.RECORD_AUDIO 2>/dev/null || true
$ADB shell pm grant $APP_PKG android.permission.POST_NOTIFICATIONS 2>/dev/null || true

for i in {1..10}; do
  # Tap Record action (Bottom center)
  $ADB shell input tap $X_CENTER $Y_BOTTOM_BAR
  sleep 2
  # Tap Pause/Resume
  $ADB shell input tap $X_LEFT $Y_BOTTOM_BAR
  sleep 1
  $ADB shell input tap $X_LEFT $Y_BOTTOM_BAR
  sleep 2
  # Background app while service is active
  $ADB shell input keyevent KEYCODE_HOME
  sleep 2
  # Reopen app
  $ADB shell monkey -p $APP_PKG -c android.intent.category.LAUNCHER 1
  sleep 1
  # Tap Stop / Save
  $ADB shell input tap $X_RIGHT $Y_BOTTOM_BAR
  sleep 2
done"""),
    "04_network_toggle_workmanager": ("Network Drop during AI / Background Processing", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..8}; do
  $ADB shell cmd connectivity airplane-mode enable 2>/dev/null || $ADB shell svc wifi disable
  sleep 2
  $ADB shell cmd connectivity airplane-mode disable 2>/dev/null || $ADB shell svc wifi enable
  sleep 4
done"""),
    "05_folder_db_io_stress": ("Room Database Mutation & Concurrency Stress", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..15}; do
  # Tap Add / Create action
  $ADB shell input tap $X_RIGHT $Y_TOP_BAR
  sleep 0.5
  $ADB shell input text "Stress_Record_$i"
  sleep 0.3
  $ADB shell input tap $X_CENTER $Y_CENTER
  sleep 0.5
done"""),
    "06_search_ime_stress": ("Search Input & IME Keyboard Stress", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
$ADB shell input tap $X_CENTER $Y_TOP_BAR
sleep 1
for i in {1..5}; do
  $ADB shell input text "Stress_Search_Query_$i"
  sleep 0.5
  for j in {1..25}; do $ADB shell input keyevent 67; done
  sleep 0.2
done
$ADB shell input keyevent KEYCODE_BACK"""),
    "07_navigation_backstack_spam": ("Compose Navigation & Fast Backstack Pop", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..30}; do
  $ADB shell input tap $X_CENTER $Y_CENTER
  sleep 0.3
  $ADB shell input keyevent KEYCODE_BACK
  sleep 0.2
  $ADB shell input tap $X_RIGHT $Y_TOP_BAR
  sleep 0.3
  $ADB shell input keyevent KEYCODE_BACK
  sleep 0.2
done"""),
    "08_audio_player_timeline_seek": ("Audio Player Seekbar Dragging & Timeline State Stress", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
$ADB shell input tap $X_CENTER $Y_CENTER
sleep 2
for i in {1..20}; do
  $ADB shell input tap $X_CENTER $Y_BOTTOM_BAR
  sleep 0.2
  $ADB shell input swipe $X_LEFT $Y_BOTTOM $X_RIGHT $Y_BOTTOM 50
  sleep 0.1
  $ADB shell input swipe $X_RIGHT $Y_BOTTOM $X_LEFT $Y_BOTTOM 50
  sleep 0.1
done"""),
    "09_bottom_sheet_modal_spam": ("Compose ModalBottomSheet & Dialog Stress", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..25}; do
  $ADB shell input tap $X_RIGHT $Y_CENTER
  sleep 0.3
  $ADB shell input tap $X_CENTER $Y_TOP_BAR
  sleep 0.2
done"""),
    "10_upload_worker_kill_restore": ("Universal Upload WorkManager Kill & Recovery", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
$ADB shell input tap $X_RIGHT $Y_BOTTOM_BAR
sleep 1
$ADB shell am force-stop $APP_PKG
sleep 2
$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2"""),
    "11_tab_switch_fury": ("Multi-Tab Fast Switching", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..20}; do
  $ADB shell input tap $((SCREEN_W * 25 / 100)) $Y_TOP_BAR
  sleep 0.05
  $ADB shell input tap $((SCREEN_W * 50 / 100)) $Y_TOP_BAR
  sleep 0.05
  $ADB shell input tap $((SCREEN_W * 75 / 100)) $Y_TOP_BAR
  sleep 0.05
done"""),
    "12_oom_large_note_stress": ("Long List Fling & PSS Memory Check", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..30}; do
  $ADB shell input swipe $X_CENTER $Y_BOTTOM $X_CENTER $Y_TOP 50
  sleep 0.1
  $ADB shell input swipe $X_CENTER $Y_TOP $X_CENTER $Y_BOTTOM 50
  sleep 0.1
done"""),
    "13_paywall_back_race": ("Paywall Navigation Race", """for i in {1..10}; do
  $ADB shell am start -n $APP_PKG/com.vio.paywall.presentation.ui.PaywallActivity 2>/dev/null || $ADB shell am start -n $APP_PKG/.MainActivity
  sleep 0.5
  $ADB shell input keyevent KEYCODE_BACK
  sleep 0.2
  $ADB shell input keyevent KEYCODE_BACK
  sleep 0.3
done"""),
    "14_locale_config_change": ("Theme & Font Scale Configuration Stress", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..8}; do
  $ADB shell settings put system font_scale 1.3
  sleep 1
  $ADB shell settings put system font_scale 1.0
  sleep 1
done"""),
    "15_full_chaos_monkey": ("Low Memory Killer + Chaos Monkey", """$ADB shell am start -n $APP_PKG/.MainActivity
sleep 2
for i in {1..5}; do
  $ADB shell am send-trim-memory $APP_PKG RUNNING_CRITICAL
  sleep 1
  $ADB shell monkey -p $APP_PKG --pct-touch 50 --pct-motion 30 --pct-appswitch 20 -v 500
  sleep 1
done""")
}

# Tự động thêm kịch bản DeepLink nếu dự án có cấu hình DeepLinks
if DEEP_LINKS:
    links_payload = "\n".join([f'  $ADB shell am start -W -a android.intent.action.VIEW -d "{link}/fuzz_$i" $APP_PKG\n  sleep 0.3' for link in DEEP_LINKS])
    scripts["16_auto_deeplink_bom"] = ("DeepLink Fuzzing Bomb", f"""for i in {{1..15}}; do
{links_payload}
done""")

# ==============================================================================
# 3. XUẤT RA TOÀN BỘ SCRIPTS VÀ RUN_ALL.SH
# ==============================================================================

def generate(output_dir="scripts/subagent"):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("logs/subagent", exist_ok=True)

    for case_id, (name, logic) in scripts.items():
        content = BASE_TEMPLATE.replace("__CASE_ID__", case_id)
        content = content.replace("__CASE_NAME__", name)
        content = content.replace("__APP_PKG__", APP_PKG)
        content = content.replace("__DEVICE_PARAM__", DEVICE_PARAM)
        content = content.replace("__SCREEN_W__", str(SCREEN_W))
        content = content.replace("__SCREEN_H__", str(SCREEN_H))
        content = content.replace("__LOGIC__", logic)

        file_path = os.path.join(output_dir, f"{case_id}.sh")
        with open(file_path, "w") as f:
            f.write(content)
        os.chmod(file_path, 0o755)

    # Master runner script
    master = f"""#!/bin/bash
set -e
mkdir -p logs/subagent
APP_PKG="{APP_PKG}"
ADB="adb {DEVICE_PARAM}"

echo "===================================================================="
echo " 🚀 Crash Hunter 2.0: Running All Stress Test Cases for $APP_PKG"
echo " Target Resolution: {SCREEN_W}x{SCREEN_H}"
echo "===================================================================="

REPORT_FILE="CRASH_REPORT_FINAL.md"
echo "# Crash Hunter Stress Test Report" > "$REPORT_FILE"
echo "> Target Package: '$APP_PKG'" >> "$REPORT_FILE"
echo "> Screen Resolution: '{SCREEN_W}x{SCREEN_H}'" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "| Case ID | Test Name | Status | Fatal Crashes | RAM Delta | Backstack |" >> "$REPORT_FILE"
echo "|---------|-----------|--------|---------------|-----------|-----------|" >> "$REPORT_FILE"

TOTAL_CRASHES=0
TOTAL_LEAKS=0

for case_sh in $(ls {output_dir}/[0-9]*.sh | sort); do
    cid=$(basename "$case_sh" .sh)
    echo ""
    echo ">>> Running $cid..."
    bash "$case_sh" || true
    
    filtered="logs/subagent/${{cid}}_filtered.txt"
    mem_before="logs/subagent/${{cid}}_mem_before.txt"
    mem_after="logs/subagent/${{cid}}_mem_after.txt"
    backstack="logs/subagent/${{cid}}_backstack.txt"
    
    crashes=0
    if [ -f "$filtered" ]; then
        crashes=$(grep -c "FATAL EXCEPTION" "$filtered" 2>/dev/null || true)
        crashes=${{crashes:-0}}
        TOTAL_CRASHES=$((TOTAL_CRASHES + crashes))
    fi
    
    pss_b=0
    if [ -f "$mem_before" ]; then
        pss_b=$(grep -i "TOTAL PSS:" "$mem_before" | head -n1 | awk '{{print $3}}' 2>/dev/null || echo 0)
        pss_b=${{pss_b:-0}}
    fi
    pss_a=0
    if [ -f "$mem_after" ]; then
        pss_a=$(grep -i "TOTAL PSS:" "$mem_after" | head -n1 | awk '{{print $3}}' 2>/dev/null || echo 0)
        pss_a=${{pss_a:-0}}
    fi
    delta_kb=0
    if [ "$pss_a" -gt 0 ] && [ "$pss_b" -gt 0 ]; then
        delta_kb=$((pss_a - pss_b))
    fi
    delta_mb=$((delta_kb / 1024))
    
    hist_count=0
    if [ -f "$backstack" ]; then
        hist_count=$(grep -c -i "$APP_PKG/.MainActivity" "$backstack" 2>/dev/null || true)
        hist_count=${{hist_count:-0}}
    fi
    
    status="PASS"
    if [ "$crashes" -gt 0 ]; then
        timber_line=$(grep -E -o "Timber_[a-zA-Z0-9_]+: \\([a-zA-Z0-9_]+\\.kt:[0-9]+\\)" "$filtered" 2>/dev/null | head -n 1 || true)
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
    
    name=$(head -n 2 "$case_sh" | tail -n 1 | sed 's/# //')
    echo "| '$cid' | $name | **$status** | $crashes | ${{delta_mb}}MB | $hist_count inst |" >> "$REPORT_FILE"
done

echo "" >> "$REPORT_FILE"
echo "### Overall Verdict:" >> "$REPORT_FILE"
echo "- Total Fatal Crashes: $TOTAL_CRASHES" >> "$REPORT_FILE"
echo "- Total Leaks (RAM/Nav): $TOTAL_LEAKS" >> "$REPORT_FILE"

cat "$REPORT_FILE"
"""

    with open(os.path.join(output_dir, "run_all.sh"), "w") as f:
        f.write(master)
    os.chmod(os.path.join(output_dir, "run_all.sh"), 0o755)
    print(f"[*] Đã sinh xong {len(scripts)} kịch bản test (100% tọa độ động) trong {output_dir}/")

if __name__ == '__main__':
    generate()
