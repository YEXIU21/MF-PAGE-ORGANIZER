# Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "PaddleOCR not available" in Standalone EXE

**Symptoms:**
```
WARNING - PaddleOCR not available, using filename fallback
```

**Root Cause:**
Multiple Python installations causing dependency mismatch. PyInstaller uses one Python, but PaddleOCR is installed in another.

**Solution:**
1. Create virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Install dependencies in .venv:
   ```bash
   .venv\Scripts\python.exe -m pip install paddleocr paddlepaddle opencv-python pillow img2pdf pikepdf
   ```

3. Build script automatically uses .venv Python

4. Rebuild EXE:
   ```bash
   python build_scripts/build_exe_onefile.py
   ```

---

### Issue 2: "PDX has already been initialized" Error

**Symptoms:**
```
RuntimeError: PDX has already been initialized. Reinitialization is not supported.
```

**Root Cause:**
PaddleOCR being imported multiple times (during diagnostics and during processing).

**Solution:**
Singleton pattern implemented in `paddle_number_detector.py`:
- First call: Initializes PaddleOCR
- Subsequent calls: Reuse existing instance
- No reinitialization occurs

---

### Issue 3: Missing `.version` File

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'paddlex/.version'
```

**Solution:**
Automatically creates `.version` file if missing (implemented in `paddle_number_detector.py`):
```python
if not os.path.exists(paddlex_version_file):
    with open(paddlex_version_file, 'w') as f:
        f.write('3.0.0')
```

---

### Issue 4: EXE Size Too Large (5.60GB)

**Symptoms:**
- Build completes but EXE is 2-5GB
- Slow startup time
- Excessive memory usage

**Root Cause:**
PyInstaller bundling unnecessary packages (PyTorch, TensorFlow, JAX).

**Solution:**
Build scripts now exclude bloat:
```python
'--exclude-module=torch',
'--exclude-module=tensorflow',
'--exclude-module=jax',
```

**Expected sizes:**
- ✅ Optimized: 500-700MB (with PaddleOCR)
- ❌ Bloated: 2-5GB (with unnecessary packages)

---

### Issue 5: Build Fails with Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'paddleocr'
```

**Solution:**
Ensure all dependencies are installed in the Python environment used for building:
```bash
# Check which Python is being used
python -c "import sys; print(sys.executable)"

# Install in that Python
python -m pip install paddleocr paddlepaddle opencv-python pillow img2pdf pikepdf
```

---

### Issue 6: Roman Numerals Not Detected

**Symptoms:**
- Pages with roman numerals (vi, vii, viii, ix, x, xi, xii) not recognized
- Falls back to filename detection

**Root Cause:**
- PaddleOCR not initialized
- Scanning positions not covering where numerals appear

**Solution:**
1. Ensure PaddleOCR is working (see Issue 1)
2. System now scans 8 positions:
   - top_left, top_center, top_right
   - middle_left, middle_right
   - bottom_left, bottom_center, bottom_right

---

### Issue 7: Slow Processing Speed

**Symptoms:**
- Processing takes too long
- System seems to scan every position

**Solution:**
AI Pattern Learning automatically optimizes:
- First 10 pages: Learns where numbers appear
- After learning: Scans most likely positions first
- Result: 4-6x faster processing

---

### Issue 8: Build Script Can't Find Files

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'icon.ico'
```

**Solution:**
Ensure you're running build script from project root:
```bash
cd "G:\Vault\Ubix\Page Automation"
python build_scripts/build_exe_onefile.py
```

---

## Diagnostic Commands

### Check Python Installation
```bash
python -c "import sys; print(sys.executable)"
```

### Check PaddleOCR Installation
```bash
python -c "import paddleocr; print('Version:', paddleocr.__version__)"
```

### Check All Dependencies
```bash
python -c "import paddleocr, paddlex, paddle, cv2, PIL, img2pdf, pikepdf; print('All packages OK!')"
```

### List Installed Packages
```bash
python -m pip list
```

### Check Virtual Environment
```bash
# Windows
.venv\Scripts\python.exe -m pip list

# Check if .venv is being used
python -c "import sys; print('Using venv:', '.venv' in sys.executable)"
```

---

## Build Verification

After building, check:

1. **File Size:**
   - ✅ 500-700MB: Correct (with PaddleOCR)
   - ⚠️ 300MB: Missing PaddleOCR
   - ❌ 2-5GB: Bloated with unnecessary packages

2. **Startup Test:**
   - Double-click EXE
   - GUI should appear in 2-3 seconds
   - Check diagnostics log for PaddleOCR initialization

3. **Processing Test:**
   - Select test folder with pages
   - Process a few pages
   - Check logs for:
     ```
     INFO - PaddleOCR initialized successfully (CPU)
     INFO - Found 'vii' in top-right corner (95% confidence)
     ```

---

## Getting Help

If issues persist:

1. **Check Logs:**
   - Located in: `logs/` folder
   - Look for ERROR and WARNING messages

2. **Enable Debug Mode:**
   - Set log level to DEBUG in config.json
   - Provides detailed diagnostic information

3. **Verify Environment:**
   - Run all diagnostic commands above
   - Ensure all packages are installed correctly

4. **Clean Rebuild:**
   ```bash
   # Delete old builds
   rmdir /s build_scripts\build
   rmdir /s build_scripts\dist
   
   # Rebuild
   python build_scripts/build_exe_onefile.py
   ```

---

## Known Limitations

1. **First Run Download:**
   - If models not bundled, PaddleOCR downloads them on first use
   - Requires internet connection
   - Takes 5-10 minutes

2. **GPU Support:**
   - Currently uses CPU only
   - GPU support requires CUDA installation

3. **Language Support:**
   - Default: English
   - Other languages require additional model downloads

---

## Performance Tips

1. **Use Fast Mode:**
   - Enable in GUI settings
   - Skips unnecessary preprocessing
   - 2-3x faster processing

2. **Bundle Models:**
   - Ensure models in `~/.paddlex/` before building
   - Enables 100% offline operation
   - No download delays

3. **Use Folder Build:**
   - Faster startup than one-file build
   - Better for development and testing
   - Command: `python build_scripts/build_exe_folder.py`
