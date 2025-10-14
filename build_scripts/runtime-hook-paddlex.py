"""
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
        
        def patched_require_extra(package_name, extra_name=None, obj_name=None, alt=None, **kwargs):
            """
            Patched version - bypasses OCR extra checks in frozen builds.
            Supports both decorator and direct call patterns.
            
            Args:
                package_name: Name of the package
                extra_name: Name of the extra (e.g., 'ocr') - optional for decorator pattern
                obj_name: Optional object name parameter
                alt: Alternative package name parameter
                **kwargs: Any additional keyword arguments
            """
            # Check if this is for OCR extra (works for both None and actual extra_name)
            if extra_name is None or (extra_name and 'ocr' in str(extra_name).lower()):
                # Return a no-op decorator or just return for direct calls
                if extra_name is None:
                    # Decorator pattern - return a pass-through decorator
                    def decorator(func):
                        return func
                    return decorator
                else:
                    # Direct call - just return
                    return
            
            # For non-OCR extras, use original function
            if extra_name is None:
                return _original_require_extra(package_name, **kwargs)
            else:
                return _original_require_extra(package_name, extra_name, obj_name=obj_name, alt=alt, **kwargs)
        
        deps.require_extra = patched_require_extra
        print("[Runtime Hook] Successfully patched paddlex.utils.deps.require_extra ✓")
        
    except Exception as e:
        print(f"[Runtime Hook] Warning: Could not patch paddlex deps: {e}")
