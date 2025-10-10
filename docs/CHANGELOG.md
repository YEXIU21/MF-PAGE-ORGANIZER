# Changelog

All notable changes to the MF Page Organizer project.

## [Latest] - 2025-10-10

### Added
- **Middle Scanning Positions**: Added `middle_left` and `middle_right` positions
  - Total scanning positions increased from 6 to 8
  - Better coverage for edge-middle page numbers
  - Improved detection for unusual document layouts

- **Virtual Environment Support**: Build scripts now auto-detect and use `.venv`
  - Ensures consistent dependencies
  - Solves multiple Python installation conflicts
  - Automatic fallback to system Python if .venv not found

- **Comprehensive Diagnostic Logging**: Enhanced error tracking
  - Detailed PaddleOCR initialization logging
  - Singleton pattern status tracking
  - Full traceback on errors
  - Helps identify root causes quickly

- **PyInstaller Hooks**: Added `hook-paddlex.py`
  - Ensures `.version` file is bundled
  - Collects all necessary PaddleX resources
  - Prevents missing file errors

### Fixed
- **CRITICAL: PaddleOCR Not Available in EXE** (2-day issue)
  - Root cause: Multiple Python installations causing dependency mismatch
  - Solution: Virtual environment with proper dependency isolation
  - Added `--collect-data` and `--collect-submodules` for paddle ecosystem
  - Build script now uses `.venv` Python automatically

- **PDX Reinitialization Error**
  - Singleton pattern properly implemented
  - Reuses existing PaddleOCR instance on subsequent calls
  - Prevents "PDX has already been initialized" errors

- **Missing `.version` File**
  - Automatically creates file if missing in EXE mode
  - Prevents `FileNotFoundError` during PaddleOCR initialization
  - Default version: 3.0.0

- **Startup Diagnostics Crashes**
  - Wrapped diagnostics in try-except
  - System continues normally even if diagnostics fail
  - Graceful degradation on errors

### Changed
- **Build Size Optimization**: Reduced from 2.3GB to 500-700MB
  - Excluded PyTorch, TensorFlow, JAX (unnecessary bloat)
  - Only includes required paddle ecosystem components
  - Faster startup and lower memory usage

- **AI Pattern Learning**: Enhanced for 8 scanning positions
  - Learns patterns for all positions
  - Adaptive scan order includes middle positions
  - Maintains 4-6x performance improvement

### Technical Details

#### Build Script Improvements
```python
# Added virtual environment detection
venv_python = root_dir / '.venv' / 'Scripts' / 'python.exe'
if venv_python.exists():
    python_exe = str(venv_python)  # Use .venv

# Added complete paddle ecosystem collection
'--collect-data=paddleocr',
'--collect-data=paddlex',
'--collect-data=paddle',
'--collect-submodules=paddleocr',
'--collect-submodules=paddlex',
```

#### Singleton Pattern Fix
```python
# OLD (broken):
if PaddleNumberDetector._initialized:
    return  # self.ocr not set!

# NEW (fixed):
if PaddleNumberDetector._initialized:
    self.ocr = PaddleNumberDetector._ocr_instance  # Reuse instance
    return
```

#### Scanning Coverage
```
┌─────────────────────────────┐
│ [TOP-LEFT]    [TOP-CENTER]  │ [TOP-RIGHT]
│   ✅300x300     ✅400x300    │   ✅300x300
│ ✅[MID-LEFT]                │ ✅[MID-RIGHT]
│   300x300                   │   300x300
│      MAIN PAGE CONTENT      │
│[BOTTOM-LEFT] [BOTTOM-CENTER]│[BOTTOM-RIGHT]
│   ✅300x300     ✅400x300    │   ✅300x300
└─────────────────────────────┘
```

---

## [Previous] - 2025-09-25

### Added
- AI Pattern Learning system
- Roman numeral detection (i, ii, iii, iv, v, vi, vii, viii, ix, x, xi, xii)
- Adaptive scanning order
- Performance optimization (4-6x faster after learning)
- Blank page detection
- Auto-crop validation
- PDF optimization

### Fixed
- GUI startup issues
- Missing tkinter imports
- Module import errors in EXE builds

---

## [Initial] - 2025-09-01

### Added
- Basic page organization functionality
- PaddleOCR integration
- GUI interface
- PDF creation
- Image preprocessing
- Batch processing
- Output management

---

## Upgrade Guide

### From Previous Version to Latest

1. **Create Virtual Environment:**
   ```bash
   python -m venv .venv
   ```

2. **Install Dependencies:**
   ```bash
   .venv\Scripts\python.exe -m pip install paddleocr paddlepaddle opencv-python pillow img2pdf pikepdf
   ```

3. **Rebuild EXE:**
   ```bash
   python build_scripts/build_exe_onefile.py
   ```

4. **Verify:**
   - Check EXE size: Should be 500-700MB
   - Test with sample pages
   - Verify PaddleOCR initialization in logs

---

## Breaking Changes

### None

All changes are backward compatible. Existing functionality preserved.

---

## Deprecations

### None

No features deprecated in this release.

---

## Known Issues

1. **First Run Download:**
   - If models not bundled, downloads on first use
   - Requires internet connection
   - Takes 5-10 minutes

2. **GPU Support:**
   - Currently CPU only
   - GPU support planned for future release

---

## Contributors

- AI Assistant (Cascade)
- User (YEXIU21)

---

## License

Apache License 2.0

---

## Support

For issues and questions:
- Check TROUBLESHOOTING_GUIDE.md
- Review logs in `logs/` folder
- Enable DEBUG mode for detailed diagnostics
