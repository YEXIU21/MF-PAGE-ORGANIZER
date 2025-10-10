"""
PyInstaller hook for PaddleX
Ensures .version file and other PaddleX resources are bundled
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files from paddlex package
datas = collect_data_files('paddlex')

# Collect all submodules
hiddenimports = collect_submodules('paddlex')

# Explicitly include .version file if it exists
import os
try:
    import paddlex
    paddlex_dir = os.path.dirname(paddlex.__file__)
    version_file = os.path.join(paddlex_dir, '.version')
    if os.path.exists(version_file):
        datas.append((version_file, 'paddlex'))
except:
    pass
