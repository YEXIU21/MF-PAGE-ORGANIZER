#!/usr/bin/env python3
"""
One-File EXE Builder - Creates single PageAutomation.exe file (OPTIMIZED)
✅ Maximum portability (single file)
✅ Full PaddleOCR 3.2+ support with PaddleX[ocr] dependencies
✅ Professional icon
✅ PREVENTS 5.60GB bloat by excluding unnecessary packages
✅ Expected size: ~500MB-1GB instead of 5.60GB
✅ Roman numeral detection (vi, vii, viii, ix, x, xi, xii)
✅ Python 3.12 compatible

REQUIREMENTS:
- Python 3.12+ recommended
- paddlex[ocr]>=3.0.0 (for PaddleOCR 3.2+ pipeline support)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def prepare_models():
    """Copy PaddleOCR models for bundling"""
    print("📦 Preparing PaddleOCR models...")
    
    paddlex_dir = Path.home() / '.paddlex'
    if not paddlex_dir.exists():
        print("⚠️  No PaddleOCR models found. They will download on first use.")
        return None
    
    build_dir = Path(__file__).parent
    models_dir = build_dir / 'paddleocr_models'
    
    if models_dir.exists():
        shutil.rmtree(models_dir)
    models_dir.mkdir()
    
    # Copy model files (skip problematic cache/git files)
    model_count = 0
    for src_file in paddlex_dir.rglob('*'):
        if src_file.is_file():
            skip_patterns = ['.git', '.cache', '__pycache__', '.tmp', '.pyc']
            if any(pattern in str(src_file) for pattern in skip_patterns):
                continue
            
            rel_path = src_file.relative_to(paddlex_dir)
            dest_file = models_dir / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
    
    print(f"✓ Prepared {model_count} model files")
    return models_dir

def main():
    print("=" * 70)
    print("MF PAGE ORGANIZER - ONE-FILE BUILD (OPTIMIZED)")
    print("=" * 70)
    print("🎯 PREventS 5.60GB bloat by excluding unnecessary packages")
    print("📊 Expected size: ~500MB-1GB (NOT 5.60GB)")
    print("✅ Maximum portability - run from anywhere")
    print()
    
    # Check Python version (Python 3.12+ recommended)
    py_version = sys.version_info
    print(f"🐍 Python Version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version < (3, 12):
        print("⚠️  WARNING: Python 3.12+ is recommended for best compatibility")
        print("   Current version may work but is not tested")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("Build cancelled. Please use Python 3.12+")
            return False
    else:
        print("✅ Python version is compatible")
    print()
    
    build_dir = Path(__file__).parent
    root_dir = build_dir.parent
    
    # ★ CRITICAL: Use .venv Python if available (ensures correct dependencies)
    venv_python = root_dir / '.venv' / 'Scripts' / 'python.exe'
    if venv_python.exists():
        python_exe = str(venv_python)
        print(f"✅ Using virtual environment: {python_exe}")
    else:
        python_exe = sys.executable
        print(f"⚠️  Using system Python: {python_exe}")
        print("   Recommendation: Create .venv for better dependency management")
    # Clean old builds
    print("[1/5] Cleaning old builds...")
    for cleanup in ['build', 'dist']:
        cleanup_path = build_dir / cleanup
        if cleanup_path.exists():
            shutil.rmtree(cleanup_path)
    print("✓ Clean")
    
    # Create icon
    print("\n[2/5] Creating icon...")
    try:
        from PIL import Image
        icon_src = root_dir / 'PageAutomationic.png'
        icon_dst = build_dir / 'icon.ico'
        img = Image.open(icon_src)
        img.save(icon_dst, format='ICO', sizes=[(16,16), (32,32), (48,48), (256,256)])
        print("✓ Icon created")
    except Exception as e:
        print(f"✗ Icon failed: {e}")
        return False
    
    # Prepare models
    print("\n[3/5] Preparing models...")
    models_dir = prepare_models()
    
    # Install PyInstaller
    print("\n[4/5] Installing PyInstaller...")
    subprocess.run([python_exe, '-m', 'pip', 'install', 'pyinstaller', '--quiet'])
    print("✓ PyInstaller ready")
    
    # Build with OPTIMIZATION to prevent 5.60GB bloat
    print("\n[5/5] Building OPTIMIZED ONE-FILE EXE...")
    print("🎯 Excluding bloated packages to prevent 5.60GB issue...")
    print("⏳ This takes 15-20 minutes - please wait...")
    
    cmd = [
        python_exe, '-m', 'PyInstaller',
        '--name=PageAutomationOneFile',
        '--onefile',  # ★ Single file
        '--windowed',
        f'--icon={icon_dst}',
        '--clean',
        '--noconfirm',
        '--noupx',  # ★ CRITICAL: Disable UPX to prevent interpreter corruption
        '--runtime-tmpdir=.',  # ★ CRITICAL: Use current dir for temp extraction
        f'--additional-hooks-dir={build_dir}',
        
        # ★ CRITICAL: Exclude bloated packages that cause 5.60GB builds
        '--exclude-module=torch',
        '--exclude-module=torchvision', 
        '--exclude-module=tensorflow',
        '--exclude-module=jax',
        # Note: Be careful with scipy exclusions - only exclude specific submodules
        '--exclude-module=torch.distributed',
        '--exclude-module=torch.nn',
        '--exclude-module=torch.optim',
        '--exclude-module=torch.autograd',
        '--exclude-module=torch.cuda',
        '--exclude-module=torch.backends',
        
        # Data files
        f'--add-data={root_dir / "core"}{os.pathsep}core',
        f'--add-data={root_dir / "utils"}{os.pathsep}utils',
        f'--add-data={root_dir / "config.json"}{os.pathsep}.',
        f'--add-data={root_dir / "PageAutomationic.png"}{os.pathsep}.',
    ]
    
    # Add models if available
    if models_dir and models_dir.exists():
        cmd.append(f'--add-data={models_dir}{os.pathsep}.paddlex')
    
    # ★ COMPLETE imports for GUI functionality
    essential_imports = [
        # GUI and UI
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=tkinter.messagebox',
        
        # Core application modules (CRITICAL FOR FUNCTIONALITY)
        '--hidden-import=core',
        '--hidden-import=core.input_handler',
        '--hidden-import=core.preprocessor', 
        '--hidden-import=core.ocr_engine',
        '--hidden-import=core.numbering_system',
        '--hidden-import=core.output_manager',
        '--hidden-import=core.paddle_ocr_engine',
        '--hidden-import=core.paddle_number_detector',
        '--hidden-import=core.ai_learning',
        '--hidden-import=core.ai_pattern_learning',
        '--hidden-import=core.blank_page_detector',
        '--hidden-import=core.confidence_system',
        '--hidden-import=core.content_analyzer',
        '--hidden-import=core.crop_validator',
        '--hidden-import=core.interactive_cropper',
        '--hidden-import=core.performance_optimizer',
        '--hidden-import=core.smart_cache',
        
        # Utility modules (CRITICAL FOR FUNCTIONALITY)
        '--hidden-import=utils',
        '--hidden-import=utils.config',
        '--hidden-import=utils.logger',
        '--hidden-import=utils.memory',
        
        # Standard library
        '--hidden-import=threading',
        '--hidden-import=tempfile',
        '--hidden-import=shutil',
        '--hidden-import=pathlib',
        '--hidden-import=json',
        
        # Image processing
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image', 
        '--hidden-import=PIL.ImageTk',
        '--hidden-import=cv2',
        
        # OCR and PDF
        '--hidden-import=paddleocr',
        '--hidden-import=paddleocr.paddleocr',
        '--hidden-import=paddleocr.tools',
        '--hidden-import=paddleocr.tools.infer',
        '--hidden-import=paddleocr._pipelines',
        '--hidden-import=paddleocr._pipelines.base',
        '--hidden-import=paddleocr._pipelines.ocr',
        '--hidden-import=paddlex',
        '--hidden-import=paddlex.inference',
        '--hidden-import=paddlex.inference.pipelines',
        '--hidden-import=paddlex.utils',
        '--hidden-import=paddlex.utils.deps',
        '--hidden-import=paddle',
        '--hidden-import=paddle.inference',
        '--hidden-import=numpy',
        '--hidden-import=img2pdf',
        '--hidden-import=pikepdf'
    ]
    cmd.extend(essential_imports)
    
    # ★ NO collect-all commands that cause bloat
    # REMOVED: '--collect-all=paddle' (this causes the 5.60GB issue)
    # REMOVED: '--collect-all=paddleocr' (this pulls in too much)
    
    # ★ CRITICAL: Collect data files for paddle ecosystem
    cmd.extend([
        '--collect-data=paddleocr',
        '--collect-data=paddlex',
        '--collect-data=paddle',
        '--collect-submodules=paddleocr',
        '--collect-submodules=paddlex',
        str(root_dir / 'gui_mf.py')
    ])
    
    result = subprocess.run(cmd, cwd=build_dir)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ ONE-FILE BUILD COMPLETE!")
        print("=" * 60)
        
        exe_path = build_dir / 'dist' / 'PageAutomationOneFile.exe'
        print(f"\n📄 Single EXE: {exe_path}")
        
        # Check file size with bloat warning
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📊 File Size: {size_mb:.1f} MB")
            
            if size_mb > 2000:  # 2GB
                print("⚠️  WARNING: File is still too large! Check for remaining bloated dependencies.")
            elif size_mb > 1000:  # 1GB
                print("⚠️  File is larger than expected but acceptable.")
            else:
                print("✅ File size is reasonable!")
            
            if models_dir and models_dir.exists():
                print("✅ Models bundled - 100% offline operation")
            else:
                print("⚠️  No models bundled - will download on first use")
        
        print(f"\n🎯 Perfect for:")
        print("  • Email distribution")
        print("  • USB deployment") 
        print("  • Cloud sharing")
        print("  • Portable operation")
        
        print(f"\n🚀 Test the EXE: Double-click {exe_path}")
        print("=" * 60)
        return True
    else:
        print("\n❌ Build failed!")
        return False

if __name__ == '__main__':
    main()
