#!/bin/bash
set -e

# ==============================================================================
# 🎯 Crash Hunter 2.0: One-Touch Android Stress & Diagnostic CLI
# ==============================================================================

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="."
MODE="all" # all, maestro, adb

print_help() {
    echo "===================================================================="
    echo " 🎯 Crash Hunter 2.0 CLI — Antigravity QA Engine"
    echo "===================================================================="
    echo "Usage: ./hunt.sh [options]"
    echo ""
    echo "Options:"
    echo "  -d, --dir <path>       Đường dẫn thư mục dự án Android (Mặc định: .)"
    echo "  -m, --mode <mode>      Chế độ chạy: 'all' (Mặc định), 'maestro', hoặc 'adb'"
    echo "  -h, --help             Hiển thị hướng dẫn sử dụng"
    echo ""
    echo "Examples:"
    echo "  ./hunt.sh                     # Tự động quét và chạy toàn bộ trong dự án hiện tại"
    echo "  ./hunt.sh -d ~/NoteAIDemo     # Chạy test trên dự án NoteAIDemo"
    echo "  ./hunt.sh -m maestro          # Chỉ chạy các kịch bản Maestro Semantic UI"
    echo "  ./hunt.sh -m adb              # Chỉ chạy bộ Fuzzing Chaos ADB Monkey"
    echo "===================================================================="
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--dir)
            TARGET_DIR="$2"
            shift 2
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo "ERROR: Tùy chọn không hợp lệ '$1'"
            print_help
            exit 1
            ;;
    esac
done

TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

echo "===================================================================="
echo " 🚀 Khởi động Crash Hunter 2.0"
echo " 📂 Target Directory: $TARGET_DIR"
echo " ⚙️  Execution Mode:   $MODE"
echo "===================================================================="

# 1. Kiểm tra môi trường cơ bản (Python3, ADB)
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 chưa được cài đặt."
    exit 1
fi

if ! command -v adb &> /dev/null; then
    # Thử tìm adb trong Android SDK thông dụng
    if [ -d "$HOME/Android/Sdk/platform-tools" ]; then
        export PATH="$PATH:$HOME/Android/Sdk/platform-tools"
    elif [ -d "$ANDROID_HOME/platform-tools" ]; then
        export PATH="$PATH:$ANDROID_HOME/platform-tools"
    else
        echo "ERROR: Không tìm thấy lệnh 'adb'. Vui lòng cài đặt Android Platform Tools."
        exit 1
    fi
fi

# 2. Khám phá cấu hình tự động (Discovery)
echo "[1/4] Đang quét cấu hình dự án & thiết bị..."
DISCOVERY_JSON=$(python3 "$BOT_DIR/scripts/core/discovery.py" "$TARGET_DIR")

PACKAGE_ID=$(echo "$DISCOVERY_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('package_id') or '')")
DEVICE_ID=$(echo "$DISCOVERY_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('device_id') or '')")
SCREEN_W=$(echo "$DISCOVERY_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('screen_width', 1080))")
SCREEN_H=$(echo "$DISCOVERY_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('screen_height', 2400))")
HAS_MAESTRO_CLI=$(echo "$DISCOVERY_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('has_maestro_cli', False))")
MAESTRO_BIN=$(echo "$DISCOVERY_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('maestro_bin') or '')")
HAS_PROJECT_MAESTRO=$(echo "$DISCOVERY_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('has_project_maestro', False))")

if [ -z "$PACKAGE_ID" ]; then
    echo "ERROR: Không thể tự động phát hiện Application ID. Hãy đảm bảo bạn đang trỏ vào thư mục project Android."
    exit 1
fi

if [ -z "$DEVICE_ID" ]; then
    echo "ERROR: Không tìm thấy thiết bị Android nào kết nối qua ADB."
    exit 1
fi

echo "     ✔ Target Package: $PACKAGE_ID"
echo "     ✔ Active Device:  $DEVICE_ID"
echo "     ✔ Resolution:     ${SCREEN_W}x${SCREEN_H}"
echo "     ✔ Maestro CLI:    ${MAESTRO_BIN:-Chưa cài đặt}"
echo "     ✔ Project .maestro: $HAS_PROJECT_MAESTRO"

# 3. Thực thi Engine 1: Maestro Semantic UI (nếu có)
if [ "$MODE" = "all" ] || [ "$MODE" = "maestro" ]; then
    if [ "$HAS_MAESTRO_CLI" = "True" ] && [ "$HAS_PROJECT_MAESTRO" = "True" ]; then
        echo ""
        echo "[2/4] [Engine 1] Chạy kịch bản Maestro Semantic UI Testing..."
        python3 -c "
import sys; sys.path.insert(0, '$BOT_DIR/scripts/core')
from maestro_runner import MaestroRunner
runner = MaestroRunner(package_id='$PACKAGE_ID', device_id='$DEVICE_ID', maestro_bin='$MAESTRO_BIN', log_dir='$TARGET_DIR/logs/subagent')
runner.discover_and_run_all('$TARGET_DIR/.maestro')
"
    else
        if [ "$MODE" = "maestro" ]; then
            echo "WARNING: Bỏ qua Maestro Engine (Maestro CLI chưa cài đặt hoặc project chưa có thư mục .maestro/)."
        fi
    fi
fi

# 4. Thực thi Engine 2: Dynamic ADB Chaos/Stress
if [ "$MODE" = "all" ] || [ "$MODE" = "adb" ]; then
    echo ""
    echo "[3/4] [Engine 2] Sinh và thực thi bộ ADB Chaos/Monkey Fuzzing..."
    cd "$TARGET_DIR"
    python3 "$BOT_DIR/scripts/generate_tests.py"
    if [ -f "$TARGET_DIR/scripts/subagent/run_all.sh" ]; then
        bash "$TARGET_DIR/scripts/subagent/run_all.sh" || true
    fi
    cd "$BOT_DIR"
fi

# 5. Phân tích kết quả và xuất Báo Cáo
echo ""
echo "[4/4] Đang tổng hợp báo cáo chẩn đoán..."
python3 -c "
import sys; sys.path.insert(0, '$BOT_DIR/scripts/core')
from reporter import CrashReporter
reporter = CrashReporter(log_dir='$TARGET_DIR/logs/subagent', report_file='$TARGET_DIR/CRASH_REPORT_FINAL.md', package_id='$PACKAGE_ID')
reporter.generate_report()
"

if [ -f "$TARGET_DIR/CRASH_REPORT_FINAL.md" ]; then
    echo ""
    echo "===================================================================="
    echo " 📊 KẾT QUẢ NGHIỆM THU CUỐI CÙNG"
    echo "===================================================================="
    cat "$TARGET_DIR/CRASH_REPORT_FINAL.md"
fi

echo ""
echo "===================================================================="
echo " ✅ Hoàn tất! Báo cáo chi tiết đã lưu tại: $TARGET_DIR/CRASH_REPORT_FINAL.md"
echo "===================================================================="
