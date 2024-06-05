from sublime import Window, View
from .constants import BUILD_PANE, WARNING_PANE

class PaneManager:
    @staticmethod
    def get_build_pane(window: Window) -> View:
        return window.find_output_panel(BUILD_PANE) or window.create_output_panel(BUILD_PANE)

    @staticmethod
    def get_log_navigation_pane(window: Window) -> View:
        return window.find_output_panel(WARNING_PANE) or window.create_output_panel(WARNING_PANE)

    @staticmethod
    def show_warining_pane(window: Window):
        window.run_command("show_panel", {"panel": f"output.{WARNING_PANE}"})

    @staticmethod
    def clear_build_pane(window: Window):
        build_pane = PaneManager.get_build_pane(window=window)
        build_pane.set_read_only(False)
        build_pane.run_command('select_all')
        build_pane.run_command('right_delete')
        build_pane.set_read_only(True)

def setup_with(self: View, file_regex: str):
    self.settings().set("result_file_regex", file_regex)
    self.settings().set("word_wrap", True)
    self.settings().set("line_numbers", True)
    self.settings().set("gutter", True)
    self.settings().set("word_wrap", True)
    self.settings().set("scroll_past_end", False)

## Oh, for fuck sake, seriously, this is a type extention in Python?
View.setup_with = setup_with
