#!/usr/bin/env python3
"""
One-File EXE Builder for MF Page Organizer
Creates a single standalone executable file with full PaddleOCR support
"""

import os
import sys
import subprocess
from pathlib import Path

def _get_paddleocr_models_path():
    """Get PaddleOCR models path for bundling"""
    try:
        import paddleocr
        import site
        
        # Try to find PaddleOCR installation directory
        paddleocr_path = Path(paddleocr.__file__).parent
        
        # Look for inference models in PaddleOCR installation
        inference_path = paddleocr_path / "inference"
        if inference_path.exists():
            return str(inference_path)
        
        # Fallback: Look in site-packages
        for site_path in site.getsitepackages():
            site_paddleocr = Path(site_path) / "paddleocr" / "inference"
            if site_paddleocr.exists():
                return str(site_paddleocr)
        
        # Fallback: Check user's .paddleocr directory
        user_models = Path.home() / ".paddleocr"
        if user_models.exists():
            return str(user_models)
        
        print("⚠️  Warning: PaddleOCR models directory not found")
        return ""
        
    except ImportError:
        print("⚠️  Warning: PaddleOCR not installed")
        return ""

def main():
    print("=" * 70)
    print("MF PAGE ORGANIZER - One-File EXE Builder")
    print("=" * 70)
    print()
    print("Creating a SINGLE executable file (larger size, portable)")
    print()
    
    # Paths
    build_dir = Path(__file__).parent
    root_dir = build_dir.parent
    
    # Step 1: Convert icon
    print("[1/4] Converting icon...")
    try:
        from PIL import Image
        icon_src = root_dir / 'PageAutomationic.png'
        icon_dst = build_dir / 'icon.ico'
        img = Image.open(icon_src)
        img.save(icon_dst, format='ICO', sizes=[(16,16), (32,32), (48,48), (256,256)])
        print("✓ Icon created")
    except Exception as e:
        print(f"✗ Icon failed: {e}")
        return
    
    # Step 2: Install PyInstaller
    print("\n[2/4] Installing PyInstaller...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', '--quiet'])
    print("✓ PyInstaller ready")
    
    # Step 3: Pre-download PaddleOCR models (optional for one-file)
    print("\n[3/4] Pre-downloading PaddleOCR models...")
    download_script = build_dir / 'download_paddleocr_models.py'
    if download_script.exists():
        result = subprocess.run([sys.executable, str(download_script)])
        if result.returncode == 0:
            print("✓ PaddleOCR models ready")
        else:
            print("⚠️  PaddleOCR models download had issues, continuing anyway")
    else:
        print("⚠️  Model downloader not found, models will download on first use")
    
    # Step 4: Build one-file executable
    print("\n[4/4] Building ONE-FILE executable...")
    print("⚠️  This may take 10-15 minutes and create a large file (~500MB)")
    print("Please wait...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=PageAutomationOneFile',
        '--onefile',  # ★ KEY DIFFERENCE: Creates single EXE file
        '--windowed',
        f'--icon={icon_dst}',
        '--clean',
        '--noconfirm',
        f'--additional-hooks-dir={build_dir}',  # Use our custom hooks
        # Add data files (embedded in the single EXE)
        f'--add-data={root_dir / "core"}{os.pathsep}core',
        f'--add-data={root_dir / "utils"}{os.pathsep}utils',
        f'--add-data={icon_dst}{os.pathsep}.',
        f'--add-data={root_dir / "PageAutomationic.png"}{os.pathsep}.',
        f'--add-data={root_dir / "config.json"}{os.pathsep}.',
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
        # PaddleOCR data - collect all model files (ENHANCED FOR STANDALONE)
        '--collect-all=paddleocr',
        '--collect-all=paddle',
        '--collect-data=paddleocr',
        '--collect-data=paddle',
        '--collect-submodules=paddleocr',
        '--collect-submodules=paddle',
        # Note: One-file builds handle models differently - they download on first use
        # This avoids the massive file size that would result from bundling all models
        # Main GUI entry point
        str(root_dir / 'gui_mf.py')
    ]
    
    result = subprocess.run(cmd, cwd=build_dir)
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ ONE-FILE BUILD COMPLETE!")
        print("=" * 70)
        
        exe_path = build_dir / 'dist' / 'PageAutomationOneFile.exe'
        print(f"\nEXE Location: {exe_path}")
        print(f"EXE Name: PageAutomationOneFile.exe")
        
        # Get file size
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"EXE Size: {size_mb:.1f} MB")
        
        print(f"\n📋 One-File Features:")
        print("  ✅ Single executable file (fully portable)")
        print("  ✅ No additional files or folders needed")
        print("  ✅ Professional window icon")
        print("  ✅ All core functionality embedded")
        print("  ✅ PaddleOCR support (models download on first use)")
        print("  ✅ Roman numeral detection (vi, vii, viii, ix, x, xi, xii)")
        print("  ✅ Multi-position page scanning")
        print("  ✅ Configuration file embedded")
        print("  ✅ No console window")
        
        print(f"\n⚡ Performance Notes:")
        print("  • First startup: ~10-15 seconds (extracts to temp)")
        print("  • Subsequent runs: ~3-5 seconds")
        print("  • PaddleOCR models: Download automatically on first OCR use")
        print("  • File size: Large (~200-500MB) but fully self-contained")
        
        print(f"\n🚀 Perfect for:")
        print("  • Sharing via email or USB")
        print("  • Running on computers without installation")
        print("  • Portable deployment")
        print("  • Users who want a single file solution")
        
        print("\n🎯 Test it by double-clicking the EXE!")
        print("=" * 70)
    else:
        print("\n❌ One-file build failed!")
        print("This may be due to:")
        print("  • Insufficient disk space")
        print("  • Antivirus interference")
        print("  • PyInstaller version issues")
        print("\nTry the regular build instead: python build_exe_with_splash.py")

if __name__ == '__main__':
    main()
