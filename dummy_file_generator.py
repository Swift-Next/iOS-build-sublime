import sublime
import sublime_plugin
import os

class CreateIosSublimeBuildCommand(sublime_plugin.WindowCommand):
    def run(self):
        # Get the folders in the current project
        folders = self.window.folders()

        # Assuming the first folder is the project root
        project_root = folders[0]
        file_path = os.path.join(project_root, '.iOS-sublime-build')

        # Create the file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'w') as _:
                pass  # Create an empty file

            sublime.message_dialog(f"Created: {file_path}")
        else:
            sublime.message_dialog(f"File already exists: {file_path}")