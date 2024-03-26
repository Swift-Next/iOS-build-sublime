import re

from Default.exec import ExecCommand, ProcessListener, AsyncProcess

WARNING_PANE = "Warnings Pane"

OPEN_PROJECT = "open {projct_path}"

SIMCTL_LIST_CMD = "xcrun simctl list"
SIMCTL_BOOT_DEVICE_CMD = "xcrun simctl boot {device_uuid}"

BUILD_CMD = "xcodebuild -quiet -{project_kind} {project_name} -scheme {scheme} -destination 'generic/platform=iOS Simulator' build | xcbeautify --disable-colored-output --quieter"
CLEAN_CMD = "xcodebuild -quiet -{project_kind} {project_name} -scheme {scheme} -destination 'generic/platform=iOS Simulator' clean"
CLEAN_BUILD_CMD = "xcodebuild -quiet -{project_kind} {project_name} -scheme {scheme} -destination 'generic/platform=iOS Simulator' clean build | xcbeautify --disable-colored-output --quieter"

BUILT_SETTINGS = "xcodebuild -{project_kind} {project_name} -scheme {scheme} -showBuildSettings"

INSTALL_APP = "xcrun simctl install {device_uuid} {product_path}"
RUN_APP = "xcrun simctl launch {with_debugger} --terminate-running-process {device_uuid} {bundle_id}"


class SharedState:
    instance = None

