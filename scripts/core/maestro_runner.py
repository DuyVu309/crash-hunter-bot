#!/usr/bin/env python3
import os
import subprocess
import glob
import re

class MaestroRunner:
    """
    Điều khiển và thực thi các kịch bản Maestro UI kèm theo Diagnostic Profiling:
    - dumpsys meminfo trước và sau flow
    - dumpsys activity activities (Audit Backstack Leak)
    - logcat full & filtered (Timber File:Line extraction)
    """

    def __init__(self, package_id, device_id=None, maestro_bin=None, log_dir="logs/subagent"):
        self.package_id = package_id
        self.device_id = device_id
        self.maestro_bin = maestro_bin or "maestro"
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def _adb_cmd(self, *args):
        cmd = ["adb"]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(args)
        return cmd

    def run_case(self, yaml_path, case_id):
        print(f"====================================================================")
        print(f" [*] Maestro Smart Runner: {case_id}")
        print(f"     Target Flow: {yaml_path}")
        print(f"====================================================================")

        mem_before_file = os.path.join(self.log_dir, f"{case_id}_mem_before.txt")
        mem_after_file = os.path.join(self.log_dir, f"{case_id}_mem_after.txt")
        logcat_full_file = os.path.join(self.log_dir, f"{case_id}_full_logcat.txt")
        logcat_filtered_file = os.path.join(self.log_dir, f"{case_id}_filtered.txt")
        backstack_file = os.path.join(self.log_dir, f"{case_id}_backstack.txt")
        gfx_file = os.path.join(self.log_dir, f"{case_id}_gfx.txt")

        # 1. Reset logcat & gfxinfo
        subprocess.run(self._adb_cmd("logcat", "-c"), stderr=subprocess.DEVNULL)
        subprocess.run(self._adb_cmd("shell", "dumpsys", "gfxinfo", self.package_id, "reset"),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 2. Record pre-test memory
        with open(mem_before_file, "w") as f:
            subprocess.run(self._adb_cmd("shell", "dumpsys", "meminfo", self.package_id), stdout=f, stderr=f)

        # 3. Execute Maestro Flow
        maestro_cmd = [self.maestro_bin]
        if self.device_id:
            maestro_cmd.extend(["--device", self.device_id])
        maestro_cmd.extend(["test", yaml_path])

        status_code = 0
        try:
            res = subprocess.run(maestro_cmd)
            status_code = res.returncode
        except Exception as e:
            print(f"ERROR: Không thể thực thi Maestro: {e}")
            status_code = 1

        # 4. Dump diagnostics
        with open(logcat_full_file, "w") as f:
            subprocess.run(self._adb_cmd("logcat", "-d"), stdout=f, stderr=f)

        with open(mem_after_file, "w") as f:
            subprocess.run(self._adb_cmd("shell", "dumpsys", "meminfo", self.package_id), stdout=f, stderr=f)

        with open(gfx_file, "w") as f:
            subprocess.run(self._adb_cmd("shell", "dumpsys", "gfxinfo", self.package_id), stdout=f, stderr=f)

        with open(backstack_file, "w") as f:
            out = subprocess.check_output(self._adb_cmd("shell", "dumpsys", "activity", "activities"), text=True, errors="ignore")
            for line in out.splitlines():
                if "Hist" in line or f"{self.package_id}/" in line:
                    f.write(line + "\n")

        # 5. Filter logcat
        keywords = "Timber_\\|FATAL EXCEPTION\\|ANR\\|OutOfMemory\\|SQLite\\|StrictMode\\|CancellationException\\|MediaCodec\\|AudioRecord\\|AudioCaptureManager\\|NavController\\|IllegalArgument\\|IllegalState"
        cmd = f"grep -i '{keywords}' {logcat_full_file} > {logcat_filtered_file} || true"
        subprocess.run(cmd, shell=True)

        return status_code

    def discover_and_run_all(self, maestro_dir=".maestro"):
        if not os.path.isdir(maestro_dir):
            print(f"WARNING: Thư mục '{maestro_dir}' không tồn tại.")
            return

        yaml_files = sorted(glob.glob(os.path.join(maestro_dir, "**/*.yaml"), recursive=True))
        yaml_files += sorted(glob.glob(os.path.join(maestro_dir, "**/*.yml"), recursive=True))

        # Loại bỏ subflows
        target_files = [f for f in yaml_files if "subflows" not in f]

        if not target_files:
            print(f"WARNING: Không tìm thấy file kịch bản Maestro nào trong {maestro_dir}.")
            return

        print(f"[*] Tìm thấy {len(target_files)} kịch bản Maestro UI testing.")
        for idx, file_path in enumerate(target_files, 1):
            case_id = f"MAESTRO_{idx:02d}_" + os.path.basename(file_path).replace(".yaml", "").replace(".yml", "").upper()
            self.run_case(file_path, case_id)
