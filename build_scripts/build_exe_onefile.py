#!/usr/bin/env python3
"""
ONE-FILE EXE BUILDER - MF PAGE ORGANIZER
Creates standalone PageAutomationOneFile.exe with all dependencies bundled
✅ Full PaddleOCR + PaddleX[ocr] support
✅ Runtime hook to bypass dependency checks  
✅ Professional icon and metadata
✅ Optimized size (~500MB-1GB)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_runtime_hook():
    """Create runtime hook to patch paddlex dependency checker"""
    hook_content = '''"""
Runtime hook for PaddleX - Patches dependency checker for frozen builds
"""
import sys

if getattr(sys, 'frozen', False):
    import os
    
    # Set PaddleX home to bundled models
    base_path = sys._MEIPASS
    paddlex_home = os.path.join(base_path, '.paddlex')
    if os.path.exists(paddlex_home):
        os.environ['PADDLEX_HOME'] = paddlex_home
        print(f"[Runtime Hook] Set PADDLEX_HOME to: {paddlex_home}")
    
    # Create .version file if missing
    version_file = os.path.join(paddlex_home, '.version')
    if not os.path.exists(version_file):
        try:
            os.makedirs(paddlex_home, exist_ok=True)
            with open(version_file, 'w') as f:
                f.write('3.0.0')
            print(f"[Runtime Hook] Created .version file")
        except Exception as e:
            print(f"[Runtime Hook] Warning: Could not create .version file: {e}")
    
    # Pre-check paddlex[ocr] dependencies
    print("[Runtime Hook] Pre-checking paddlex[ocr] dependencies...")
    required_deps = [
        'einops', 'ftfy', 'imagesize', 'jinja2', 'lxml',
        'openpyxl', 'premailer', 'pypdfium2', 'regex',
        'sklearn', 'tiktoken', 'tokenizers'
    ]
    
    missing = []
    for dep in required_deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"[Runtime Hook] WARNING: Missing dependencies: {', '.join(missing)}")
    else:
        print("[Runtime Hook] All paddlex[ocr] dependencies found ✓")
    
    # ★ CRITICAL: Patch paddlex.utils.deps.require_extra to bypass checks
    print("[Runtime Hook] Patching paddlex.utils.deps.require_extra...")
    try:
        from paddlex.utils import deps
        
        _original_require_extra = deps.require_extra
        
        def patched_require_extra(package_name, extra_name, obj_name=None, alt=None, **kwargs):
            """Patched version - bypasses OCR extra checks in frozen builds"""
            if extra_name and 'ocr' in str(extra_name).lower():
                return  # Skip check - deps are bundled
            return _original_require_extra(package_name, extra_name, obj_name=obj_name, alt=alt, **kwargs)
        
        deps.require_extra = patched_require_extra
        print("[Runtime Hook] Successfully patched paddlex.utils.deps.require_extra ✓")
        
    except Exception as e:
        print(f"[Runtime Hook] Warning: Could not patch paddlex deps: {e}")
'''
    
    build_dir = Path(__file__).parent
    hook_file = build_dir / 'runtime-hook-paddlex.py'
    hook_file.write_text(hook_content)
    print(f"✓ Created runtime hook: {hook_file}")
    return hook_file

def prepare_models():
    """Copy PaddleOCR models for bundling"""
    print("📦 Preparing PaddleOCR models...")
    
    paddlex_dir = Path.home() / '.paddlex'
    if not paddlex_dir.exists():
        print("⚠️  No models found. They will download on first use.")
        return None
    
    build_dir = Path(__file__).parent
    models_dir = build_dir / 'paddleocr_models'
    
    if models_dir.exists():
        shutil.rmtree(models_dir)
    models_dir.mkdir()
    
    # Copy model files
    model_count = 0
    for src_file in paddlex_dir.rglob('*'):
        if src_file.is_file():
            # Skip cache/git files
            if any(p in str(src_file) for p in ['.git', '.cache', '__pycache__', '.tmp', '.pyc']):
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
    print("MF PAGE ORGANIZER - ONE-FILE BUILD")
    print("=" * 70)
    print("📦 Creating standalone executable with ALL dependencies bundled")
    print("🎯 Expected size: ~500MB-1GB")
    print()
    
    build_dir = Path(__file__).parent
    root_dir = build_dir.parent
    
    # Use system Python (not venv)
    python_exe = sys.executable
    print(f"🐍 Python: {python_exe}")
    
    # Clean old builds
    print("\n[1/6] Cleaning old builds...")
    for cleanup in ['build', 'dist']:
        cleanup_path = build_dir / cleanup
        if cleanup_path.exists():
            shutil.rmtree(cleanup_path)
    print("✓ Clean")
    
    # Create icon
    print("\n[2/6] Creating icon...")
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
    
    # Create runtime hook
    print("\n[3/6] Creating runtime hook...")
    runtime_hook = create_runtime_hook()
    
    # Prepare models
    print("\n[4/6] Preparing models...")
    models_dir = prepare_models()
    
    # Install PyInstaller
    print("\n[5/6] Installing PyInstaller...")
    subprocess.run([python_exe, '-m', 'pip', 'install', 'pyinstaller', '--quiet'])
    print("✓ PyInstaller ready")
    
    # Build ONE-FILE EXE
    print("\n[6/6] Building ONE-FILE EXE...")
    print("⏳ This takes 15-20 minutes...")
    
    cmd = [
        python_exe, '-m', 'PyInstaller',
        '--name=PageAutomationOneFile',
        '--onefile',  # ★ Single file
        # '--windowed',  # Commented out for debugging
        f'--icon={icon_dst}',
        '--clean',
        '--noconfirm',
        '--noupx',
        '--runtime-tmpdir=.',
        f'--runtime-hook={runtime_hook}',  # ★ CRITICAL: Patch paddlex deps
        
        # Exclude bloated packages
        '--exclude-module=torch',
        '--exclude-module=torchvision',
        '--exclude-module=tensorflow',
        '--exclude-module=jax',
        
        # Data files
        f'--add-data={root_dir / "core"}{os.pathsep}core',
        f'--add-data={root_dir / "utils"}{os.pathsep}utils',
        f'--add-data={root_dir / "config.json"}{os.pathsep}.',
        f'--add-data={root_dir / "PageAutomationic.png"}{os.pathsep}.',
    ]
    
    # Add models if available
    if models_dir and models_dir.exists():
        cmd.append(f'--add-data={models_dir}{os.pathsep}.paddlex')
    
    # ★ COMPLETE hidden imports
    hidden_imports = [
        # GUI
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
        
        # Core modules
        'core', 'core.input_handler', 'core.preprocessor', 'core.ocr_engine',
        'core.numbering_system', 'core.output_manager', 'core.paddle_ocr_engine',
        'core.paddle_number_detector', 'core.ai_learning', 'core.ai_pattern_learning',
        'core.blank_page_detector', 'core.confidence_system', 'core.content_analyzer',
        'core.crop_validator', 'core.interactive_cropper', 'core.performance_optimizer',
        'core.smart_cache',
        
        # Utils
        'utils', 'utils.config', 'utils.logger', 'utils.memory',
        
        # Standard library
        'threading', 'tempfile', 'shutil', 'pathlib', 'json',
        'importlib.metadata', 'importlib.resources', 'pkg_resources',
        
        # Image processing
        'PIL', 'PIL.Image', 'PIL.ImageTk', 'cv2',
        
        # OCR and PDF
        'paddleocr', 'paddleocr.paddleocr', 'paddleocr.tools', 'paddleocr.tools.infer',
        'paddleocr._pipelines', 'paddleocr._pipelines.base', 'paddleocr._pipelines.ocr',
        'paddlex', 'paddlex.inference', 'paddlex.inference.pipelines',
        'paddlex.utils', 'paddlex.utils.deps', 'paddlex.inference.utils',
        'paddle', 'paddle.inference',
        'numpy', 'img2pdf', 'pikepdf',
        
        # ★ CRITICAL: paddlex[ocr] runtime dependencies
        'einops', 'ftfy', 'imagesize', 'jinja2', 'lxml', 'openpyxl',
        'premailer', 'pypdfium2', 'regex', 'sklearn', 'tiktoken', 'tokenizers',
        
        # Additional ecosystem
        'yaml', 'yaml.loader', 'yaml.dumper',
        'scipy', 'scipy.special', 'scipy.ndimage',
        'Cython', 'Cython.Compiler', 'Cython.Build',
    ]
    
    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')
    
    # ★ Collect data/binaries
    cmd.extend([
        '--collect-data=paddleocr',
        '--collect-data=paddlex',
        '--collect-data=paddle',
        '--collect-data=Cython',
        '--collect-data=yaml',
        '--collect-data=sklearn',
        '--collect-submodules=paddleocr',
        '--collect-submodules=paddlex',
        '--collect-all=einops',
        '--collect-all=ftfy',
        '--collect-all=lxml',
        '--collect-all=openpyxl',
        '--collect-all=pypdfium2',
        '--collect-all=tiktoken',
        '--collect-all=tokenizers',
        
        # ★ CRITICAL: Copy metadata for runtime checks
        '--copy-metadata=paddlex',
        '--copy-metadata=paddleocr',
        '--copy-metadata=paddlepaddle',
        '--copy-metadata=einops',
        '--copy-metadata=ftfy',
        '--copy-metadata=imagesize',
        '--copy-metadata=jinja2',
        '--copy-metadata=lxml',
        '--copy-metadata=openpyxl',
        '--copy-metadata=premailer',
        '--copy-metadata=pypdfium2',
        '--copy-metadata=regex',
        '--copy-metadata=scikit-learn',
        '--copy-metadata=tiktoken',
        '--copy-metadata=tokenizers',
        '--copy-metadata=numpy',
        '--copy-metadata=opencv-contrib-python',
        '--copy-metadata=pillow',
        '--copy-metadata=pyyaml',
        '--copy-metadata=scipy',
        
        str(root_dir / 'gui_mf.py')
    ])
    
    result = subprocess.run(cmd, cwd=build_dir)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ ONE-FILE BUILD COMPLETE!")
        print("=" * 60)
        
        exe_path = build_dir / 'dist' / 'PageAutomationOneFile.exe'
        print(f"\n📄 EXE: {exe_path}")
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📊 Size: {size_mb:.1f} MB")
            
            if size_mb > 2000:
                print("⚠️  File is too large! Check for bloated dependencies.")
            elif size_mb > 1000:
                print("⚠️  File is larger than expected but acceptable.")
            else:
                print("✅ File size is reasonable!")
            
            if models_dir and models_dir.exists():
                print("✅ Models bundled - 100% offline operation")
            else:
                print("⚠️  No models bundled - will download on first use")
        
        print(f"\n🚀 Test: Double-click {exe_path}")
        print("=" * 60)
        return True
    else:
        print("\n❌ Build failed!")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