class SwiftExecCommand(ExecCommand, ProcessListener):
    encoding = 'utf-8'
    in_ios_section = False
    ios_version = ''
    devices = {}
    step = ''
    picked_device_uuid = ''
    bundle = ''
    product_path = ''
    scheme = ''
    projectfile_name = ''
    mode = ''
    file_regex = ''
    line_regex = ''
    syntax = 'Packages/Text/Plain text.tmLanguage'
    target_build_dir = None
    executable_folder_path = None

    def run(self, **kwargs):
        SharedState.instance = self

        self.step = kwargs.pop("step", "")
        self.env = kwargs.get("env", {})
        self.with_debugger = kwargs.pop('debugger', False)

        self.mode = kwargs.pop("mode", None)
        self.projectfile_name = self.window.active_view().settings().get('ios_build_system')['projectfile_name']
        self.scheme = self.window.active_view().settings().get('ios_build_system')['scheme']
        self.bundle = self.window.active_view().settings().get('ios_build_system')['bundle']
        self.file_regex = kwargs.get('file_regex', None)
        self.working_dir = kwargs.get('working_dir', None)
        self.line_regex = kwargs.get('line_regex', None)
        self.syntax = kwargs.get('syntax', None)

        if self.mode == "toggle_simulator":
            if self.step == "Booted": self.step = ""
            command = SIMCTL_LIST_CMD
            print(command)
            process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True)
            process.start()
        elif self.mode == "build_and_run":
            print('started')
            project_kind = 'workspace' if self.projectfile_name.split('.')[1] == "xcworkspace" else "project"
            command = BUILD_CMD.format(project_kind=project_kind, project_name=self.projectfile_name, scheme=self.scheme)
            print(command)
            super().run( shell_cmd=command, **kwargs)
        elif self.mode == "clean_build":
            project_kind = 'workspace' if self.projectfile_name.split('.')[1] == "xcworkspace" else "project"
            command = CLEAN_CMD.format(project_kind=project_kind, project_name=self.projectfile_name, scheme=self.scheme)
            super().run( shell_cmd=command, **kwargs)

        elif self.mode == "open_project":
            full_project_path = f'{self.working_dir}/{self.projectfile_name}'
            command = OPEN_PROJECT.format(projct_path=full_project_path)
            print(command)
            process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=None, shell=False)
            process.start()

    def on_data(self, process, data):
        if self.mode == "toggle_simulator":
            self.process_simctl_devices(data)

        elif self.mode == "build_and_run" and (self.step == "" or self.step == "spawned"):
            super().on_data(process, data)

        elif self.mode == "build_and_run" and self.step == "built":
            self.process_xcode_settings(data)

        elif self.mode == "build_and_run" and self.step == "obtained_product_path":
            self.process_simctl_devices(data)
            print(self.devices)

        elif self.mode == "clean_build":
            super().on_data(process, data)


    def on_finished(self, process):
        self.build_process(process=process)

    def handle_booted_device_uuid(self, uuid):
        self.picked_device_uuid = uuid
        if self.mode == "build_and_run": self.build_process(process=None)
        else: # if "toggle_simulator"
            command = SIMCTL_BOOT_DEVICE_CMD.format(device_uuid=uuid)
            print(command)
            process = AsyncProcess(cmd=None,shell_cmd=command, env=self.env, listener=self, shell=True)
            process.start()

    def process_simctl_devices(self, data):
        # print(f"process_simctl_devices(self, data):")
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
        print("process_xcode_settings(self, data):")
        lines = data.split('\n')
        for line in lines:
            if "TARGET_BUILD_DIR" in line:
                self.target_build_dir = line.split('=')[1].strip()
            elif "EXECUTABLE_FOLDER_PATH" in line:
                self.executable_folder_path = line.split('=')[1].strip()

            # If both paths are found, no need to continue parsing
            if self.target_build_dir and self.executable_folder_path:
                target_substring = "Build/Products"
                index = self.target_build_dir.rfind(target_substring)
                if index != -1:
                    cut_path = self.target_build_dir[:index]
                    self.product_path = f"{cut_path}{target_substring}/Debug-iphonesimulator/{self.executable_folder_path}"
                    print("self.product_path", self.product_path)
                    break


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
            if self.step == "": self.step = "started"
            elif self.step == "started": self.step = "booted"
            elif self.step == "booted": self.step = ""

        print(f"manage_internal_state_end: {self.step}")

    def build_process(self, process):
        print(f"on_finished_start: {self.step}")
        self.manage_build_internal_state()
        if self.mode == "toggle_simulator" and self.step != "booted":
            print("manage_build_internal_state()")
            self.window.run_command("run_app_on_ios_devices_select", {"devices": self.devices})

        elif self.mode == "build_and_run":
            if self.step == "built":
                ## present pane with warnings for convenience
                self.present_warnings_and_errors_panel()

                ## on built obtaining built product path
                project_kind = 'workspace' if self.projectfile_name.split('.')[1] == "xcworkspace" else "project"
                command = BUILT_SETTINGS.format(project_kind=project_kind, project_name=self.projectfile_name, scheme=self.scheme)
                print(command)
                process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True)
                process.start()

            if self.step == "obtained_product_path":
                ## on obtained product path obtaining the devices list
                command = SIMCTL_LIST_CMD
                print(command)
                process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True)
                process.start()
                print("xcrun_simcl started")

            elif self.step == "obrained_devices":
                ## on both devices list and product path obtained user should pick a device to run
                self.window.run_command("run_app_on_ios_devices_select", {"devices": self.devices, "filter": "Booted"})

            elif self.step == "device_picked":
                ## on device picked by a user fire install
                command = INSTALL_APP.format(device_uuid=self.picked_device_uuid, product_path=self.product_path)
                print(command)
                process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True)
                process.start()
            elif self.step == "installed":
                ## on installation finish run app
                with_debugger = "--wait-for-debugger" if self.with_debugger else ""
                command = RUN_APP.format(with_debugger=with_debugger, device_uuid=self.picked_device_uuid, bundle_id=self.bundle)
                print(command)
                process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True)
                process.start()

            elif self.step == "spawned":
                super().on_finished(process)

        print(f"on_finished_end: {self.step}")

    def present_warnings_and_errors_panel(self):
        output_view = self.window.find_output_panel("exec")
        if output_view is None: return

        errors_struct = self.output_view.find_all_results_with_text()
        print("errors_struct",len(errors_struct))
        formatted_errors = []
        for file, line, column, text in errors_struct:
            formatted_error = f"[!]  {file}:{line}:{column}: {text}"
            formatted_errors.append(formatted_error)

        if len(formatted_errors) > 0:
            warning_pane = self.window.find_output_panel(WARNING_PANE) or self.window.create_output_panel(WARNING_PANE)
            warning_pane.settings().set("result_file_regex", self.file_regex)
            warning_pane.settings().set("result_line_regex", self.line_regex)
            # warning_pane.settings().set("result_base_dir", working_dir)
            warning_pane.settings().set("word_wrap", False)
            warning_pane.settings().set("line_numbers", True)
            warning_pane.settings().set("gutter", False)
            warning_pane.settings().set("scroll_past_end", False)
            # self.warning_pane.assign_syntax(self.syntax)

            warning_pane.set_read_only(False)
            warning_pane.run_command('select_all')  # Select all existing content
            warning_pane.run_command('right_delete')  # Delete selected content
            warning_pane.run_command('append', {'characters': "\n".join(formatted_errors)})  # Append the formatted errors
            warning_pane.set_read_only(True)

            self.window.run_command("show_panel", {"panel": f"output.{WARNING_PANE}"})
