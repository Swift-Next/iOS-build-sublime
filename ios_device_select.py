import sublime_plugin

class RunAppOnIosDevicesSelectCommand(sublime_plugin.WindowCommand):
    def run(self, devices, filter=None):
        print("RunAppOnIosDevicesSelectCommand")
        self.devices = devices
        if filter:
            filtered_devices = {uuid: details for uuid, details in devices.items() if details['status'].lower() == filter.lower()}
        else:
            filtered_devices = devices

        self.items = [(key, f"{value['formatted_output']}") for key, value in filtered_devices.items()]
        self.items = sorted(self.items, key=lambda item: item[1].lower(), reverse=True)

        if len(self.items) == 1:
            print("RunAppOnIosDevicesSelectCommand in")
            selected_uuid = self.items[0][0]  # This is the UUID of the selected item
            self.return_uuid(selected_uuid=selected_uuid)
            return
        elif len(self.items) == 0:
            self.return_uuid(selected_uuid="")
            return

        print("RunAppOnIosDevicesSelectCommand 2")
        # Create a list of tuples where each tuple is (UUID, formatted string)
        # Prepare the list for display using only the formatted string part of each tuple
        display_items = [item[1] for item in self.items]
        self.window.show_quick_panel(display_items, self.on_done)

    def on_done(self, picked):
        if picked == -1:
            return
        # Use the picked index to access the corresponding tuple in self.items
        selected_uuid = self.items[picked][0]  # This is the UUID of the selected item
        print(f"User selected: {selected_uuid}")

        print("on_done")
        self.return_uuid(selected_uuid)

    def return_uuid(self, selected_uuid):
        from .ios_build import SharedState, IosExecCommand # https://stackoverflow.com/a/52927102
        SharedState.instance.handle_booted_device_uuid(selected_uuid)
