from typing import List, Tuple, Dict
from sublime import Window
from .panes_manager import PaneManager

class LogProcessor:

    @staticmethod
    def process_errors_(errors_struct: List[Tuple[str, int, int, str]]) -> Dict[str, List[Tuple[int, int, str]]]:
        errs_by_file: Dict[str, List[Tuple[int, int, str]]] = {}

        for file, line, column, text in errors_struct:
            if file not in errs_by_file:
                errs_by_file[file] = []
            if (line, column, text) not in errs_by_file[file]:
                errs_by_file[file].append((line, column, text))

        return errs_by_file

    @staticmethod
    def get_priority_(error: str) -> int:
        if "error" in error:
            return 0
        elif "warning" in error:
            return 1
        elif "note" in error:
            return 2
        return 3  # Default to the lowest priority if none of the expected types are found

    @staticmethod
    def sort_errors_and_files_(errs_by_file: Dict[str, List[Tuple[int, int, str]]]) -> Dict[str, List[Tuple[int, int, str]]]:
        sorted_errs_by_file: Dict[str, List[Tuple[int, int, str]]] = {}

        # Sort errors within each file
        for file, errors in errs_by_file.items():
            errors.sort(key=lambda x: LogProcessor.get_priority_(x[2]))
            sorted_errs_by_file[file] = errors

        # Sort files by the highest priority error they contain
        sorted_files = sorted(sorted_errs_by_file.keys(), key=lambda file: LogProcessor.get_priority_(sorted_errs_by_file[file][0][2]))

        return {file: sorted_errs_by_file[file] for file in sorted_files}

    @staticmethod
    def present_warnings_and_errors_panel(window: Window):
        errors_list = PaneManager.get_build_pane(window=window).find_all_results_with_text()
        print("errors_list",len(errors_list))

        errs_by_file = LogProcessor.process_errors_(errors_list)

        sorted_errors_by_file = LogProcessor.sort_errors_and_files_(errs_by_file)

        warning_pane = PaneManager.get_log_navigation_pane(window=window)
        warning_pane.set_read_only(False)
        warning_pane.run_command('select_all')  # Select all existing content
        warning_pane.run_command('right_delete')
        warning_pane.set_read_only(True)

        if len(sorted_errors_by_file.keys()) > 0:
            warning_pane.settings().set("result_file_regex", "^(?=/)(.*)")
            warning_pane.settings().set("result_line_regex", "\\s+(\\d+):(\\d+):\\s(.*)")
            # warning_pane.settings().set("result_base_dir", "/")
            warning_pane.settings().set("word_wrap", True)
            warning_pane.settings().set("line_numbers", True)
            warning_pane.settings().set("gutter", True)
            warning_pane.settings().set("scroll_past_end", False)
            warning_pane.assign_syntax("iOS-build-log.sublime-syntax")
            for file in sorted_errors_by_file:
                warning_pane.run_command('append', {'characters': file, 'force': True})
                warning_pane.run_command('append', {'characters': "\n", 'force': True})
                for line, column, text in sorted_errors_by_file[file]:
                    warning_pane.run_command('append', {'characters': f"    {line}:{column}: {text}", 'force': True})  # Append the formatted errors
                    warning_pane.run_command('append', {'characters': "\n", 'force': True})
                warning_pane.run_command('append', {'characters': "\n", 'force': True})
            PaneManager.show_warining_pane(window=window)
