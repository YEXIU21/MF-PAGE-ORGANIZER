#!/usr/bin/env python3
"""
Simple and Reliable EXE Builder for MF Page Organizer (Fast Startup)
Builds a working standalone executable without splash screen for faster startup
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 70)
    print("MF PAGE ORGANIZER - Fast Startup EXE Builder")
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
    
    # Step 3: Build
    print("\n[3/3] Building EXE (5-10 minutes)...")
    print("Please wait...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=PageAutomation',
        '--onedir',  # Create folder with EXE
        '--windowed',  # No console
        f'--icon={icon_dst}',
        '--clean',
        '--noconfirm',
        f'--add-data={root_dir / "core"}{os.pathsep}core',
        f'--add-data={root_dir / "utils"}{os.pathsep}utils',
        f'--add-data={root_dir / "splash_screen.py"}{os.pathsep}.',
        f'--add-data={icon_dst}{os.pathsep}.',  # Add icon to bundle
        f'--add-data={root_dir / "PageAutomationic.png"}{os.pathsep}.',  # Add PNG for fallback
        f'--add-data={root_dir / "config.json"}{os.pathsep}.',  # Add config file
        '--hidden-import=tkinter',
        '--hidden-import=PIL',
        '--hidden-import=PIL.ImageTk',
        '--hidden-import=cv2',
        '--hidden-import=paddleocr',
        '--hidden-import=paddle',
        '--hidden-import=numpy',
        '--hidden-import=img2pdf',
        '--hidden-import=pikepdf',
        str(root_dir / 'gui_mf.py')
    ]
    
    result = subprocess.run(cmd, cwd=build_dir)
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ FAST STARTUP BUILD COMPLETE!")
        print("=" * 70)
        print(f"\nEXE Location: {build_dir / 'dist' / 'PageAutomation' / 'PageAutomation.exe'}")
        print("\nFeatures included:")
        print("• ✅ Fast startup (no splash screen)")
        print("• ✅ Professional window icon")
        print("• ✅ All core functionality")
        print("• ✅ Configuration file included")
        print("• ✅ No console window")
        print("\nTest it by double-clicking the EXE!")
    else:
        print("\n❌ Fast startup build failed!")

if __name__ == '__main__':
    main()
