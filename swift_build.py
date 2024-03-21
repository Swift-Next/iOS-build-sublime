import sublime
import sublime_plugin
import re

from Default.exec import ExecCommand, ProcessListener, AsyncProcess


BUILD_CMD = "xcodebuild -quiet -workspace AppClose.xcworkspace -scheme AppClose -destination 'generic/platform=iOS Simulator' build"
CLEAN_BUILD_CMD = "xcodebuild -quiet -workspace AppClose.xcworkspace -scheme AppClose -destination 'generic/platform=iOS Simulator' clean build"
RUN_APP = "xcrun simctl launch --terminate-running-process E0C3EA3F-7F50-4F84-9AC7-A6E24C4FAB32 com.appclose.appclose"
# INSTALL_APP = f"xcrun simctl install {selected_uuid} /Users/yar/Library/Developer/Xcode/DerivedData/AppClose-brevdtkvkmeibkbvojjivinndsjo/Build/Products/Debug-iphonesimulator/AppClose.app"

class SharedState:
    instance = None

class SwiftExecCommand(ExecCommand, ProcessListener):
    encoding = 'utf-8'
    in_ios_section = False
    ios_version = ''
    devices = {}
    step = ''
    working_dir = "$folder"

    def run(self, **kwargs):
        SharedState.instance = self
        mode = kwargs.pop("mode", None)
        self.mode = mode
        print(mode == "build_and_run")
        if mode == "select_simulator" or mode == "install_application":
            print('wrong')
            cmd = "xcrun simctl list"
            env = {}
            process = AsyncProcess(cmd=cmd, shell_cmd=None, env=env, listener=self, shell=True)
            process.start()
        if mode == "build_and_run":
            print('started')
            super().run(shell_cmd=BUILD_CMD, **kwargs)

    def on_data(self, process, data):
        if self.mode == "build_and_run" and self.step == "get_devices":
            self.process_simctl_devices(data)
            self.step = "install"

        elif self.mode == "build_and_run":
            print("continue")
            super().on_data(process, data)
            return

        elif self.mode == "select_simulator" or self.mode == "install_application":
            self.process_simctl_devices(data)

    def on_finished(self, process):
        if self.mode == "select_simulator":
            self.window.run_command("show_ios_devices_select", {"devices": self.devices})
        elif self.mode == "install_application":
            self.window.run_command("run_app_on_ios_devices_select", {"devices": self.devices, "filter": filter})
        elif self.mode == "build_and_run":
            print("complete")
            if self.step == "":

                cmd = "xcrun simctl list"
                env = {}
                process = AsyncProcess(cmd=cmd, shell_cmd=None, env=env, listener=self, shell=True)
                process.start()
                self.step = "get_devices"
                print("getting list")
            elif self.step == "install":
                print("installing")
                self.window.run_command("run_app_on_ios_devices_select", {"devices": self.devices, "filter": "Booted"})
            # self.run_built_app()

    def process_simctl_devices(self, data):
        print(data)
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
                    device_name = match.group(1).strip()  # Full device name, including generation
                    uuid = match.group(2)  # UUID, capturing if needed
                    status = match.group(3)  # Status, e.g., "Shutdown"

                    # Compose the string as per the required output format
                    formatted_output = f"{self.ios_version}: {device_name} | {status}"
                    self.devices[uuid] = {
                        "ios_version": self.ios_version,
                        "status": status,
                        "devices_name": device_name,
                        "formatted_output": formatted_output
                    }

    def run_built_app(self, uuid):
        print(f"build_up: {uuid}")
        # process = AsyncProcess(cmd=cmd, shell_cmd=None, env=env, listener=self, shell=True)
        # process.start()

def run_built_app(self):
        print("build_up")

class ShowIosDevicesSelectCommand(sublime_plugin.WindowCommand):
    def run(self, devices, filter=None):
        self.devices = devices
        if filter:
            filtered_devices = {uuid: details for uuid, details in devices.items() if details['status'].lower() == filter.lower()}
        else:
            filtered_devices = devices

        # Create a list of tuples where each tuple is (UUID, formatted string)
        self.items = [(key, f"{value['formatted_output']}") for key, value in filtered_devices.items()]
        self.items = sorted(self.items, key=lambda item: item[1].lower(), reverse=True)
        # Prepare the list for display using only the formatted string part of each tuple
        display_items = [item[1] for item in self.items]
        sublime.set_timeout(lambda: self.window.show_quick_panel(display_items, self.on_done), 0)

    def on_done(self, picked):
        if picked == -1:
            return
        # Use the picked index to access the corresponding tuple in self.items
        selected_uuid = self.items[picked][0]  # This is the UUID of the selected item
        print(f"User selected: {selected_uuid}")

        cmd = f"xcrun simctl boot {selected_uuid}"
        self.window.run_command('exec', {'shell_cmd': cmd})

