"""
Build EXE with Custom Splash Screen (Tkinter Progress Bar)
Shows custom splash_screen.py with loading messages and progress bar
"""

import subprocess
import sys
import os
from pathlib import Path
from PIL import Image

def main():
    print("=" * 70)
    print("BUILDING EXE WITH CUSTOM SPLASH (Tkinter)")
    print("=" * 70)
    
    # Paths
    build_dir = Path(__file__).parent
    root_dir = build_dir.parent
    
    # Step 1: Convert PNG to ICO
    print("\n[1/3] Converting icon...")
    try:
        png_path = root_dir / 'PageAutomationic.png'
        icon_dst = build_dir / 'icon.ico'
        
        # Create multi-size ICO (proper Windows 11 support)
        img = Image.open(png_path)
        img.save(icon_dst, format='ICO', sizes=[(16,16), (32,32), (48,48), (256,256)])
        print("✓ Icon converted with multiple sizes")
    except Exception as e:
        print(f"✗ Icon failed: {e}")
        return
    
    # Step 2: Install PyInstaller
    print("\n[2/3] Installing PyInstaller...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', '--quiet'])
    print("✓ PyInstaller ready")
    
    # Step 3: Build with custom splash support
    print("\n[3/3] Building EXE with custom splash...")
    print("Please wait...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=PageAutomationCustom',
        '--onedir',
        '--windowed',
        f'--icon={icon_dst}',
        '--clean',
        '--noconfirm',
        f'--additional-hooks-dir={build_dir}',  # Use our custom hooks
        # NO --splash parameter - we use custom Python splash instead
        f'--add-data={root_dir / "core"}{os.pathsep}core',
        f'--add-data={root_dir / "utils"}{os.pathsep}utils',
        # Include custom splash screen
        f'--add-data={root_dir / "splash_screen.py"}{os.pathsep}.',
        # Icon files for GUI
        f'--add-data={root_dir / "PageAutomationic.png"}{os.pathsep}.',
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
        # PaddleOCR/PaddleX models from user directory (CRITICAL for OCR)
        f'--add-data={Path.home() / ".paddlex"}{os.pathsep}.paddlex',
        # Main GUI entry point
        str(root_dir / 'gui_mf.py')
    ]
    
    result = subprocess.run(cmd, cwd=build_dir)
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ CUSTOM SPLASH BUILD COMPLETE!")
        print("=" * 70)
        print(f"\nEXE Location: {build_dir / 'dist' / 'PageAutomationCustom' / 'PageAutomationCustom.exe'}")
        print(f"EXE Name: PageAutomationCustom.exe")
        print("\n📋 Features:")
        print("  ✓ Custom Tkinter splash with progress bar")
        print("  ✓ Loading status messages")
        print("  ✓ Professional animated progress")
        print("  ✓ All core functionality included")
        print("  ✓ PaddleOCR models bundled")
        print("  ✓ Multi-threading support")
        print("  ✓ img2pdf optimization (5.8x faster)")
        print("\n🎨 Splash Screen: Custom Tkinter (splash_screen.py)")
        print("   - Shows: Loading messages with progress bar")
        print("   - Animation: Smooth progress bar animation")
        print("   - Messages: 'Loading OCR engine...', 'Initializing AI...', etc.")
        print("\n💡 Note: This uses the custom Tkinter splash in EXE mode")
        print("   Unlike build_exe_with_splash.py which uses image splash")
        print("\n" + "=" * 70)
    else:
        print("\n❌ Custom splash build failed!")
        print("Check error messages above.")
    
    return result.returncode

if __name__ == '__main__':
    exit(main())
