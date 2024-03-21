import sublime
import sublime_plugin
import re

from Default.exec import ExecCommand, ProcessListener, AsyncProcess

SIMCTL_LIST_CMD = "xcrun simctl list"

SIMCTL_BOOT_DEVICE_CMD = "xcrun simctl boot {device_uuid}"

BUILD_CMD = "xcodebuild -quiet -{project_kind} {project_name} -scheme {scheme} -destination 'generic/platform=iOS Simulator' build"
CLEAN_BUILD_CMD = "xcodebuild -quiet -{project_kind} {project_name} -scheme {scheme} -destination 'generic/platform=iOS Simulator' clean build"

BUILT_SETTINGS = "xcodebuild -{project_kind} {project_name} -scheme {scheme} -showBuildSettings"

INSTALL_APP = "xcrun simctl install {device_uuid} {product_path}"
RUN_APP = "xcrun simctl launch {device_uuid} {bundle_id} --terminate-spawned-process"

class SharedState:
    instance = None

class SwiftExecCommand(ExecCommand, ProcessListener):
    encoding = 'utf-8'
    in_ios_section = False
    ios_version = ''
    devices = {}
    step = ''
    picked_device_uuid = ''

    def run(self, **kwargs):
        SharedState.instance = self

        self.mode = kwargs.pop("mode", None)
        self.projectfile_name = kwargs.pop('projectfile_name', None)
        self.scheme = kwargs.pop('scheme', None)
        self.bundle = kwargs.pop('bundle', None)
        self.product_path = kwargs.pop('product_path', None)

        if self.mode == "toggle_simulator":
            process = AsyncProcess(cmd=None, shell_cmd=SIMCTL_LIST_CMD, env={}, listener=self, shell=True)
            process.start()
        if self.mode == "build_and_run":
            print('started')
            project_kind = 'workspace' if self.projectfile_name.split('.')[1] == "xcworkspace" else "project"
            super().run(
                shell_cmd=BUILD_CMD.format(project_kind=project_kind, project_name=self.projectfile_name, scheme=self.scheme),
                **kwargs
            )

    def on_data(self, process, data):
        if self.mode == "toggle_simulator":
            self.process_simctl_devices(data)

        elif self.mode == "build_and_run" and self.step == "":
            super().on_data(process, data)

        elif self.mode == "build_and_run" and self.step == "built":
            self.process_xcode_settings(data)

        elif self.mode == "build_and_run" and self.step == "obtained_product_path":
            self.process_simctl_devices(data)
            print(self.devices)


    def on_finished(self, process):
        self.build_process()

    def handle_booted_device_uuid(self, uuid):
        self.picked_device_uuid = uuid
        if self.mode == "build_and_run": self.build_process()
        else:
            process = AsyncProcess(
                cmd=None,
                shell_cmd=SIMCTL_BOOT_DEVICE_CMD.format(device_uuid=uuid),
                env={},
                listener=self,
                shell=True
            )
            process.start()

    def process_simctl_devices(self, data):
        print(f"process_simctl_devices(self, data):")
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
                    self.devices[uuid] = {
                        "ios_version": self.ios_version,
                        "status": status,
                        "devices_name": device_name,
                        "formatted_output": formatted_output
                    }

    def process_xcode_settings(self, data):
        # print("process_xcode_settings(self, data):")
        lines = data.split('\n')
        target_build_dir, executable_folder_path = None, None
        for line in lines:
            if "TARGET_BUILD_DIR" in line:
                target_build_dir = line.split('=')[1].strip()
            elif "EXECUTABLE_FOLDER_PATH" in line:
                executable_folder_path = line.split('=')[1].strip()

            # If both paths are found, no need to continue parsing
            if target_build_dir and executable_folder_path:
                break

        if target_build_dir and executable_folder_path:
            # Combine the paths
            self.product_path = f"{target_build_dir}/{executable_folder_path}"

    def manage_build_internal_state(self):
        print(f"manage_internal_state_begin: {self.step}")
        if self.mode == "build_and_run":
            if self.step == "" or self.step == "spawned": self.step = "built"
            elif self.step == "built": self.step = "obtained_product_path"
            elif self.step == "obtained_product_path": self.step = "obrained_devices"
            elif self.step == "obrained_devices": self.step = "device_picked"
            elif self.step == "device_picked": self.step = "installed"
            elif self.step == "installed": self.step = "spawned"
            elif self.step == "spawned": self.step = ""
        elif self.mode == "toggle_simulator":
            if self.step == "": self.step = "booted"
            elif self.step == "booted": self.step = ""

        print(f"manage_internal_state_end: {self.step}")

    def build_process(self):
        print(f"on_finished_start: {self.step}")
        self.manage_build_internal_state()
        if self.mode == "toggle_simulator" and self.step != "booted":
            self.window.run_command("run_app_on_ios_devices_select", {"devices": self.devices})

        elif self.mode == "build_and_run":
            if self.step == "built":
                ## on built obtaining built product path
                project_kind = 'workspace' if self.projectfile_name.split('.')[1] == "xcworkspace" else "project"
                process = AsyncProcess(
                    cmd=None,
                    shell_cmd=BUILT_SETTINGS.format(project_kind=project_kind, project_name=self.projectfile_name, scheme=self.scheme),
                    env={},
                    listener=self,
                    shell=True
                )
                process.start()

            if self.step == "obtained_product_path":
                ## on obtained product path obtaining the devices list
                process = AsyncProcess(cmd=None, shell_cmd=SIMCTL_LIST_CMD, env={}, listener=self, shell=True)
                process.start()
                print("xcrun_simcl started")

            elif self.step == "obrained_devices":
                ## on both devices list and product path obtained user should pick a device to run
                self.window.run_command("run_app_on_ios_devices_select", {"devices": self.devices, "filter": "Booted"})

            elif self.step == "device_picked":
                ## on device picked by a user fire install
                process = AsyncProcess(
                    cmd=None,
                    shell_cmd=INSTALL_APP.format(device_uuid=self.picked_device_uuid, product_path=self.product_path),
                    env={},
                    listener=self,
                    shell=True
                )
                process.start()
            elif self.step == "installed":
                ## on installation finish run app
                print(RUN_APP.format(device_uuid=self.picked_device_uuid, bundle_id=self.bundle),)
                process = AsyncProcess(
                    cmd=None,
                    shell_cmd=RUN_APP.format(device_uuid=self.picked_device_uuid, bundle_id=self.bundle),
                    env={},
                    listener=self,
                    shell=True
                )
                process.start()

            elif self.step == "spawned":
                ## on spawned finish build/run so far
                pass

        print(f"on_finished_end: {self.step}")


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
            self.return_uuid(selected_uuid=selected_uuid)
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
        self.return_uuid(selected_uuid)

        # cmd = f"xcrun simctl install {selected_uuid} /Users/yar/Library/Developer/Xcode/DerivedData/AppClose-brevdtkvkmeibkbvojjivinndsjo/Build/Products/Debug-iphonesimulator/AppClose.app"
        # self.window.run_command('exec', {'shell_cmd': cmd})

    def return_uuid(self, selected_uuid):
        SharedState.instance.handle_booted_device_uuid(selected_uuid)
