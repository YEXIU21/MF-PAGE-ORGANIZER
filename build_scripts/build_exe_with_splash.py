#!/usr/bin/env python3
"""
Enhanced EXE Builder for MF Page Organizer with Splash Screen
Builds a working standalone executable with splash screen support
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
    print("MF PAGE ORGANIZER - Enhanced EXE Builder (With Splash Screen)")
    print("=" * 70)
    print()
    
    # Paths
    build_dir = Path(__file__).parent
    root_dir = build_dir.parent
    
    # Step 1: Convert icon
    print("[1/3] Converting icon...")
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
    
    # Step 2: Install PyInstaller and download PaddleOCR models
    print("\n[2/4] Installing PyInstaller...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', '--quiet'])
    print("✓ PyInstaller ready")
    
    print("\n[3/4] Pre-downloading PaddleOCR models...")
    download_script = build_dir / 'download_paddleocr_models.py'
    result = subprocess.run([sys.executable, str(download_script)])
    if result.returncode == 0:
        print("✓ PaddleOCR models ready")
    else:
        print("⚠️  PaddleOCR models download had issues, continuing anyway")
    
    # Step 4: Build with splash screen support
    print("\n[4/4] Building executable with PaddleOCR support...")
    print("Please wait...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=PageAutomationEnhanced',
        '--onedir',
        '--windowed',
        f'--icon={icon_dst}',
        '--clean',
        '--noconfirm',
        f'--additional-hooks-dir={build_dir}',  # Use our custom hooks
        f'--splash={root_dir / "PageAutomationic.png"}',  # Use icon as splash screen
        f'--add-data={root_dir / "core"}{os.pathsep}core',
        f'--add-data={root_dir / "utils"}{os.pathsep}utils',
        # Icon files for GUI (both ICO and PNG)
        # Note: splash_screen.py NOT included - EXE uses PyInstaller image splash only
        f'--add-data={icon_dst}{os.pathsep}.',  # Add ICO for taskbar/window
        f'--add-data={root_dir / "PageAutomationic.png"}{os.pathsep}.',  # Add PNG for fallback
        # Configuration
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
        # PaddleOCR model files and dependencies
        '--collect-data=paddleocr',
        '--collect-data=paddle',
        '--collect-submodules=paddleocr',
        '--collect-submodules=paddle',
        # PaddleOCR/PaddleX models from user directory (CRITICAL for OCR to work)
        *([f'--add-data={Path.home() / ".paddlex"}{os.pathsep}.paddlex'] if (Path.home() / ".paddlex").exists() else []),
        *([f'--add-data={Path.home() / ".paddleocr"}{os.pathsep}.paddleocr'] if (Path.home() / ".paddleocr").exists() else []),
        # Include PaddleOCR's inference directory (if found)
        *([f'--add-data={models_path}{os.pathsep}paddleocr_models'] if (models_path := _get_paddleocr_models_path()) else []),
        # Main GUI entry point
        str(root_dir / 'gui_mf.py')
    ]
    
    result = subprocess.run(cmd, cwd=build_dir)
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ ENHANCED BUILD COMPLETE!")
        print("=" * 70)
        print(f"\nEXE Location: {build_dir / 'dist' / 'PageAutomationEnhanced' / 'PageAutomationEnhanced.exe'}")
        print("\nFeatures included:")
        print("• ✅ Beautiful splash screen with loading animation")
        print("• ✅ Professional window icon")
        print("• ✅ All core functionality")
        print("• ✅ Configuration file included")
        print("• ✅ No console window")
        print("\nTest it by double-clicking the EXE!")
    else:
        print("\n❌ Enhanced build failed!")

if __name__ == '__main__':
    main()
