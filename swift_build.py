import sublime
import sublime_plugin
import re

from Default.exec import ExecCommand
from Default.exec import AsyncProcess

class ProcessListener:
    def __init__(self, on_finish_callback=None):
        self.encoding = 'utf-8'
        self.in_ios_section = False
        self.ios_version = ''
        self.devices = {}
        self.on_finish_callback = on_finish_callback

    def on_data(self, process, data):
        lines = data.split('\n')
        for line in lines:
            if '-- iOS' in line:
                self.in_ios_section = True
                pattern = r"iOS \d+\.\d+"
                self.ios_version = re.search(pattern, line).group()  # Directly using the string since it's a known value
            elif '--' in line:
                self.in_ios_section = False

            if self.in_ios_section and ('iPhone' in line or 'iPad' in line):
                print(f"line: {line}")
                # Adjusted regex pattern to more accurately match your requirements
                match = re.match(r'^\s+(iP\w+(?: \w+)? (?:Pro|Plus)?(?: Max)?.*)\(([\w\d]{8}-(?:[\w\d]{4}-){3}[\w\d]{12})\) \((Booted|Shutdown)\)', line)
                print(f"match {match}")
                if match:
                    # device_type = match.group(1)  # "iPhone" or "iPad"
                    device_name = match.group(1).strip()  # Full device name, including generation
                    uuid = match.group(2)  # UUID, capturing if needed
                    status = match.group(3)  # Status, e.g., "Shutdown"

                    # Compose the string as per the required output format
                    formatted_output = f"{self.ios_version}: {device_name} | {status}"
                    self.devices[uuid] = formatted_output

    def on_finished(self, process):
        print("\nProcess finished.")
        if self.on_finish_callback:
            sublime.set_timeout(lambda: self.on_finish_callback(self.devices), 0)


class SwiftExecCommand(ExecCommand):
    def run(self, **kwargs):
        listener = ProcessListener(self.on_process_finished)
        cmd = "xcrun simctl list"
        env = {}

        process = AsyncProcess(cmd=cmd, shell_cmd=None, env=env, listener=listener, shell=True)
        process.start()

    def on_process_finished(self, devices):
        self.window.run_command("show_ios_devices_select", {"devices": devices})


class ShowIosDevicesSelectCommand(sublime_plugin.WindowCommand):
    def run(self, devices):
        self.devices = devices
        # Create a list of tuples where each tuple is (UUID, formatted string)
        self.items = [(key, f"{value}") for key, value in devices.items()]
        # Prepare the list for display using only the formatted string part of each tuple
        display_items = [item[1] for item in self.items]
        sublime.set_timeout(lambda: self.window.show_quick_panel(display_items, self.on_done), 0)

    def on_done(self, picked):
        if picked == -1:
            return
        # Use the picked index to access the corresponding tuple in self.items
        selected_uuid = self.items[picked][0]  # This is the UUID of the selected item
        print(f"User selected: {selected_uuid}")