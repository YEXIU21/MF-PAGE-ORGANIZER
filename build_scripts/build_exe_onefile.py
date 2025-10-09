#!/usr/bin/env python3
"""
One-File EXE Builder - Creates single PageAutomation.exe file (OPTIMIZED)
✅ Maximum portability (single file)
✅ Full PaddleOCR support with bundled models
✅ Professional icon
✅ PREVENTS 5.60GB bloat by excluding unnecessary packages
✅ Expected size: ~500MB-1GB instead of 5.60GB
✅ Roman numeral detection (vi, vii, viii, ix, x, xi, xii)
"""

import os
import sys
import subprocess
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
    
    build_dir = Path(__file__).parent
    root_dir = build_dir.parent
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
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', '--quiet'])
    print("✓ PyInstaller ready")
    
    # Build with OPTIMIZATION to prevent 5.60GB bloat
    print("\n[5/5] Building OPTIMIZED ONE-FILE EXE...")
    print("🎯 Excluding bloated packages to prevent 5.60GB issue...")
    print("⏳ This takes 15-20 minutes - please wait...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=PageAutomationOneFile',
        '--onefile',  # ★ Single file
        '--windowed',
        f'--icon={icon_dst}',
        '--clean',
        '--noconfirm',
        f'--additional-hooks-dir={build_dir}',
        
        # ★ CRITICAL: Exclude bloated packages that cause 5.60GB builds
        '--exclude-module=torch',
        '--exclude-module=torchvision', 
        '--exclude-module=tensorflow',
        '--exclude-module=jax',
        '--exclude-module=scipy.sparse.csgraph._validation',
        '--exclude-module=scipy.spatial.ckdtree',
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
    
    # ★ MINIMAL imports only - prevent auto-discovery of bloated packages
    minimal_imports = [
        '--hidden-import=tkinter',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image', 
        '--hidden-import=PIL.ImageTk',
        '--hidden-import=cv2',
        '--hidden-import=paddleocr.paddleocr',  # Specific paddleocr only
        '--hidden-import=numpy',
        '--hidden-import=img2pdf',
        '--hidden-import=pikepdf'
    ]
    cmd.extend(minimal_imports)
    
    # ★ NO collect-all commands that cause bloat
    # REMOVED: '--collect-all=paddle' (this causes the 5.60GB issue)
    # REMOVED: '--collect-all=paddleocr' (this pulls in too much)
    
    # Only collect specific paddleocr data
    cmd.extend([
        '--collect-data=paddleocr',
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
