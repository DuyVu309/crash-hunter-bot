#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import json
import sys

class ProjectDiscovery:
    """
    Tự động khám phá cấu hình thiết bị, môi trường và dự án Android:
    - Package ID (Application ID)
    - DeepLink Schemes
    - Thiết bị ADB & Độ phân giải màn hình (wm size)
    - Công cụ Maestro CLI & Kịch bản Maestro có sẵn
    """

    def __init__(self, project_dir="."):
        self.project_dir = os.path.abspath(project_dir)

    def get_application_id(self):
        """Tìm Application ID từ build.gradle.kts, build.gradle hoặc AndroidManifest.xml"""
        gradle_files = [
            os.path.join(self.project_dir, "app/build.gradle.kts"),
            os.path.join(self.project_dir, "app/build.gradle"),
            os.path.join(self.project_dir, "build.gradle.kts"),
            os.path.join(self.project_dir, "build.gradle"),
        ]

        for path in gradle_files:
            if os.path.exists(path):
                try:
                    with open(path, "r", errors="ignore") as f:
                        content = f.read()
                        # Match: applicationId = "com.example.app" hoặc applicationId "com.example.app"
                        match = re.search(r'applicationId\s*=?\s*["\']([^"\']+)["\']', content)
                        if match:
                            return match.group(1)
                        # Match: namespace = "com.example.app"
                        match_ns = re.search(r'namespace\s*=?\s*["\']([^"\']+)["\']', content)
                        if match_ns:
                            return match_ns.group(1)
                except Exception:
                    pass

        manifest_path = os.path.join(self.project_dir, "app/src/main/AndroidManifest.xml")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", errors="ignore") as f:
                    content = f.read()
                    match = re.search(r'package=["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
            except Exception:
                pass

        return None

    def get_deep_links(self):
        """Quét toàn bộ schemes/hosts định nghĩa trong AndroidManifest.xml"""
        links = []
        manifest_path = os.path.join(self.project_dir, "app/src/main/AndroidManifest.xml")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", errors="ignore") as f:
                    content = f.read()
                    matches = re.finditer(
                        r'<data[^>]*android:scheme=["\']([^"\']+)["\'][^>]*android:host=["\']([^"\']+)["\']',
                        content
                    )
                    for match in matches:
                        links.append(f"{match.group(1)}://{match.group(2)}")
            except Exception:
                pass
        return list(set(links))

    def get_active_device(self):
        """Lấy device id đầu tiên đang kết nối qua ADB"""
        try:
            out = subprocess.check_output(["adb", "devices"], text=True, stderr=subprocess.DEVNULL)
            lines = out.strip().split("\n")[1:]
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    return parts[0]
        except Exception:
            pass
        return None

    def get_screen_resolution(self, device_id=None):
        """Lấy độ phân giải màn hình thực tế (Width, Height) qua `adb shell wm size`"""
        cmd = ["adb"]
        if device_id:
            cmd.extend(["-s", device_id])
        cmd.extend(["shell", "wm", "size"])

        try:
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            # Match: Physical size: 1080x2400 hoặc Override size: 1080x2400
            matches = re.findall(r'(\d+)x(\d+)', out)
            if matches:
                last_match = matches[-1]
                return int(last_match[0]), int(last_match[1])
        except Exception:
            pass
        return 1080, 2400 # Default fallback

    def detect_maestro(self):
        """Kiểm tra đường dẫn binary của Maestro CLI"""
        path = shutil.which("maestro")
        if path:
            return path
        home_maestro = os.path.expanduser("~/.maestro/bin/maestro")
        if os.path.isfile(home_maestro) and os.access(home_maestro, os.X_OK):
            return home_maestro
        return None

    def has_project_maestro(self):
        """Kiểm tra xem project có sẵn thư mục .maestro/ với các file .yaml hay không"""
        maestro_dir = os.path.join(self.project_dir, ".maestro")
        if os.path.isdir(maestro_dir):
            for root, _, files in os.walk(maestro_dir):
                for f in files:
                    if f.endswith(".yaml") or f.endswith(".yml"):
                        return True
        return False

    def discover_all(self):
        device = self.get_active_device()
        width, height = self.get_screen_resolution(device)
        app_id = self.get_application_id()
        deep_links = self.get_deep_links()
        maestro_bin = self.detect_maestro()
        has_maestro_flows = self.has_project_maestro()

        return {
            "project_dir": self.project_dir,
            "package_id": app_id,
            "device_id": device,
            "screen_width": width,
            "screen_height": height,
            "deep_links": deep_links,
            "has_maestro_cli": maestro_bin is not None,
            "maestro_bin": maestro_bin,
            "has_project_maestro": has_maestro_flows
        }

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    discovery = ProjectDiscovery(target_dir)
    data = discovery.discover_all()
    print(json.dumps(data, indent=2))
