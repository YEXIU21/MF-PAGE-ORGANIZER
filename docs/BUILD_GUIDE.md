# MF Page Organizer - Build Guide

This document explains how to build standalone EXE files for Windows using the build scripts located in the `build_scripts/` folder.

## Available Build Options

### 1. Fast Startup Build (Recommended for Development)
**File:** `build_scripts/build_exe.py`
**Command:** `python build_exe.py`

**Features:**
- ✅ Fast startup (no splash screen)
- ✅ Professional window icon
- ✅ All core functionality
- ✅ Configuration file included
- ✅ No console window
- ⚡ **Faster startup time**

**Output:** `build_scripts/dist/PageAutomation/PageAutomation.exe`

### 2. Enhanced Build with Splash Screen
**File:** `build_scripts/build_exe_with_splash.py`
**Command:** `python build_exe_with_splash.py`

**Features:**
- ✅ Beautiful splash screen with loading animation
- ✅ Professional window icon
- ✅ All core functionality
- ✅ Configuration file included
- ✅ No console window
- 🎨 **Professional user experience**

**Output:** `build_scripts/dist/PageAutomationEnhanced/PageAutomationEnhanced.exe`

## How to Build

1. **Navigate to build_scripts folder:**
   ```cmd
   cd "build_scripts"
   ```

2. **Choose your build type:**

   **For fast startup (recommended for testing):**
   ```cmd
   python build_exe.py
   ```

   **For enhanced experience with splash screen:**
   ```cmd
   python build_exe_with_splash.py
   ```

3. **Wait for build to complete** (5-10 minutes)

4. **Test the EXE:**
   - Navigate to the `dist` folder
   - Double-click the EXE file to test

## Requirements

- Python 3.8+
- PIL (Pillow) - for icon conversion
- PyInstaller - automatically installed by build script
- img2pdf - for optimized PDF creation (5.8x faster)
- pikepdf - dependency of img2pdf

**Note**: Run `pip install -r requirements.txt` to install all dependencies before building.

## Icon Handling Fixed ✅

Both build scripts now properly handle window icons:

1. **Icon Conversion**: Convert `PageAutomationic.png` to `icon.ico`
2. **Bundle Inclusion**: Include the icon in the EXE bundle via `--add-data`
3. **EXE Icon**: Set the EXE icon for Windows via `--icon`
4. **Runtime Icon**: GUI looks for `icon.ico` in `sys._MEIPASS` for EXE mode
5. **Script Fallback**: Include PNG fallback for script mode

## Blank Page Portrait Orientation ✅

The system now includes enhanced blank page handling:

- **Landscape Detection**: Automatically detects blank landscape pages
- **Portrait Rotation**: Rotates blank landscape pages to portrait (default orientation)
- **GUI Control**: "Rotate landscape blanks to portrait" checkbox in GUI
- **Default Setting**: Portrait orientation is enabled by default
- **Config Integration**: `rotate_blank_to_portrait: true` in config.json

## File Structure After Build

```
build_scripts/
├── build_exe.py                    # Fast startup build
├── build_exe_with_splash.py        # Enhanced build with splash
├── icon.ico                        # Generated icon file
├── dist/
│   ├── PageAutomation/             # Fast startup version
│   │   └── PageAutomation.exe
│   └── PageAutomationEnhanced/     # Enhanced version with splash
│       └── PageAutomationEnhanced.exe
└── build/                          # Temporary build files
```

## Troubleshooting

**If build fails:**
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check that `PageAutomationic.png` exists in the root directory
3. Run the build script from the `build_scripts` folder
4. Check for error messages in the console output

**If icon doesn't show:**
- The icon is now properly included in both build versions
- For EXE mode: looks for `icon.ico` in `sys._MEIPASS`
- For script mode: converts PNG to ICO automatically

**If splash screen doesn't work:**
- Use the enhanced build: `build_exe_with_splash.py`
- Ensure `splash_screen.py` exists in the root directory
- All required modules are included as hidden imports

## Distribution

After successful build:
1. Navigate to `build_scripts/dist/`
2. Copy the entire folder (e.g., `PageAutomation/` or `PageAutomationEnhanced/`)
3. Distribute the entire folder to users
4. Users can run the EXE directly without Python installation
