#!/usr/bin/env python3
"""
PyInstaller Hook for PaddleOCR
Ensures all PaddleOCR models and dependencies are bundled correctly
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files
import os
from pathlib import Path

# Collect all PaddleOCR modules and data
datas, binaries, hiddenimports = collect_all('paddleocr')

# Additional hidden imports for PaddleOCR components
hiddenimports += [
    'paddleocr.paddleocr',
    'paddleocr.tools',
    'paddleocr.tools.infer',
    'ppocr',
    'ppocr.utils',
    'ppocr.data',
    'ppocr.modeling',
    'ppocr.modeling.architectures',
    'ppocr.modeling.backbones',
    'ppocr.modeling.heads',
    'ppocr.modeling.necks',
    'ppocr.modeling.transforms',
    'ppocr.postprocess',
    'ppocr.optimizer',
    'ppocr.losses',
    'ppocr.metrics',
    'tools.infer.predict_system',
    'tools.infer.predict_rec',
    'tools.infer.predict_det',
    'tools.infer.predict_cls',
    'tools.infer.utility',
    'paddle.inference',
    'paddle.framework',
    'paddle.fluid',
    'paddle.fluid.core',
    'paddle.fluid.core_avx',
    'yaml',
    'Polygon',
    'pyclipper',
    'shapely',
    'imgaug',
    'lmdb',
    'tqdm',
    'visualdl',
    'python-Levenshtein',
    'rapidfuzz',
    'opencv-python',
    'opencv-contrib-python',
    'Cython',
    'lanms-neo',
]

# Try to collect PaddleOCR model files from standard locations
try:
    # Check user's home directory for downloaded models
    paddlex_home = Path.home() / '.paddlex'
    if paddlex_home.exists():
        for model_file in paddlex_home.rglob('*'):
            if model_file.is_file():
                datas.append((str(model_file), str(model_file.relative_to(Path.home()))))
    
    # Check user's .paddleocr directory for models
    paddleocr_home = Path.home() / '.paddleocr'
    if paddleocr_home.exists():
        for model_file in paddleocr_home.rglob('*'):
            if model_file.is_file():
                datas.append((str(model_file), str(model_file.relative_to(Path.home()))))
    
    # Try to find models in PaddleOCR installation
    import paddleocr
    paddleocr_path = Path(paddleocr.__file__).parent
    inference_path = paddleocr_path / 'inference'
    if inference_path.exists():
        for model_file in inference_path.rglob('*'):
            if model_file.is_file():
                datas.append((str(model_file), f'paddleocr_models/{model_file.relative_to(inference_path)}'))

    print("✅ PaddleOCR hook: Models bundled successfully")
    
except Exception as e:
    print(f"⚠️  PaddleOCR hook warning: {e}")
    # Continue without models - runtime will download them if needed
