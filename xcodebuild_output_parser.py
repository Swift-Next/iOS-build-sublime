import re
from typing import Dict, Optional

class XcodebuildOutputParser:

    in_ios_section = False
    ios_version = ''
    target_build_dir = ''
    executable_folder_path = ''


    def process_simctl_devices(self, data: str) -> Dict[str, str]:
        devices = {}
        lines = data.split('\n')
        for line in lines:
            if '-- iOS' in line:
                self.in_ios_section = True
                pattern = r"iOS \d+\.\d+"
                self.ios_version = re.search(pattern, line).group()  # Directly using the string since it's a known value
            elif '--' in line:
                self.in_ios_section = False

            if self.in_ios_section and ('iPhone' in line or 'iPad' in line):
                # print(f"line: {line}")
                # Adjusted regex pattern to more accurately match your requirements
                match = re.match(r'^\s+(iP\w+(?: \w+)? (?:Pro|Plus)?(?: Max)?.*)\(([\w\d]{8}-(?:[\w\d]{4}-){3}[\w\d]{12})\) \((Booted|Shutdown)\)', line)
                # print(f"match {match}")
                if match:
                    device_name = match.group(1).strip()  # Full device name, including generation
                    uuid = match.group(2)  # UUID, capturing if needed
                    status = match.group(3)  # Status, e.g., "Shutdown"

                    # Compose the string as per the required output format
                    formatted_output = f"{self.ios_version}: {device_name} | {status}"
                    devices[uuid] = {
                        "ios_version": self.ios_version,
                        "status": status,
                        "devices_name": device_name,
                        "formatted_output": formatted_output
                    }
        return devices

    def process_xcode_settings(self, data: str) -> Optional[str]:
        print("process_xcode_settings(self, data):")
        lines = data.split('\n')
        for line in lines:
            if "TARGET_BUILD_DIR" in line:
                self.target_build_dir = line.split('=')[1].strip()
            elif "EXECUTABLE_FOLDER_PATH " in line:
                self.executable_folder_path = line.split('=')[1].strip()

            # If both paths are found, no need to continue parsing
            if self.target_build_dir and self.executable_folder_path:
                target_substring = "Build/Products"
                index = self.target_build_dir.rfind(target_substring)
                if index != -1:
                    cut_path = self.target_build_dir[:index]
                    return f"{cut_path}{target_substring}/Debug-iphonesimulator/{self.executable_folder_path}"
