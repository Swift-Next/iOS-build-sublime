from sublime_plugin import EventListener
from sublime import View, QueryOperator
from .ios_build import SharedState

class IosExecCommandRunningContext(EventListener):
    def on_query_context(self, view: View, key: str, operator: QueryOperator, operand: str, match_all: bool):
        if key == "ios_exec_command_running":
            return SharedState.instance and SharedState.instance.current_process
        return None
