class XcodebuildCommandBuilder:
    def __init__(self, project_filename: str, scheme: str):
        self.project_name = project_filename
        self.scheme = scheme
        self.project_kind = 'workspace' if project_filename.split('.')[1] == "xcworkspace" else "project"
        self.__command__ = __INITIAL_COMMAND__

    def quiet(self) -> 'XcodebuildCommandBuilder':
        self.__command__ += ' ' + '-quiet'
        return self

    def manage_bundle(self) -> 'XcodebuildCommandBuilder':
        self.__command__ = f'rm -rf /tmp/{self.project_name}/bundle;' + ' ' + self.__command__
        self.__command__ += ' ' + f'-resultBundlePath /tmp/{self.project_name}/bundle'
        return self

    def target_setup(self) -> 'XcodebuildCommandBuilder':
        self.__command__ += ' ' + f'-{self.project_kind} {self.project_name} -scheme {self.scheme}'
        return self

    def destination_setup(self) -> 'XcodebuildCommandBuilder':
        self.__command__ += ' ' + "-destination 'generic/platform=iOS Simulator'"
        return self

    def build(self) -> 'XcodebuildCommandBuilder':
        self.__command__ += ' ' + 'build'
        return self

    def clean(self) -> 'XcodebuildCommandBuilder':
        self.__command__ += ' ' + 'clean'
        return self

    def build_settings(self) -> 'XcodebuildCommandBuilder':
        self.__command__ += ' ' + '-showBuildSettings'
        return self

    def assemble_command(self) -> str:
        command = self.__command__
        self.__command__ = __INITIAL_COMMAND__
        return command

__INITIAL_COMMAND__ = 'xcodebuild'
