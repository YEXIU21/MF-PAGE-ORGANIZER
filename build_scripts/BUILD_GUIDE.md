# MF PAGE ORGANIZER - Build Guide

## Overview
This guide explains how to build standalone executables for the MF Page Organizer application with full PaddleOCR support.

## Build Options

### 1. **One-File Build** (Recommended for Distribution)
- **Script**: `build_exe_onefile.py`
- **Output**: Single `PageAutomationOneFile.exe` file
- **Size**: ~500MB-1GB
- **Pros**: Maximum portability, easy to distribute
- **Cons**: Slower startup (extracts to temp folder)

### 2. **Folder Build** (Recommended for Development)
- **Script**: `build_exe_folder.py`
- **Output**: `PageAutomation` folder with exe + support files
- **Size**: ~400MB-800MB
- **Pros**: Faster startup, easier to debug and update
- **Cons**: Multiple files to distribute

## Prerequisites

### System Requirements
- **Python**: 3.10, 3.11, or 3.12 (3.12 recommended)
- **RAM**: 8GB minimum, 16GB+ recommended for build process
- **Disk Space**: 5GB free space for build artifacts
- **OS**: Windows 10/11

### Python Dependencies
All dependencies in `requirements.txt` must be installed:
```bash
pip install -r requirements.txt
```

**Critical Dependencies:**
- `paddleocr>=2.7.0`
- `paddlex[ocr]>=3.0.0`
- `paddlepaddle>=2.5.0`
- `pyinstaller` (installed automatically by build scripts)

### Optional: Pre-download Models
For offline builds with bundled models:
```python
python -c "from paddleocr import PaddleOCR; PaddleOCR()"
```
This downloads models to `~/.paddlex/` which the build scripts will bundle.

## Building

### One-File Build
```bash
cd build_scripts
python build_exe_onefile.py
```

**Output**: `build_scripts/dist/PageAutomationOneFile.exe`

### Folder Build
```bash
cd build_scripts
python build_exe_folder.py
```

**Output**: `build_scripts/dist/PageAutomation/` folder

## Build Process Details

### What Gets Bundled

1. **Application Code**
   - `gui_mf.py` (main GUI entry point)
   - `main.py` (CLI entry point)
   - `core/` modules (all processing logic)
   - `utils/` modules (config, logging, memory)

2. **Configuration & Resources**
   - `config.json` (default settings)
   - `PageAutomationic.png` (app icon)
   - `icon.ico` (executable icon)

3. **Python Dependencies**
   - All packages from `requirements.txt`
   - **PaddleOCR + PaddleX ecosystem** (with special handling)
   - OpenCV, PIL, NumPy, SciPy
   - PDF libraries (img2pdf, PyPDF2, reportlab)

4. **PaddleOCR Models** (if pre-downloaded)
   - Text detection models
   - Text recognition models
   - Bundled as `.paddlex/` in exe

5. **Runtime Hook**
   - Patches `paddlex.utils.deps.require_extra()`
   - Bypasses dependency checks in frozen builds
   - Sets up PaddleX environment variables

### Critical Fixes Implemented

#### 1. PaddleX Dependency Checker Patch
**Problem**: PaddleX checks for `paddlex[ocr]` extras at runtime, even when deps are bundled.

**Solution**: Runtime hook patches `require_extra()` function:
```python
def patched_require_extra(package_name, extra_name, obj_name=None, alt=None, **kwargs):
    if extra_name and 'ocr' in str(extra_name).lower():
        return  # Skip check - deps are bundled
    return _original_require_extra(package_name, extra_name, obj_name=obj_name, alt=alt, **kwargs)
```

#### 2. Metadata Bundling
All paddlex[ocr] dependencies require metadata for `importlib.metadata` checks:
- `--copy-metadata=paddlex`
- `--copy-metadata=paddleocr`
- `--copy-metadata=einops, ftfy, jinja2, lxml, openpyxl, premailer, pypdfium2, regex, scikit-learn, tiktoken, tokenizers`
- Plus: numpy, opencv-contrib-python, pillow, pyyaml, scipy

