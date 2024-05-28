from sublime import Window, View
from .constants import BUILD_PANE, WARNING_PANE

class PaneManager:
    @staticmethod
    def create_output_panel(window: Window, name: str, file_regex: str) -> View:
        build_pane = window.create_output_panel(BUILD_PANE)
        build_pane.settings().set("result_file_regex", file_regex)
        build_pane.settings().set("word_wrap", True)
        build_pane.settings().set("line_numbers", True)
        build_pane.settings().set("gutter", True)
        build_pane.settings().set("word_wrap", True)
        build_pane.settings().set("scroll_past_end", False)
        return build_pane

    @staticmethod
    def get_build_pane(window: Window, file_regex: str = '') -> View:
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
