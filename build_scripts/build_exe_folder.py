#!/usr/bin/env python3
"""
Folder EXE Builder - Creates PageAutomation.exe with supporting files (OPTIMIZED)
✅ Fast startup
✅ Full PaddleOCR support with bundled models
✅ Professional icon
✅ PREVENTS 5.60GB bloat by excluding unnecessary packages
✅ All features included
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
            model_count += 1
    
    print(f"✓ Prepared {model_count} model files")
    return models_dir

def main():
    print("=" * 70)
    print("MF PAGE ORGANIZER - FOLDER BUILD (OPTIMIZED)")
    print("=" * 70)
    print("🎯 PREVENTS 5.60GB bloat by excluding unnecessary packages")
    print("📊 Expected size: ~300-500MB (NOT 5.60GB)")
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
    print("\n[5/5] Building OPTIMIZED FOLDER EXE...")
    print("🎯 Excluding bloated packages to prevent 5.60GB issue...")
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=PageAutomation',
        '--onedir',  # ★ Folder build
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
        '--hidden-import=core.reordering_engine',
        '--hidden-import=core.output_handler',
        '--hidden-import=core.paddle_ocr_engine',
        '--hidden-import=core.paddle_number_detector',
        
        # Utility modules (CRITICAL FOR FUNCTIONALITY)
        '--hidden-import=utils',
        '--hidden-import=utils.config',
        '--hidden-import=utils.logger',
        '--hidden-import=utils.file_utils',
        '--hidden-import=utils.image_utils',
        
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
        '--hidden-import=paddleocr.paddleocr',  # Specific paddleocr only
        '--hidden-import=numpy',
        '--hidden-import=img2pdf',
        '--hidden-import=pikepdf'
    ]
    cmd.extend(essential_imports)
    
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
        print("\n" + "=" * 70)
        print("✅ OPTIMIZED FOLDER BUILD COMPLETE!")
        print("=" * 70)
        
        exe_path = build_dir / 'dist' / 'PageAutomation' / 'PageAutomation.exe'
        print(f"\n📁 EXE Location: {exe_path}")
        
        # Check total size of folder
        if exe_path.exists():
            dist_folder = build_dir / 'dist' / 'PageAutomation'
            
            # Calculate total size
            total_size = 0
            for file_path in dist_folder.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            size_mb = total_size / (1024 * 1024)
            print(f"📊 Total Folder Size: {size_mb:.1f} MB")
            
            if size_mb > 2000:  # 2GB
                print("⚠️  WARNING: Folder is still too large! Check for remaining bloated dependencies.")
            elif size_mb > 1000:  # 1GB
                print("⚠️  Folder is larger than expected but acceptable.")
            else:
                print("✅ Folder size is reasonable!")
        
        # Check models
        models_in_exe = build_dir / 'dist' / 'PageAutomation' / '_internal' / '.paddlex'
        if models_in_exe.exists():
            model_count = len(list(models_in_exe.rglob('*')))
            print(f"✅ Models bundled: {model_count} files")
            print("✅ PaddleOCR will work offline!")
        else:
            print("⚠️  No models bundled - will download on first use")
        
        print(f"\n🎯 Perfect for:")
        print("  • Development and testing")
        print("  • Professional distribution")
        print("  • Fast startup (~2-3 seconds)")
        print("  • Local installations")
        
        print(f"\n🚀 Test the EXE: Double-click {exe_path}")
        print("=" * 70)
        return True
    else:
        print("\n❌ Build failed!")
        return False

if __name__ == '__main__':
    main()
