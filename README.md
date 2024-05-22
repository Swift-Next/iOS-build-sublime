# iOS build system for Sublime Text 4

> [!NOTE] 
> It's in deep WIP state. So now only a few golden paths are working and yet working quite roughly.


## Usage

You have to add a setup config for your xcodeproject in your sublime-project as follow:

```json
"settings": {
    "ios_build_system": {
        "projectfile_name": "YourApp.xcodeproj", // could be .xcworkspace as well
        "scheme": "AppScheme",
        "bundle": "com.yourapp.yourapp",
    },
},
```

Then all the commands should work as expected.