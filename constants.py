WARNING_PANE = "iOS Build Pane"

BUILD_PANE = "exec"

OPEN_PROJECT = "open {projct_path}"

SIMCTL_LIST_CMD = "xcrun simctl list"
SIMCTL_BOOT_DEVICE_CMD = "xcrun simctl boot {device_uuid}"

REMOVE_BUNDLE_CMD = "rm -rf /tmp/{project_name}/bundle;"

BUILD_CMD = "xcodebuild -quiet -{project_kind} {project_name} -scheme {scheme} -destination 'generic/platform=iOS Simulator' -resultBundlePath /tmp/{project_name}/bundle build"
CLEAN_CMD = "xcodebuild -{project_kind} {project_name} -scheme {scheme} -destination 'generic/platform=iOS Simulator' clean"
CLEAN_BUILD_CMD = "xcodebuild -{project_kind} {project_name} -scheme {scheme} -destination 'generic/platform=iOS Simulator' clean build"

BUILT_SETTINGS = "xcodebuild -{project_kind} {project_name} -scheme {scheme} -showBuildSettings"

INSTALL_APP = "xcrun simctl install {device_uuid} {product_path}"
RUN_APP = "xcrun simctl launch {with_debugger} --terminate-running-process {device_uuid} {bundle_id}"