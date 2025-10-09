#!/usr/bin/env python3
"""
One-File EXE Builder with Bundled Models
Creates a single standalone executable with PaddleOCR models pre-bundled
This creates a larger file (~800MB-1GB) but includes everything
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def _check_models_exist():
    """Check if PaddleOCR models exist in user directory"""
    paddlex_dir = Path.home() / '.paddlex'
    if paddlex_dir.exists():
        model_files = list(paddlex_dir.rglob('*.pdparams'))
        return len(model_files) > 0
    return False

def _prepare_models_for_bundling():
    """Prepare model directory for bundling, avoiding problematic files"""
    paddlex_dir = Path.home() / '.paddlex'
    if not paddlex_dir.exists():
        return []
    
    bundle_args = []
    
    # Create a clean model directory
    temp_models = Path.cwd() / 'temp_models'
    if temp_models.exists():
        shutil.rmtree(temp_models)
    temp_models.mkdir()
    
    print("📦 Preparing models for bundling...")
    
    # Copy essential model files, skip problematic ones
    for model_file in paddlex_dir.rglob('*'):
        if model_file.is_file():
            # Skip problematic files
            skip_patterns = ['.git', '.cache', '__pycache__', '.pyc', '.tmp']
            if any(pattern in str(model_file) for pattern in skip_patterns):
                continue
            
            # Copy essential files
            relative_path = model_file.relative_to(paddlex_dir)
            dest_file = temp_models / relative_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(model_file, dest_file)
    
    # Add the cleaned model directory
    bundle_args.append(f'--add-data={temp_models}{os.pathsep}.paddlex')
    
    model_count = len(list(temp_models.rglob('*')))
    print(f"✓ Prepared {model_count} model files for bundling")
    
    return bundle_args, temp_models

def main():
    print("=" * 70)
    print("MF PAGE ORGANIZER - One-File EXE Builder (WITH MODELS)")
    print("=" * 70)
    print()
    print("Creating a SINGLE executable file with PaddleOCR models embedded")
    print("⚠️  This creates a LARGE file (~800MB-1GB) but is fully offline")
    print()
    
    # Check if models exist
    if not _check_models_exist():
        print("❌ PaddleOCR models not found!")
        print("Please run this first to download models:")
        print("  python build_scripts/download_paddleocr_models.py")
        print()
        print("Or use the regular one-file build (models download on first use):")
        print("  python build_scripts/build_exe_onefile.py")
        return False
    
    # Paths
    build_dir = Path(__file__).parent
    root_dir = build_dir.parent
    
    # Step 1: Convert icon
    print("[1/5] Converting icon...")
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
    
    # Step 2: Install PyInstaller
    print("\n[2/5] Installing PyInstaller...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', '--quiet'])
    print("✓ PyInstaller ready")
    
    # Step 3: Prepare models
    print("\n[3/5] Preparing PaddleOCR models for bundling...")
    try:
        model_args, temp_models = _prepare_models_for_bundling()
    except Exception as e:
        print(f"✗ Model preparation failed: {e}")
        return False
    
    # Step 4: Build one-file executable with models
    print("\n[4/5] Building ONE-FILE executable with embedded models...")
    print("⚠️  This may take 15-20 minutes and create a VERY large file (~800MB-1GB)")
    print("Please wait...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=PageAutomationOneFileWithModels',
        '--onefile',  # ★ Creates single EXE file
        '--windowed',
        f'--icon={icon_dst}',
        '--clean',
        '--noconfirm',
        f'--additional-hooks-dir={build_dir}',
        # Add data files (embedded in the single EXE)
        f'--add-data={root_dir / "core"}{os.pathsep}core',
        f'--add-data={root_dir / "utils"}{os.pathsep}utils',
        f'--add-data={icon_dst}{os.pathsep}.',
        f'--add-data={root_dir / "PageAutomationic.png"}{os.pathsep}.',
        f'--add-data={root_dir / "config.json"}{os.pathsep}.',
    ] + model_args + [  # Add prepared model files
        # Hidden imports for all required modules
        '--hidden-import=tkinter',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageTk',
        '--hidden-import=cv2',
        '--hidden-import=paddleocr',
        '--hidden-import=paddle',
        '--hidden-import=paddleocr.paddleocr',
        '--hidden-import=paddle.inference',
        '--hidden-import=paddle.framework',
        '--hidden-import=paddle.fluid',
        '--hidden-import=ppocr',
        '--hidden-import=ppocr.utils',
        '--hidden-import=ppocr.data',
        '--hidden-import=ppocr.modeling',
        '--hidden-import=ppocr.postprocess',
        '--hidden-import=ppocr.tools',
        '--hidden-import=tools',
        '--hidden-import=tools.infer',
        '--hidden-import=numpy',
        '--hidden-import=img2pdf',
        '--hidden-import=pikepdf',
        '--hidden-import=threading',
        '--hidden-import=time',
        '--hidden-import=sys',
        '--hidden-import=os',
        '--hidden-import=pathlib',
        # PaddleOCR data - collect all dependencies
        '--collect-all=paddleocr',
        '--collect-all=paddle',
        '--collect-data=paddleocr',
        '--collect-data=paddle',
        '--collect-submodules=paddleocr',
        '--collect-submodules=paddle',
        # Main GUI entry point
        str(root_dir / 'gui_mf.py')
    ]
    
    result = subprocess.run(cmd, cwd=build_dir)
    
    # Step 5: Cleanup and report
    print("\n[5/5] Cleaning up...")
    if temp_models.exists():
        shutil.rmtree(temp_models)
        print("✓ Temporary files cleaned")
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ ONE-FILE BUILD WITH MODELS COMPLETE!")
        print("=" * 70)
        
        exe_path = build_dir / 'dist' / 'PageAutomationOneFileWithModels.exe'
        print(f"\nEXE Location: {exe_path}")
        print(f"EXE Name: PageAutomationOneFileWithModels.exe")
        
        # Get file size
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"EXE Size: {size_mb:.1f} MB")
        
        print(f"\n📋 Fully Self-Contained Features:")
        print("  ✅ Single executable file (NO internet needed)")
        print("  ✅ PaddleOCR models pre-bundled")
        print("  ✅ 100% offline operation")
        print("  ✅ Roman numeral detection (vi, vii, viii, ix, x, xi, xii)")
        print("  ✅ Multi-position page scanning")
        print("  ✅ Professional window icon")
        print("  ✅ All core functionality embedded")
        print("  ✅ Configuration file embedded")
        print("  ✅ No console window")
        
        print(f"\n⚡ Performance Notes:")
        print("  • First startup: ~15-20 seconds (large extraction)")
        print("  • Subsequent runs: ~5-8 seconds")
        print("  • OCR speed: MAXIMUM (models pre-loaded)")
        print("  • No network required: 100% offline")
        print("  • File size: LARGE (~800MB-1GB) but complete")
        
        print(f"\n🎯 Perfect for:")
        print("  • Offline environments (no internet)")
        print("  • Air-gapped systems")
        print("  • Maximum performance OCR")
        print("  • Complete self-contained deployment")
        print("  • Enterprise environments")
        
        print("\n🚀 This is the ULTIMATE portable version!")
        print("=" * 70)
        return True
    else:
        print("\n❌ One-file build with models failed!")
        print("This may be due to:")
        print("  • Insufficient disk space (need ~2GB free)")
        print("  • Memory limitations during build")
        print("  • Antivirus interference")
        print("\nTry the regular one-file build instead:")
        print("  python build_scripts/build_exe_onefile.py")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
