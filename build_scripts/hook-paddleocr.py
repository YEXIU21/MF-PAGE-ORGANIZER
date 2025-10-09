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

# PaddleOCR models will be downloaded automatically on first run
# This avoids build conflicts with .git and .cache files in model directories
print("ℹ️  PaddleOCR hook: Skipping model bundling to avoid conflicts")
print("ℹ️  Models will be downloaded automatically on first OCR use")
print("✅ PaddleOCR hook: Dependencies collected successfully")
