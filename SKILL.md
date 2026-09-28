---
name: crash-hunter-bot
description: Kích hoạt quy trình ADB Stress Test tự động bằng Subagent để săn lỗi Crash, RAM Leak, và Navigation Leak. Phân tích chi tiết đến từng dòng code nhờ Timber log.
---

# Crash Hunter Bot (QA Automation Skill)

Khi User yêu cầu chạy "Crash Hunter" hoặc test crash (ADB, Monkey), bạn BẮT BUỘC thực hiện các bước sau:

## 1. Sinh kịch bản Test
Chạy lệnh python để tự động quét Package ID và DeepLink của dự án:
```bash
mkdir -p scripts/subagent logs/subagent
python3 .agents/skills/crash-hunter-bot/scripts/generate_tests.py
```

## 2. Triệu hồi Subagent (CrashHunterBot)
Dùng tool `define_subagent` với cấu hình sau:
- **Name:** `CrashHunterBot`
- **Description:** QA Automation Engineer.
- **System Prompt:** 
  You are CrashHunterBot, a QA Automation Engineer. Run `bash scripts/subagent/run_all.sh` (ensure `adb` is in PATH). Wait for it to finish.
  Then, analyze the logs in `logs/subagent/`. Apply these criteria:
  - **CRASH**: FATAL EXCEPTION in `_filtered.txt`.
  - **NAV LEAK**: More than 2 identical Activities in `_backstack.txt`.
  - **RAM LEAK**: TOTAL PSS in `_mem_after.txt` is 100MB higher than `_mem_before.txt`.
  - **DDOS**: Many identical network requests in `_filtered.txt`.
  
  **IMPORTANT**: The app uses Timber, so logs often contain the exact file and line number (e.g., `(ViewModel.kt:150)`). You MUST extract this `(File:Line)` information and include it in your report! For example: `FAIL | DDOS Ktor Spam tại (SearchViewModel.kt:157)`.
  
  Create an artifact `CRASH_REPORT_FINAL.md` summarizing the results (PASS/FAIL/WARNING) and notify the parent agent.

## 3. Thực thi & Nghiệm thu
Dùng `invoke_subagent` phái nó đi làm việc ở chế độ ngầm (`BypassSandbox=true`).
Khi Subagent báo cáo xong, tóm tắt các lỗi nghiêm trọng nhất cho User kèm SỐ DÒNG CODE CHI TIẾT. Cảnh báo rủi ro về Coroutines/MVI State nếu có.
