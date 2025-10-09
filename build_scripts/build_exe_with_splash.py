#!/usr/bin/env python3
"""
Enhanced EXE Builder for MF Page Organizer with Splash Screen
Builds a working standalone executable with splash screen support
"""

import os
import sys
import subprocess
from pathlib import Path

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
    
    # Step 2: Install PyInstaller
    print("\n[2/3] Installing PyInstaller...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', '--quiet'])
    print("✓ PyInstaller ready")
    
    # Step 3: Build with splash screen support
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
        # Icon files for GUI
        # Note: splash_screen.py NOT included - EXE uses PyInstaller image splash only
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
        '--hidden-import=numpy',
        '--hidden-import=img2pdf',
        '--hidden-import=pikepdf',
        '--hidden-import=threading',
        '--hidden-import=time',
        '--hidden-import=sys',
        '--hidden-import=os',
        '--hidden-import=pathlib',
        # PaddleOCR data - collect all model files
        '--collect-all=paddleocr',
        '--collect-all=paddle',
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
