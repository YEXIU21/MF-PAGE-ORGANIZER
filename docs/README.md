# MF Page Organizer - Documentation

Welcome to the MF Page Organizer documentation. This system automatically organizes scanned document pages using AI and OCR technology.

## 📋 Documentation Index

### 🚀 Getting Started
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - How to install and set up the system
- **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - How to build standalone EXE files

### 🏗️ System Architecture  
- **[FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md)** - Project structure and organization
- **[FINAL_IMPLEMENTATION.md](FINAL_IMPLEMENTATION.md)** - Complete system implementation details
- **[SYSTEM_COMPLETE.md](SYSTEM_COMPLETE.md)** - System completion summary

### 🔧 Technical Details
- **[PADDLEOCR_MIGRATION.md](PADDLEOCR_MIGRATION.md)** - OCR engine migration details
- **[SYSTEM_OVERHAUL_COMPLETE.md](SYSTEM_OVERHAUL_COMPLETE.md)** - System overhaul documentation
- **[CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md)** - Code cleanup and optimization summary

## ✨ Latest Features

### Blank Page Portrait Orientation ✅
- **Automatic Detection**: Identifies blank landscape pages
- **Portrait Rotation**: Rotates blank landscape pages to portrait orientation
- **GUI Control**: Toggle via "Rotate landscape blanks to portrait" checkbox
- **Default Setting**: Portrait orientation enabled by default
- **Configuration**: `rotate_blank_to_portrait: true` in config.json

### Enhanced Build System ✅  
- **Fast Startup Build**: Quick startup without splash screen
- **Enhanced Build**: Professional splash screen with loading animation
- **Icon Handling**: Fixed window icon display in both EXE and script modes
- **Configuration**: Config files properly included in builds

## 🎯 Key Capabilities

1. **Smart Page Detection**
   - Roman numeral recognition (i, ii, iii, iv, v, vi, vii, viii, ix, x, xi, xii)
   - Arabic number detection (1, 2, 3, 4, 5...)
   - Multiple position scanning (top-left, top-right, bottom-left, center)
   - Content-based reordering

2. **Blank Page Management**
   - Blank page identification
   - Configurable removal modes (start, end, start & end, all, none)
   - Automatic landscape-to-portrait rotation
   - Portrait orientation as default

3. **Image Processing**
   - Auto-rotation and orientation correction
   - Auto-cropping of borders and margins
   - Dark circle and spot removal
   - Image quality enhancement
   - 300 DPI conversion

4. **User Experience**
   - Professional GUI with dark/light theme support
   - Drag & drop file support
   - Real-time progress tracking
   - Splash screen with loading animation
   - Cancellable processing

## 📁 Project Structure

```
MF Page Organizer/
├── docs/                    # All documentation
├── build_scripts/           # EXE build scripts
├── core/                    # Core processing modules
├── utils/                   # Utility modules
├── gui_mf.py               # Main GUI application
├── main.py                 # CLI interface
├── config.json             # System configuration
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

1. **For Users**: Download and run the EXE from releases
2. **For Developers**: See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
3. **For Building**: See [BUILD_GUIDE.md](BUILD_GUIDE.md)

## 📞 Support

For issues, feature requests, or questions:
- Check the documentation in this folder
- Review the troubleshooting sections in relevant guides
- Examine the system logs in the GUI for error details
