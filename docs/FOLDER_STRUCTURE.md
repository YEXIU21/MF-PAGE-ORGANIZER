# 📁 Project Folder Structure

## 🎯 **Quick Navigation**

```
Page Automation/
│
├── 🚀 gui_mf.py                    # Main application (double-click to run)
├── 🔧 main.py                      # CLI version
├── 📋 requirements.txt             # Python dependencies
│
├── 📦 build_scripts/               # ⭐ BUILD STANDALONE EXE HERE!
│   ├── BUILD_STANDALONE_EXE.bat   # One-click build script
│   ├── BUILD_INSTRUCTIONS.md      # How to build
│   ├── README.md                  # Build folder guide
│   └── dist/PageAutomation/       # 🎉 FINAL EXE OUTPUT (after build)
│       ├── PageAutomation.exe     # Standalone executable
│       ├── README.txt             # User guide
│       └── QUICK_START.txt        # Quick start
│
├── 🧠 core/                        # Core system logic
│   ├── numbering_system.py        # Page ordering (100% accurate!)
│   ├── paddle_number_detector.py  # OCR detection
│   ├── ai_pattern_learning.py     # Adaptive learning
│   └── ...                        # Other core modules
│
├── 🛠️ utils/                       # Utility functions
│   ├── logger.py                  # Logging system
│   ├── config.py                  # Configuration
│   └── ...                        # Other utilities
│
├── 📚 docs/                        # Documentation
│   ├── FINAL_IMPLEMENTATION.md    # Complete technical docs
│   ├── INSTALLATION_GUIDE.md      # Setup guide
│   └── ...                        # Other documentation
│
└── 🧪 tests/                       # Test files
    └── ...                        # Test scripts
```

---

## 🎯 **What Each Folder Does**

### **`build_scripts/`** ⭐ MOST IMPORTANT FOR BUILDING EXE
**Purpose**: Build standalone executable for distribution

**What's Inside**:
- Build scripts (`.bat` files)
- Build instructions
- Icon file
- **`dist/PageAutomation/`** - Final EXE output (after building)

**When to Use**:
- When you want to create standalone EXE
- When distributing to non-technical users
- When you need offline-capable version

**How to Use**:
```cmd
cd build_scripts
BUILD_STANDALONE_EXE.bat
```

---

### **`core/`** - System Logic
**Purpose**: Core functionality of the page automation system

**Key Files**:
- `numbering_system.py` - Page ordering logic (100% accurate!)
- `paddle_number_detector.py` - OCR and number detection
- `ai_pattern_learning.py` - Adaptive learning system
- `ocr_engine.py` - OCR engine wrapper
- `confidence_system.py` - Confidence scoring
- `blank_page_detector.py` - Blank page detection

**When to Modify**:
- Improving accuracy
- Adding new features
- Fixing bugs

---

### **`utils/`** - Utilities
**Purpose**: Helper functions and utilities

**Key Files**:
- `logger.py` - Logging system
- `config.py` - Configuration management
- `file_handler.py` - File operations

**When to Modify**:
- Changing logging behavior
- Updating configuration
- Adding utility functions

---

### **`docs/`** - Documentation
**Purpose**: Project documentation

**Key Files**:
- `FINAL_IMPLEMENTATION.md` - Complete technical documentation
- `INSTALLATION_GUIDE.md` - Setup instructions
- `SYSTEM_COMPLETE.md` - System architecture

**When to Use**:
- Understanding the system
- Learning how it works
- Troubleshooting

---

### **`tests/`** - Tests
**Purpose**: Test files and test data

**When to Use**:
- Testing new features
- Verifying accuracy
- Debugging

---

## ⚠️ **Common Confusions - CLARIFIED!**

### **Q: Why are there TWO "build" folders?**
**A**: There aren't! Here's what happens:

1. **`build_scripts/`** - This is YOUR folder with build scripts
   - You create this
   - Contains build tools
   - Always keep this!

2. **`build/`** (in root) - This is PyInstaller's TEMPORARY folder
   - Auto-created during build
   - Contains temporary files
   - Can be deleted after build
   - Will be recreated next build

3. **`build_scripts/dist/`** - This is the FINAL OUTPUT
   - Contains your EXE
   - This is what you distribute!
   - Keep this after building!

### **Q: Where is my EXE after building?**
**A**: `build_scripts\dist\PageAutomation\PageAutomation.exe`

### **Q: What can I delete?**
**A**: Safe to delete:
- Root `build/` folder (PyInstaller temporary)
- Root `dist/` folder (if exists)
- `*.spec` files in root
- `__pycache__/` folders
- `.pyc` files

**DON'T delete**:
- `build_scripts/` folder
- `build_scripts/dist/PageAutomation/` (your EXE!)
- `core/`, `utils/`, `docs/` folders
- Source code files

---

## 🚀 **Quick Actions**

### **Run Application (Development)**:
```cmd
python gui_mf.py
```

### **Build Standalone EXE**:
```cmd
cd build_scripts
BUILD_STANDALONE_EXE.bat
```

### **Clean Up Temporary Files**:
```cmd
# Delete PyInstaller temporary files
rmdir /s /q build
rmdir /s /q dist
del *.spec
```

### **Test the System**:
```cmd
python main.py --input "test_folder" --output "output" --verbose
```

---

## 📊 **Folder Sizes (Approximate)**

- **Source Code**: ~5 MB
- **Dependencies** (if installed): ~500 MB
- **Build Temporary**: ~1 GB (deleted after build)
- **Final EXE Package**: ~300 MB
- **EXE Only**: ~88 MB

---

## ✅ **Checklist for Clean Project**

- [ ] Root folder has only source code
- [ ] `build_scripts/` has build tools
- [ ] `build_scripts/dist/PageAutomation/` has final EXE
- [ ] No `build/` or `dist/` in root (or can be deleted)
- [ ] Documentation is up to date
- [ ] `.gitignore` excludes temporary files

---

**Last Updated**: October 8, 2025  
**Version**: 2.0  
**Status**: Production-Ready
