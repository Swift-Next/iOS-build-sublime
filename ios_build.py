import os
from signal import Signals
from typing import Dict, Optional
from sublime import status_message
from sublime_plugin import WindowCommand
from Default.exec import ExecCommand, ProcessListener
from .AsyncProcess import AsyncProcess
from .simulator_manager_builder import SimulatorCommandBuilder
from .xcodebuild_output_parser import XcodebuildOutputParser
from .status_manager import StatusbarManager
from .build_log_processor import LogProcessor
from .exceptions.ios_build_exception import IosBuildException, present_error
from .panes_manager import PaneManager
from .constants import OPEN_PROJECT
from .build_command_builder import XcodebuildCommandBuilder
import time


class IosExecCommand(ExecCommand, ProcessListener):
    encoding = 'utf-8'
    in_ios_section = False
    ios_version: str = ''
    devices: Dict[str, str] = {}
    step: str = ''
    picked_device_uuid: str = ''
    bundle: str = ''
    product_path: str = ''
    scheme: str = ''
    projectfile_name: str = ''
    mode: str = ''
    file_regex: str = ''
    line_regex: str = ''
    syntax = 'Packages/Text/Plain text.tmLanguage'
    target_build_dir: Optional[str] = None
    executable_folder_path: Optional[str] = None
    with_debugger: bool = False
    current_process = None  # Hold reference to the current running process

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
        self.working_dir: str = self.window.folders()[0] ## assuming that the project folder is first in the list
        self.line_regex = kwargs.get('line_regex', None)
        self.syntax = kwargs.get('syntax', None)
        self.start_time = time.time()
        self.xcodebuild_command_builder = XcodebuildCommandBuilder(project_filename=self.projectfile_name, scheme=self.scheme)
        self.xcodebuld_output_parser = XcodebuildOutputParser()
        self.simctl_command_builder = SimulatorCommandBuilder(bundle_id=self.bundle)
        self.build_pane = PaneManager.get_build_pane(window=self.window)
        self.build_pane.setup_with(self.file_regex)

        self.cancel()

        if self.mode == "toggle_simulator":
            if self.step == "Booted": self.step = ""
            command = (self.simctl_command_builder
                .list()
                .assemble_command()
            )
            print(command)
            process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True, cwd=self.working_dir)
            self.current_process = process
            process.start()
        elif self.mode == "build_and_run":
            print('started')
            self.step = ""

            PaneManager.clear_build_pane(window=self.window)

            command = (self.xcodebuild_command_builder
                .manage_bundle()
                .quiet()
                .target_setup()
                .destination_setup()
                .build()
                .assemble_command()
            )
            process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True, cwd=self.working_dir)
            self.current_process = process
            process.start()
            self.show_current_state()

        elif self.mode == "clean":
            command = (self.xcodebuild_command_builder
                .target_setup()
                .destination_setup()
                .clean()
                .assemble_command()
            )
            status_message("Cleaning...")
            super().run(shell_cmd=command, **kwargs)

        elif self.mode == "open_project":
            full_project_path = f'{self.working_dir}/{self.projectfile_name}'
            command = OPEN_PROJECT.format(projct_path=full_project_path)
            print(command)
            process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True, cwd=self.working_dir)
            self.current_process = process
            process.start()

    def on_data(self, process, data):
        # print("step * mode", self.step, self.mode)
        if self.mode == "toggle_simulator":
            devices = self.xcodebuld_output_parser.process_simctl_devices(data=data)
            self.devices.update(devices)

        elif self.mode == "build_and_run" and self.step == "":
            build_pane = PaneManager.get_build_pane(window=self.window)

            build_pane.set_read_only(False)
            build_pane.run_command('append', {'characters': data})  # Append the formatted errors
            build_pane.set_read_only(True)

        elif self.mode == "build_and_run" and self.step == "built":
            if self.xcodebuld_output_parser.process_xcode_settings(data=data):
                self.product_path = self.xcodebuld_output_parser.process_xcode_settings(data=data)

        elif self.mode == "build_and_run" and self.step == "obtained_product_path":
            devices = self.xcodebuld_output_parser.process_simctl_devices(data=data)
            self.devices.update(devices)
            # print(self.devices)

        elif self.mode == "clean":
            super().on_data(process, data)

    def on_finished(self, process):
        self.build_process(process=process)
        if self.step == "spawned" or self.step == "booted":
            self.current_process = None
        elif self.step == "built":
            exit_code = process.exit_code()
            elapsed = time.time() - self.start_time
            if elapsed < 1:
                elapsed_str = "%.0fms" % (elapsed * 1000)
            else:
                elapsed_str = "%.1fs" % (elapsed)
            build_pane = PaneManager.get_build_pane(window=self.window)
            build_pane.set_read_only(False)
            if exit_code == 0 or exit_code is None:
                build_pane.run_command('append', {'characters': "[Succeeded in %s]" % elapsed_str})
            else:
                build_pane.run_command('append', {'characters': "[Failed in %s with exit code %d]" %
                           (elapsed_str, exit_code)})
                # build_pane.run_command(self.debug_text)
                self.step = "failed"
                self.current_process = None
            build_pane.set_read_only(True)

    def cancel(self):
        print("cancel")
        if self.current_process:
            print("if self.current_process:",self.current_process)
            if not self.current_process.killed:
                print("if not self.current_process.killed::")
                self.current_process.killed = True

                print("self.current_process.proc.pid", self.current_process.proc.pid)
                os.killpg(os.getpgid(self.current_process.proc.pid), Signals.SIGTERM)
                self.current_process = None
                self.step = "canceled"
                build_pane = PaneManager.get_build_pane(self.window)
                build_pane.set_read_only(False)
                build_pane.run_command('append', {'characters': "[Canceled]"})  # Append the formatted errors
                build_pane.set_read_only(True)


    def handle_booted_device_uuid(self, uuid: str):
        if not uuid:
            error = IosBuildException("No simulator in a booted state.")
            present_error("iOS Build Error", error=error)
            self.step = "failed"
            return
        if uuid == "canceled":
            self.step = "canceled"
            return

        self.picked_device_uuid = uuid
        if self.mode == "build_and_run": self.build_process(process=None)
        else: # if "toggle_simulator"
            command = (self.simctl_command_builder
                .boot()
                .device_uuid(uuid)
                .assemble_command()
            )

            print(command)
            process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True, cwd=self.working_dir)
            process.start()

    def show_current_state(self):
        if self.mode == "build_and_run":
            StatusbarManager.show_status(view=self.window.active_view(), step=self.step)

    def manage_build_internal_state(self):
        print(f"manage_internal_state_begin: {self.step}")
        if self.mode == "build_and_run":
            if self.step == "canceled" or self.step == "failed": pass
            elif self.step == "": self.step = "built"
            elif self.step == "built": self.step = "obtained_product_path"
            elif self.step == "obtained_product_path": self.step = "obrained_devices"
            elif self.step == "obrained_devices": self.step = "device_picked"
            elif self.step == "device_picked": self.step = "installed"
            elif self.step == "installed": self.step = "spawned"
            elif self.step == "spawned": pass
        elif self.mode == "toggle_simulator":
            if self.step == "": self.step = "started"
            elif self.step == "started": self.step = "booted"
            elif self.step == "booted": self.step = ""

        self.show_current_state()
        print(f"manage_internal_state_end: {self.step}")

    def build_process(self, process):
        print(f"on_finished_start: {self.step}")
        self.manage_build_internal_state()
        if self.mode == "toggle_simulator" and self.step != "booted":
            print("manage_build_internal_state()")
            self.window.run_command("run_app_on_ios_devices_select", {"devices": self.devices})

        elif self.mode == "build_and_run":
            if self.step == "built":
                LogProcessor.present_warnings_and_errors_panel(window=self.window)

                command = (self.xcodebuild_command_builder
                    .target_setup()
                    .build_settings()
                    .assemble_command()
                )
                print(command)
                process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True, cwd=self.working_dir)
                process.start()

            elif self.step == "obtained_product_path":
                ## on obtained product path obtaining the devices list
                command = (self.simctl_command_builder
                    .list()
                    .assemble_command()
                )
                print(command)
                process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True, cwd=self.working_dir)
                process.start()

            elif self.step == "obrained_devices":
                ## on both devices list and product path obtained user should pick a device to run
                self.window.run_command("run_app_on_ios_devices_select", {"devices": self.devices, "filter": "Booted"})

            elif self.step == "device_picked":
                ## on device picked by a user fire install
                command = (self.simctl_command_builder
                    .install()
                    .device_uuid(self.picked_device_uuid)
                    .product_path(self.product_path)
                    .assemble_command()
                )

                print(command)
                process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True, cwd=self.working_dir)
                process.start()
            elif self.step == "installed":
                command = (self.simctl_command_builder
                    .launch()
                    .wait_lldb(self.with_debugger)
                    .terminate_previous()
                    .device_uuid(self.picked_device_uuid)
                    .bundle()
                    .assemble_command()
                )
                print(command)
                process = AsyncProcess(cmd=None, shell_cmd=command, env=self.env, listener=self, shell=True, cwd=self.working_dir)
                process.start()

            elif self.step == "spawned":
                super().on_finished(process)

        print(f"on_finished_end: {self.step}")

class SharedState:
    instance: Optional[IosExecCommand] = None

class IosBuildCancelCommand(WindowCommand):
    def run(self):
        if SharedState.instance:
            SharedState.instance.cancel()
