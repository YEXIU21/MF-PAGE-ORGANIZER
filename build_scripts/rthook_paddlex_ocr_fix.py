"""
PyInstaller Runtime Hook to bypass paddlex[ocr] dependency checks
This patches the require_extra decorator to always pass in frozen executables
"""
import sys

if getattr(sys, 'frozen', False):
    # We're running in a PyInstaller bundle - patch the dependency check
    try:
        import paddlex.utils.deps as deps
        
        # Store original require_extra
        _original_require_extra = deps.require_extra
        
        def patched_require_extra(extra_name):
            """
            Patched version of require_extra that skips checks in frozen executables
            since all dependencies are bundled
            """
            def decorator(func_or_cls):
                # In frozen mode, assume all extras are available
                # since we bundle everything with PyInstaller
                return func_or_cls
            return decorator
        
        # Replace the require_extra function
        deps.require_extra = patched_require_extra
        
        print("✅ PaddleX OCR dependency check bypassed for frozen executable")
        
    except Exception as e:
        print(f"⚠️  Could not patch paddlex.utils.deps: {e}")
        pass
