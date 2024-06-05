class SimulatorCommandBuilder:
    def __init__(self, bundle_id: str):
        self.bundle_id = bundle_id
        self.__command__ = __INITIAL_COMMAND__

    def list(self) -> 'SimulatorCommandBuilder':
        self.__command__ += ' ' + 'list'
        return self

    def device_uuid(self, device_uuid: str) -> 'SimulatorCommandBuilder':
        self.__command__ += ' ' + device_uuid
        return self

    def product_path(self, product_path: str) -> 'SimulatorCommandBuilder':
        self.__command__ += ' ' + product_path
        return self

    def boot(self) -> 'SimulatorCommandBuilder':
        self.__command__ += ' ' + 'boot'
        return self

    def install(self) -> 'SimulatorCommandBuilder':
        self.__command__ += ' ' + 'install'
        return self

    def wait_lldb(self, enabled: bool) -> 'SimulatorCommandBuilder':
        self.__command__ += ' ' + "--wait-for-debugger" if enabled else ""
        return self

    def launch(self) -> 'SimulatorCommandBuilder':
        self.__command__ += ' ' + 'launch'
        return self

    def terminate_previous(self) -> 'SimulatorCommandBuilder':
        self.__command__ += ' ' + '--terminate-running-process'
        return self

    def bundle(self) -> 'SimulatorCommandBuilder':
        self.__command__ += ' ' + self.bundle_id
        return self

    def assemble_command(self) -> str:
        command = self.__command__
        self.__command__ = __INITIAL_COMMAND__
        return command

__INITIAL_COMMAND__ = 'xcrun simctl'
