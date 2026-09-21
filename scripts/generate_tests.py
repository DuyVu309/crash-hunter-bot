import os

BASE_TEMPLATE = """#!/bin/bash
# __CASE_NAME__
# TODO(Devs): Sửa cái APP_PKG này thành Package Name của App mà anh em đang làm nhé!
APP_PKG="com.dramable.shorts.reels.viral"
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
adb logcat -d > $LOG_DIR/${CASE_ID}_full_logcat.txt
adb shell dumpsys meminfo $APP_PKG > $LOG_DIR/${CASE_ID}_mem_after.txt
adb shell dumpsys gfxinfo $APP_PKG > $LOG_DIR/${CASE_ID}_gfx.txt
adb shell dumpsys activity activities | grep "Hist" > $LOG_DIR/${CASE_ID}_backstack.txt

# Filter logs
grep -i "com.dramable\|FATAL EXCEPTION\|ANR\|OutOfMemory\|SQLite\|StrictMode\|CancellationException\|AdError\|DownloadService\|WebView\|NavController\|IllegalArgument\|IllegalState" $LOG_DIR/${CASE_ID}_full_logcat.txt > $LOG_DIR/${CASE_ID}_filtered.txt

adb shell am force-stop $APP_PKG
echo "$CASE_ID complete."
"""

scripts = {
    "01_lifecycle": ("App Lifecycle & Memory", """for i in {1..20}; do
  adb shell monkey -p $APP_PKG -c android.intent.category.LAUNCHER 1
  sleep 2
  adb shell input keyevent KEYCODE_HOME
  sleep 1
  adb shell input keyevent KEYCODE_APP_SWITCH
  sleep 1
  adb shell monkey -p $APP_PKG -c android.intent.category.LAUNCHER 1
  sleep 2
  adb shell settings put system user_rotation 1
  sleep 1
  adb shell settings put system user_rotation 0
  sleep 1
done"""),
    "02_video_feed": ("Video Feed Fling", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
for i in {1..30}; do
  adb shell input swipe 540 1800 540 300 50
  sleep 0.1
done"""),
    "03_network_toggle": ("Network Toggle", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
for i in {1..10}; do
  adb shell svc wifi disable
  sleep 2
  adb shell svc wifi enable
  sleep 5
done"""),
    "04_db_io": ("Database I/O Spam", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
for i in {1..20}; do
  adb shell input tap 900 1800
  sleep 0.1
done"""),
    "05_search_ime": ("Search IME Spam", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
adb shell input tap 900 100
sleep 2
for i in {1..5}; do
  adb shell input text "unicode_test_%s"
  sleep 0.2
  for j in {1..15}; do adb shell input keyevent 67; done
done"""),
    "06_nav_spam": ("2 Man De Nhau", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
for i in {1..100}; do
  adb shell input tap 540 1200
done
sleep 2"""),
    "07_reward_race": ("Reward Ad Callback Race", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
for i in {1..30}; do
  adb shell input tap 540 800
  sleep 0.5
  adb shell input keyevent 4
  sleep 0.3
done"""),
    "08_deeplink_bom": ("DeepLink Bom", """for i in {1..15}; do
  adb shell am start -W -a android.intent.action.VIEW -d "shortdrama://watch?id=series_$i" $APP_PKG
  sleep 0.3
done"""),
    "09_bottom_sheet": ("Bottom Sheet Spam", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
adb shell input tap 540 1200
sleep 2
for i in {1..50}; do
  adb shell input swipe 540 1800 540 600 100
  sleep 0.2
  adb shell input swipe 540 600 540 1800 100
  sleep 0.2
done"""),
    "10_download_kill": ("Download Service Stress", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
adb shell input tap 540 1200
sleep 2
for i in {1..10}; do
  adb shell input tap 100 1500
  sleep 0.2
done
adb shell am force-stop $APP_PKG
sleep 2
adb shell am start -n $APP_PKG/.MainActivity"""),
    "11_tab_switch": ("Tab Switching Fury", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
for i in {1..30}; do
  adb shell input tap 180 150
  sleep 0.05
  adb shell input tap 540 150
  sleep 0.05
  adb shell input tap 900 150
  sleep 0.05
done"""),
    "12_rate_dialog": ("Rate App Dialog Spam", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
adb shell input tap 900 1900
sleep 1
for i in {1..30}; do
  adb shell input tap 540 600
  sleep 0.3
  adb shell input keyevent 4
  sleep 0.1
done"""),
    "13_share_resume": ("Share Intent + Resume Ad", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
adb shell input tap 540 1200
sleep 2
for i in {1..10}; do
  adb shell input tap 900 1500
  sleep 1
  adb shell input keyevent 4
  sleep 0.5
done"""),
    "14_mylist_race": ("MyList Edit Mode Race", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
adb shell input tap 700 1900
sleep 1
for i in {1..15}; do
  adb shell input tap 200 150
  adb shell input tap 900 100
  adb shell input tap 540 400
  adb shell input tap 540 150
  sleep 0.1
  adb shell input tap 540 400
  adb shell input tap 540 1900
  sleep 0.1
done"""),
    "15_webview_rotate": ("WebView + Orientation Change", """adb shell am start -n $APP_PKG/.MainActivity
sleep 3
adb shell input tap 900 1900
sleep 1
adb shell input tap 540 800
sleep 3
for i in {1..15}; do
  adb shell settings put system accelerometer_rotation 0
  adb shell settings put system user_rotation 1
  sleep 1
  adb shell settings put system user_rotation 0
  sleep 1
done""")
}

master = "#!/bin/bash\n"
os.makedirs("scripts/subagent", exist_ok=True)
for case_id, (name, logic) in scripts.items():
    content = BASE_TEMPLATE.replace("__CASE_NAME__", name).replace("__CASE_ID__", case_id).replace("__LOGIC__", logic)
    path = f"scripts/subagent/{case_id}.sh"
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)
    master += f"bash {path}\n"

with open("scripts/subagent/run_all.sh", "w") as f:
    f.write(master)
os.chmod("scripts/subagent/run_all.sh", 0o755)
print("Generated 15 test scripts and run_all.sh in scripts/subagent/")
