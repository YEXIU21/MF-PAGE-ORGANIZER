# MF PAGE ORGANIZER - PROJECT STRUCTURE

## 📁 **Clean and Organized Structure**

### **Root Directory (Main Files Only):**
```
F:\Page Automation\
├── gui_mf.py              ← Main GUI application (RUN THIS)
├── main.py                ← Command-line interface
├── infinity.py            ← Interactive prompt system
├── config.json            ← Configuration settings
├── requirements.txt       ← Python dependencies
├── README.md              ← Quick start guide
│
├── core/                  ← Core processing modules
├── utils/                 ← Utility functions
├── docs/                  ← All documentation (MOVED HERE)
├── build_scripts/         ← Build files (MOVED HERE)
├── cache/                 ← AI cache and learning data
├── build/                 ← Compiled executables
└── tests/                 ← Test files
```

---

## 🚀 **Quick Start:**

### **To Use the Tool:**
```
1. Double-click: gui_mf.py
   OR
2. Run: python gui_mf.py
```

### **To Read Documentation:**
```
All documentation moved to: docs/
- SYSTEM_STATUS.md - Current system status
- FEATURE_COMPATIBILITY.md - Feature guide
- AI_IMPROVEMENTS.md - AI features
- And more...
```

### **To Build Standalone:**
```
All build files moved to: build_scripts/
- build_final.py - Build script
- final.spec - PyInstaller spec
```

---

## 📂 **Folder Details:**

### **core/** - Core Processing Modules
```
├── input_handler.py           ← Load images/PDFs
├── preprocessor.py            ← Image enhancement
├── ocr_engine.py              ← OCR + AI detection
├── advanced_number_detector.py ← AI page number detection
├── numbering_system.py        ← Pattern analysis
├── content_analyzer.py        ← Content relationships
├── confidence_system.py       ← Confidence scoring
├── output_manager.py          ← Generate output
├── blank_page_detector.py     ← Remove blank pages
├── smart_cache.py             ← AI memory system
├── ai_learning.py             ← Learning system
├── performance_optimizer.py   ← RAM adaptation
└── embedded_ocr.py            ← Embedded OCR
```

### **utils/** - Utility Functions
```
├── config.py                  ← Configuration management
├── logger.py                  ← Logging system
└── ...
```

### **docs/** - Documentation (ORGANIZED)
```
├── SYSTEM_STATUS.md           ← System check results
├── FEATURE_COMPATIBILITY.md   ← Feature guide
├── AI_IMPROVEMENTS.md         ← AI features explained
├── AI_DETECTION_METHOD.md     ← How AI detects pages
├── ADAPTIVE_PERFORMANCE.md    ← Performance optimization
├── OUTPUT_STRUCTURE.md        ← Output folder structure
├── ERROR_FIXES.md             ← Bug fixes applied
├── And more...
```

### **build_scripts/** - Build Files (ORGANIZED)
```
├── build_final.py             ← Build standalone EXE
├── final.spec                 ← PyInstaller configuration
├── simple.spec                ← Simple build config
├── BUILD_STATUS.txt           ← Build status
└── BUILD_SUMMARY.txt          ← Build summary
```

### **cache/** - AI Data (Auto-Generated)
```
├── cache_index.json           ← Cache index
├── ai_learning.json           ← Learning data
└── *.pkl                      ← Cached OCR results
```

### **build/** - Compiled Executables
```
└── MF_Page_Organizer.exe      ← Standalone application
```

---

## 🎯 **What to Use:**

### **For End Users:**
```
✅ gui_mf.py - Main application
✅ README.md - Quick guide
✅ docs/ - Full documentation
```

### **For Developers:**
```
✅ core/ - Source code
✅ utils/ - Utilities
✅ main.py - CLI interface
✅ tests/ - Test files
```

### **For Building:**
```
✅ build_scripts/ - Build tools
✅ requirements.txt - Dependencies
```

---

## 🧹 **Cleanup Summary:**

### **What Was Moved:**

1. **Documentation Files** → `docs/`
   - All .md files (except README.md)
   - 19 documentation files organized

2. **Build Files** → `build_scripts/`
   - build_final.py
   - *.spec files
   - BUILD*.txt files

3. **Deleted:**
   - rebuild_standalone.py (empty file)

### **What Stayed in Root:**
- ✅ gui_mf.py (main application)
- ✅ main.py (CLI)
- ✅ infinity.py (interactive system)
- ✅ config.json (settings)
- ✅ requirements.txt (dependencies)
- ✅ README.md (quick guide)

---

## 📊 **Before vs After:**

### **Before (Crowded):**
```
F:\Page Automation\
├── gui_mf.py
├── main.py
├── ADAPTIVE_PERFORMANCE.md
├── AI_DETECTION_METHOD.md
├── AI_IMPROVEMENTS.md
├── BUILD_STATUS.txt
├── CANCEL_FUNCTIONALITY_FIX.md
├── CHECKBOX_VERIFICATION.md
├── DEFAULT_SETTINGS.md
├── DELIVERY_CHECKLIST.md
├── ERROR_FIXES.md
├── FEATURE_COMPATIBILITY.md
├── ... (19 more .md files)
├── build_final.py
├── final.spec
├── simple.spec
└── ... (confusing!)
```

### **After (Clean):**
```
F:\Page Automation\
├── gui_mf.py              ← Run this!
├── main.py
├── infinity.py
├── config.json
├── requirements.txt
├── README.md
├── core/                  ← Source code
├── utils/                 ← Utilities
├── docs/                  ← All docs here
├── build_scripts/         ← Build files here
├── cache/                 ← AI data
└── build/                 ← Executables
```

**Much cleaner and easier to navigate!**

---

## 💡 **Tips:**

1. **To run the tool**: Just use `gui_mf.py`
2. **To read docs**: Check `docs/` folder
3. **To build**: Use `build_scripts/build_final.py`
4. **To configure**: Edit `config.json`

**Everything is now organized and easy to find!**

© 2025 MF Page Organizer - Clean Structure
