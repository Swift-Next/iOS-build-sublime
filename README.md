# iOS build system for Sublime Text 4

## Usage

1. Sublime Text has a limitation in its internals to map a given build system to a scope of a project. If you're unable to find `iOS - *` build options on your `primary+shift+b` key press, you should run the given command: `iOS build: Create dummy file in project root` in command palette. It will creates a dummy file `.iOS-sublime-build` in the root of your project folder to force ST to add this build system to the project.

> [!NOTE]
> You're free to add this file into `.gitignore` or delete it at any moment, it stores no important info within itself.

2. You have to setup this plugin regarding to Xcode project you're working with in `*.sublime-project` settings as follow:

```json
"settings": {
    "ios_build_system": {
        "projectfile_name": "YourApp.xcodeproj", // could be .xcworkspace as well
        "scheme": "AppScheme",
        "bundle": "com.yourapp.yourapp",
    },
},
```

After this all building commands should work as expected now.
