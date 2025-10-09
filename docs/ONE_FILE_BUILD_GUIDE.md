# One-File Executable Build Guide

## Overview

The one-file build creates a **single, portable executable** that contains everything needed to run MF Page Organizer. This is perfect for distribution and sharing.

## Key Features

### ✅ **Single File Solution**
- **One EXE file** - No additional folders or files needed
- **Fully portable** - Run from any location (USB, email, cloud storage)
- **Self-contained** - All dependencies embedded

### ✅ **Full Functionality**  
- **Complete PaddleOCR support** - Roman numeral detection (vi, vii, viii, ix, x, xi, xii)
- **Multi-position scanning** - Top-left, top-right, bottom-left, center
- **Content-based reordering** - Uses actual page numbers, not filenames
- **All core features** - Same functionality as folder builds

## Build Process

### Quick Build
```powershell
cd "g:\Vault\Ubix\Page Automation"
python build_scripts\build_exe_onefile.py
```

### Build Steps
1. **Icon Conversion**: Creates Windows-compatible icon
2. **PyInstaller Installation**: Ensures build tools available
3. **Model Pre-download**: Downloads PaddleOCR models (optional)
4. **One-File Compilation**: Creates single executable (~10-15 minutes)

## Technical Details

### 📊 **File Specifications**
- **Size**: ~200-500 MB (varies based on included dependencies)
- **Format**: Windows PE executable (.exe)
- **Architecture**: x64 (matches your Python installation)
- **Compression**: Built-in PyInstaller compression

### ⚡ **Performance Characteristics**

| Metric | One-File | Folder Build |
|--------|----------|--------------|
| **First Startup** | 10-15 seconds | 2-3 seconds |
| **Subsequent Runs** | 3-5 seconds | 1-2 seconds |
| **Disk Space** | 200-500 MB | 150-300 MB |
| **RAM Usage** | Same | Same |
| **OCR Speed** | Same | Same |

### 🔧 **How It Works**
1. **Startup**: EXE extracts to temporary directory
2. **Extraction**: All files unpacked to `%TEMP%\_MEI*****\`
3. **Execution**: Runs from temporary location
4. **Cleanup**: Temp files removed on exit

## Advantages vs Folder Builds

### ✅ **One-File Advantages**
- **Ultimate Portability**: Single file to share/distribute
- **Simplified Distribution**: Email, USB, cloud storage friendly
- **No Missing Files**: Can't lose dependencies
- **Clean Installation**: No installer needed
- **Version Control**: Easy to manage single file versions

### ⚠️ **Trade-offs**
- **Larger File Size**: ~2x larger than folder build
- **Slower Startup**: Extraction time on first run
- **Antivirus Sensitivity**: Some AV may flag large executables
- **Disk Space**: Requires more space during extraction

## Use Cases

### 🎯 **Perfect For:**
- **Client Distribution**: Send to customers via email
- **Portable Operations**: Run from USB drives
- **Quick Deployment**: No installation process
- **Backup/Archive**: Single file for storage
- **Testing**: Easy to share test versions

### 🚫 **Not Ideal For:**
- **Frequent Development**: Slower build/test cycle
- **Resource-Constrained Systems**: Large file size
- **Network Deployment**: Large download size
- **Automated Installation**: Folder builds better for installers

## PaddleOCR Integration

### 📥 **Model Handling**
The one-file build handles PaddleOCR models intelligently:

1. **First OCR Use**: Models download automatically
2. **Model Storage**: Cached in user's home directory
3. **Subsequent Uses**: Models loaded from cache
4. **Offline Operation**: Works without internet after first download

### 🔍 **OCR Capabilities**
- **Roman Numerals**: vi, vii, viii, ix, x, xi, xii (from memory analysis)
- **Arabic Numbers**: 1, 2, 3, 4, 5, etc.
- **Multi-Position**: Scans all corners and center
- **High Accuracy**: Same OCR engine as folder builds

## Distribution

### 📤 **Sharing Methods**
- **Email**: Compress if size limits apply
- **Cloud Storage**: Google Drive, Dropbox, OneDrive
- **USB/Flash Drive**: Copy directly
- **Network Share**: Single file deployment
- **Download Links**: Direct download from website

### 🔒 **Security Considerations**
- **Code Signing**: Consider signing for enterprise distribution
- **Antivirus**: Test with major AV solutions
- **Checksums**: Provide SHA-256 hashes for integrity
- **Documentation**: Include usage instructions

## Troubleshooting

### ❓ **Common Issues**

**Slow Startup:**
- First run extracts files (normal)
- Subsequent runs much faster
- SSD recommended for best performance

**Antivirus Warnings:**
- Large executables may trigger false positives
- Add to AV whitelist if needed
- Consider code signing certificate

**File Size Concerns:**
- Use folder build if size is critical
- Compression tools can reduce distribution size
- Consider splitting into installer format

**Extraction Errors:**
- Ensure sufficient disk space in TEMP
- Check write permissions to temp directory
- Run as administrator if needed

## Comparison Matrix

| Aspect | One-File | Enhanced Folder | Fast Folder |
|--------|----------|-----------------|-------------|
| **Portability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Startup Speed** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **File Size** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Distribution** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Functionality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Best Practices

### 🎯 **When to Use One-File**
- Distributing to end users
- Sharing via email/cloud
- Portable/demo versions
- Backup archival
- Simple deployment scenarios

### 🎯 **When to Use Folder Build**
- Development and testing
- Performance-critical applications
- Automated deployment
- Size-constrained environments
- Frequent updates needed

The one-file build provides the ultimate in portability while maintaining full functionality, making it perfect for distribution and sharing scenarios where a single executable file is preferred.
