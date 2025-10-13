# PaddleX OCR Dependency Fix

## Problem Identified
The standalone EXE build was failing with:
```
paddlex.utils.deps.DependencyError: `OCR` requires additional dependencies.
To install them, run `pip install "paddlex[ocr]==<PADDLEX_VERSION>"`
```

## Root Cause
1. **Missing Dependency**: `paddlex[ocr]` was not included in `requirements.txt`
2. **PaddleOCR 3.2+ Requirement**: PaddleOCR 3.2+ uses PaddleX for its pipeline functionality
3. **Build Script Gap**: The PyInstaller build script didn't explicitly collect PaddleX OCR modules

## Fixes Applied

### 1. Updated requirements.txt
**Added**: `paddlex[ocr]>=3.0.0` to ensure OCR dependencies are installed

### 2. Updated build_exe_onefile.py
- Added explicit hidden imports for PaddleX OCR modules:
  - `paddleocr._pipelines.base`
  - `paddleocr._pipelines.ocr`
  - `paddlex.inference.pipelines`
  - `paddlex.utils.deps`
  - `paddle.inference`
- Added Python 3.12 version check (as per build requirements)
- Updated documentation to reflect PaddleX[ocr] support

### 3. Enhanced hook-paddlex.py
- Added explicit OCR-critical module collection
- Improved metadata file collection (.version, .json, .yaml)
- Better error handling for missing modules

## Next Steps

### Before Building:
1. **Install Dependencies** (Python 3.12 recommended):
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify PaddleX Installation**:
   ```python
   python -c "import paddlex; print(paddlex.__version__)"
   ```

3. **Test OCR Functionality**:
   ```python
   python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(); print('OK')"
   ```

### Building the EXE:
```bash
cd build_scripts
python build_exe_onefile.py
```

## Expected Results
- ✅ PaddleOCR initializes successfully in the EXE
- ✅ No more `DependencyError` for OCR functionality
- ✅ Filename fallback is no longer needed
- ✅ OCR operates at full accuracy (not just 60% confidence)

## Testing the Fix
After building, test the EXE with a book scan to ensure:
1. OCR engine initializes without errors
2. Page numbers are detected using OCR (not filename fallback)
3. No `self.ocr is None` errors in logs
4. System reports "PaddleOCR: Installed" in diagnostics

## Files Modified
1. `requirements.txt` - Added paddlex[ocr]>=3.0.0
2. `build_scripts/build_exe_onefile.py` - Enhanced OCR module collection
3. `build_scripts/hook-paddlex.py` - Improved PaddleX hook
4. `build_scripts/PADDLEX_OCR_FIX.md` - This documentation

---
**Fix Date**: 2025-01-XX  
**Python Version**: 3.12+ recommended  
**PaddleX Version**: 3.0.0+
