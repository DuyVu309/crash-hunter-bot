---
name: crash-hunter-bot
description: Kích hoạt quy trình ADB Stress Test tự động bằng Subagent để săn lỗi Crash, RAM Leak, và Navigation Leak (15 Cases).
---

# Crash Hunter Bot (QA Automation Skill)

Khi User yêu cầu chạy "Crash Hunter" hoặc test crash (ADB, Monkey), bạn BẮT BUỘC thực hiện các bước sau:

## 1. Sinh kịch bản Test
Chạy lệnh python để tạo ra 15 file shell script tại `scripts/subagent/`.
```bash
mkdir -p scripts/subagent logs/subagent
python3 .agents/skills/crash-hunter-bot/scripts/generate_tests.py
chmod +x scripts/subagent/*.sh
```

## 2. Triệu hồi Subagent (CrashHunterBot)
Dùng tool `define_subagent` với cấu hình sau:
- **Name:** `CrashHunterBot`
- **Description:** QA Automation Engineer specializing in Android ADB stress testing.
- **System Prompt:** 
  You are CrashHunterBot, a QA Automation Engineer. Run `bash scripts/subagent/run_all.sh` (ensure `adb` is in PATH via `export PATH=$PATH:/home/adminpc/Android/Sdk/platform-tools/`). Wait for it to finish.
  Then, analyze the logs in `logs/subagent/`. Apply these criteria:
  - FATAL EXCEPTION in `_filtered.txt` -> CRASH
  - More than 2 identical Activities in `_backstack.txt` -> NAV LEAK
  - TOTAL PSS in `_mem_after.txt` is 100MB higher than `_mem_before.txt` -> RAM LEAK
  - Many identical network requests in `_filtered.txt` -> DDOS
  Create an artifact `CRASH_REPORT_FINAL.md` summarizing the results (PASS/FAIL/WARNING) and notify the parent agent.

## 3. Thực thi
Dùng `invoke_subagent` phái nó đi làm việc ở chế độ ngầm. Cảnh báo User rằng quá trình này mất khoảng 1.5 tiếng vì có 15 cases x 5 phút.

## 4. Nghiệm thu
Khi Subagent báo cáo xong, đọc file `CRASH_REPORT_FINAL.md` và tóm tắt các lỗi nghiêm trọng nhất cho User. Không tự ý sửa code nếu chưa được yêu cầu. Lên kế hoạch (writing-plans) nếu User muốn sửa lỗi.
