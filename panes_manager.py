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
