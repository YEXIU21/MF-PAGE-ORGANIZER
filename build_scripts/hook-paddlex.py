"""
PyInstaller hook for PaddleX with OCR support
Ensures .version file, OCR dependencies, and other PaddleX resources are bundled
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files from paddlex package
datas = collect_data_files('paddlex')

# Collect all submodules including OCR-specific ones
hiddenimports = collect_submodules('paddlex')

# Explicitly add OCR-critical modules
ocr_modules = [
    'paddlex.inference',
    'paddlex.inference.pipelines',
    'paddlex.inference.pipelines.ocr',
    'paddlex.utils',
    'paddlex.utils.deps',
    'paddlex.repo_manager',
]

for module in ocr_modules:
    if module not in hiddenimports:
        hiddenimports.append(module)

# Explicitly include .version file and other metadata
import os
try:
    import paddlex
    paddlex_dir = os.path.dirname(paddlex.__file__)
    
    # Include version file
    version_file = os.path.join(paddlex_dir, '.version')
    if os.path.exists(version_file):
        datas.append((version_file, 'paddlex'))
    
    # Include any JSON config files
    for filename in os.listdir(paddlex_dir):
        if filename.endswith(('.json', '.yaml', '.yml')):
            file_path = os.path.join(paddlex_dir, filename)
            if os.path.isfile(file_path):
                datas.append((file_path, 'paddlex'))
except Exception as e:
    print(f"Warning: Could not collect all paddlex metadata: {e}")
    pass
