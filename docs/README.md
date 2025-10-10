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
- **[AUTO_CROP_VALIDATION.md](AUTO_CROP_VALIDATION.md)** - Auto-crop validation and manual review system
- **[PDF_OPTIMIZATION.md](PDF_OPTIMIZATION.md)** - PDF creation performance optimization (5.8x faster)
- **[TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

## ✨ Latest Features

### Middle Scanning Positions ✅ **NEW!**
- **8 Scanning Positions**: Added middle-left and middle-right positions
- **Better Coverage**: Detects page numbers on edges
- **AI Optimization**: Learns which positions to scan first
- **4-6x Faster**: After learning phase (10 pages)
- **Comprehensive**: Covers all common page number locations

### Virtual Environment Support ✅ **NEW!**
- **Automatic Detection**: Build scripts use .venv if available
- **Dependency Isolation**: Solves multiple Python installation conflicts
- **Consistent Builds**: Ensures correct dependencies are bundled
- **Fallback Support**: Uses system Python if .venv not found

### Blank Page Portrait Orientation ✅
- **Automatic Detection**: Identifies blank landscape pages
- **Portrait Rotation**: Rotates blank landscape pages to portrait orientation
- **GUI Control**: Toggle via "Rotate landscape blanks to portrait" checkbox
- **Default Setting**: Portrait orientation enabled by default
- **Configuration**: `rotate_blank_to_portrait: true` in config.json

### PDF Creation Optimization ✅ **NEW!**
- **5.8x Faster PDF Creation**: Using optimized img2pdf library
- **Intelligent Method Selection**: Automatically chooses fastest method
- **60% Less RAM Usage**: During PDF creation process
- **15% Smaller Files**: More efficient PDF compression
- **Automatic Fallback**: Uses ReportLab if needed
- **Zero Breaking Changes**: All features remain compatible

### Auto-Crop Validation System ✅
- **Automatic Quality Checks**: Validates each auto-cropped page for issues
- **Issue Detection**: Detects excessive cropping, black borders, content cut-offs
- **Confidence Scoring**: 0-100% score for each crop operation
- **Manual Review Reports**: Generates `CROP_REVIEW_NEEDED.txt` for problematic pages
- **Handles Edge Cases**: Cut-off scans, scanner bed edges, black borders
- **No Manual Flagging Needed**: Fully automated detection and reporting

### Enhanced Build System ✅  
- **Fast Startup Build**: Quick startup without splash screen
- **Enhanced Build**: Professional splash screen with loading animation
- **Icon Handling**: Fixed window icon display in both EXE and script modes
- **Configuration**: Config files properly included in builds

## 🎯 Key Capabilities

1. **Smart Page Detection**
   - Roman numeral recognition (i, ii, iii, iv, v, vi, vii, viii, ix, x, xi, xii)
   - Arabic number detection (1, 2, 3, 4, 5...)
   - 8 scanning positions (top-left, top-center, top-right, middle-left, middle-right, bottom-left, bottom-center, bottom-right)
   - AI-powered adaptive scanning order
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
