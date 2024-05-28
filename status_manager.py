from sublime import View, status_message

class StatusbarManager:
    @staticmethod
    def show_status(view: View, step: str):
        if step == "canceled":
            view.set_status("swift_build_status", "")
            status_message("Build canceled.")
        elif step == "failed":
            view.set_status("swift_build_status", "")
            status_message("Build failed.")
        elif step == "":
            view.set_status("swift_build_status", "Building...")
        elif step == "built":
            view.set_status("swift_build_status", "Obtaining Product Path...")
        elif step == "obtained_product_path":
            view.set_status("swift_build_status", "Obraining Devices...")
        elif step == "obrained_devices":
            view.set_status("swift_build_status", "Picking Devices...")
        elif step == "device_picked":
            view.set_status("swift_build_status", "App Installation...")
        elif step == "installed":
            view.set_status("swift_build_status", "App Spawning...")
        elif step == "spawned":
            view.set_status("swift_build_status", "")