class RunAppOnIosDevicesSelectCommand(sublime_plugin.WindowCommand):
    def run(self, devices, filter=None):
        print("RunAppOnIosDevicesSelectCommand")
        self.devices = devices
        if filter:
            filtered_devices = {uuid: details for uuid, details in devices.items() if details['status'].lower() == filter.lower()}
        else:
            filtered_devices = devices

        self.items = [(key, f"{value['formatted_output']}") for key, value in filtered_devices.items()]
        self.items = sorted(self.items, key=lambda item: item[1].lower(), reverse=True)

        print(self.items)

        if len(self.items) == 1:
            print("RunAppOnIosDevicesSelectCommand in")
            selected_uuid = self.items[0][0]  # This is the UUID of the selected item
            SharedState.instance.run_built_app(selected_uuid)
            # cmd = f"xcrun simctl install {selected_uuid} /Users/yar/Library/Developer/Xcode/DerivedData/AppClose-brevdtkvkmeibkbvojjivinndsjo/Build/Products/Debug-iphonesimulator/AppClose.app"
            # self.window.run_command('exec', {'shell_cmd': cmd})
            return

        print("RunAppOnIosDevicesSelectCommand 2")
        # Create a list of tuples where each tuple is (UUID, formatted string)
        # Prepare the list for display using only the formatted string part of each tuple
        display_items = [item[1] for item in self.items]
        sublime.set_timeout(lambda: self.window.show_quick_panel(display_items, self.on_done), 0)

    def on_done(self, picked):
        if picked == -1:
            return
        # Use the picked index to access the corresponding tuple in self.items
        selected_uuid = self.items[picked][0]  # This is the UUID of the selected item
        print(f"User selected: {selected_uuid}")

        print("on_done")
        SharedState.instance.run_built_app(self, selected_uuid)

        # cmd = f"xcrun simctl install {selected_uuid} /Users/yar/Library/Developer/Xcode/DerivedData/AppClose-brevdtkvkmeibkbvojjivinndsjo/Build/Products/Debug-iphonesimulator/AppClose.app"
        # self.window.run_command('exec', {'shell_cmd': cmd})

class BuildCommand(sublime_plugin.WindowCommand):
    def run(self, devices, filter=None):
        self.devices = devices
        if filter:
            filtered_devices = {uuid: details for uuid, details in devices.items() if details['status'].lower() == filter.lower()}
        else:
            filtered_devices = devices

        self.items = [(key, f"{value['formatted_output']}") for key, value in filtered_devices.items()]
        self.items = sorted(self.items, key=lambda item: item[1].lower(), reverse=True)

        if len(self.items) == 1:
            selected_uuid = self.items[0][0]  # This is the UUID of the selected item
            cmd = f"xcrun simctl install {selected_uuid} /Users/yar/Library/Developer/Xcode/DerivedData/AppClose-brevdtkvkmeibkbvojjivinndsjo/Build/Products/Debug-iphonesimulator/AppClose.app"
            self.window.run_command('exec', {'shell_cmd': cmd})
            return

        # Create a list of tuples where each tuple is (UUID, formatted string)
        # Prepare the list for display using only the formatted string part of each tuple
        display_items = [item[1] for item in self.items]
        sublime.set_timeout(lambda: self.window.show_quick_panel(display_items, self.on_done), 0)

    def on_done(self, picked):
        if picked == -1:
            return
        # Use the picked index to access the corresponding tuple in self.items
        selected_uuid = self.items[picked][0]  # This is the UUID of the selected item
        print(f"User selected: {selected_uuid}")

        cmd = f"xcrun simctl install {selected_uuid} /Users/yar/Library/Developer/Xcode/DerivedData/AppClose-brevdtkvkmeibkbvojjivinndsjo/Build/Products/Debug-iphonesimulator/AppClose.app"
        self.window.run_command('exec', {'shell_cmd': cmd})


