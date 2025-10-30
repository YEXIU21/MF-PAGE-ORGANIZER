#!/usr/bin/env python3
"""
Dependency Checker for ML Labeler
Checks which packages are installed and which are missing
"""

import sys

def check_dependency(module_name, package_name, description):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {description:20} - INSTALLED")
        return True
    except ImportError as e:
        print(f"❌ {description:20} - MISSING")
        print(f"   Install with: pip install {package_name}")
        print(f"   Error: {e}")
        print()
        return False

print("=" * 60)
print("ML LABELER DEPENDENCY CHECK")
print("=" * 60)
print()

all_good = True

print("REQUIRED FOR LABELING:")
print("-" * 60)
all_good &= check_dependency("cv2", "opencv-python", "OpenCV")
all_good &= check_dependency("PIL", "pillow", "Pillow (PIL)")
all_good &= check_dependency("numpy", "numpy", "NumPy")
all_good &= check_dependency("tkinter", "tkinter", "Tkinter (GUI)")

print()
print("REQUIRED FOR TRAINING (optional for labeling):")
print("-" * 60)
check_dependency("tensorflow", "tensorflow", "TensorFlow")

print()
print("=" * 60)
if all_good:
    print("✅ ALL LABELING DEPENDENCIES INSTALLED!")
    print("   You can use the Interactive Labeler.")
else:
    print("❌ SOME DEPENDENCIES MISSING!")
    print("   Install missing packages, then restart the app.")
print("=" * 60)