#### 3. Hidden Imports
Explicit imports for:
- All `paddlex[ocr]` runtime dependencies (12 packages)
- PaddleOCR pipeline modules
- Standard library metadata modules (`importlib.metadata`, `pkg_resources`)
- Scipy submodules (`scipy.special`, `scipy.ndimage`)
- YAML, Cython modules

#### 4. Data Collection
- `--collect-data=paddleocr` (model configs)
- `--collect-data=paddlex` (pipeline configs)
- `--collect-data=yaml` (YAML templates)
- `--collect-data=sklearn` (model data)
- `--collect-all` for binary dependencies

## Testing the Build

### Quick Test
1. Run the exe: `dist/PageAutomationOneFile.exe`
2. Check console output for:
   - `[Runtime Hook] All paddlex[ocr] dependencies found ✓`
   - `[Runtime Hook] Successfully patched paddlex.utils.deps.require_extra ✓`
   - `✓ PaddleOCR: Installed`

### Full Test
1. Copy exe to a **clean PC without Python installed**
2. Run the application
3. Process a test document
4. Verify PaddleOCR initializes successfully

### Common Issues

#### "PaddleOCR failed to initialize"
- **Check**: Runtime hook output in console
- **Fix**: Ensure `--windowed` is commented out to see console errors
- **Verify**: All paddlex[ocr] dependencies are bundled

#### "ModuleNotFoundError: No module named 'einops'"
- **Cause**: Missing hidden import or metadata
- **Fix**: Add to `hidden_imports` list and `--copy-metadata`

#### "DependencyError: OCR requires additional dependencies"
- **Cause**: Runtime hook patch failed
- **Fix**: Check runtime hook signature matches paddlex version

#### Exe is too large (>2GB)
- **Cause**: Including torch, tensorflow, or other bloated packages
- **Fix**: Verify `--exclude-module` flags are working
- **Check**: Use `pyi-archive_viewer` to inspect bundled modules

## Build Time Expectations

| Build Type | Time | Size |
|------------|------|------|
| One-File | 15-20 min | ~500MB-1GB |
| Folder | 10-15 min | ~400MB-800MB |

Times are for system with:
- CPU: 8 cores
- RAM: 16GB
- SSD storage

## Distribution

### One-File Distribution
1. Simply copy `PageAutomationOneFile.exe`
2. Optionally include README or user guide
3. Compress with 7-Zip for smaller download

### Folder Distribution
1. Zip entire `PageAutomation/` folder
2. User extracts and runs `PageAutomation.exe`
3. All support files stay in same folder

## Troubleshooting

### Build Fails with "Permission Denied"
- Close any running instances of the app
- Delete `build/` and `dist/` folders manually
- Run as Administrator if needed

### "PyInstaller not found"
- Build scripts auto-install PyInstaller
- If fails, manually run: `pip install pyinstaller`

### Models Not Bundled
- Run PaddleOCR once before building: `python -c "from paddleocr import PaddleOCR; PaddleOCR()"`
- Models download to `~/.paddlex/`
- Build script copies from there

### Exe Crashes Immediately
- Run from command line to see errors
- Check for missing DLLs or dependencies
- Verify Python version compatibility

## Advanced: Customization

### Change App Name
Edit build script:
```python
'--name=YourAppName',
```

### Enable Windowed Mode (No Console)
Uncomment in build script:
```python
'--windowed',  # Uncomment to hide console
```

### Add Custom Splash Screen
```python
'--splash=splash_image.png',
```

### Optimize Size Further
- Remove unused core modules
- Exclude additional packages with `--exclude-module`
- Don't bundle models (download on first use)

## Maintenance

### Updating Dependencies
1. Update `requirements.txt`
2. Reinstall: `pip install -r requirements.txt --upgrade`
3. Test application
4. Rebuild exe

### Version Control
- Build scripts are in `build_scripts/`
- Track changes to `BUILD_GUIDE.md`
- Document fixes in `PADDLEX_OCR_FIX.md`

## Support

For build issues:
1. Check console output with `--windowed` commented out
2. Verify all dependencies installed
3. Test application in script mode first
4. Review `PADDLEX_OCR_FIX.md` for PaddleX-specific issues

## Credits

Built with:
- **PyInstaller** - Python to executable conversion
- **PaddleOCR** - OCR engine
- **PaddleX** - Model pipeline
- **Tkinter** - GUI framework
