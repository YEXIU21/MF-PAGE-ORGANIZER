# MF Page Organizer - AI-Powered Page Organization

## 🚀 Quick Start

**To run the application:**
```
python gui_mf.py
```

Or double-click `gui_mf.py`

---

# AI Page Reordering Automation System

🎯 **Purpose**: Automatically arrange unordered page images into correct order using OCR, AI content analysis, and various numbering system detection.

## 📚 Documentation

All detailed documentation has been moved to the `docs/` folder:
- **SYSTEM_STATUS.md** - Current system status
- **FEATURE_COMPATIBILITY.md** - Feature compatibility guide
- **AI_IMPROVEMENTS.md** - AI features explained
- **PROJECT_STRUCTURE.md** - Project organization
- And more...

## Features

- **Dual Interface**: Command-line and GUI modes
- **Multiple File Support**: PDF, PNG, JPG, TIFF
- **Smart Numbering Detection**: Arabic, Roman, hybrid, hierarchical formats
- **Content-Based Ordering**: For pages without clear numbers
- **Optional Preprocessing**: Denoise, deskew, contrast enhancement
- **Confidence System**: Human review for uncertain decisions
- **Learning Memory**: Remembers past corrections and user preferences

## Installation

1. Install Python 3.8+
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Tesseract OCR:
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Add Tesseract to your PATH

## Usage

### Command Line Mode
```bash
python main.py --input "path/to/images" --output "path/to/result" --denoise off --ocr on --confidence 85
```

### GUI Mode
```bash
python gui.py
```

## Project Structure
```
Page Automation/
├── main.py                 # Main CLI entry point
├── gui.py                  # GUI interface
├── core/                   # Core functionality
│   ├── __init__.py
│   ├── input_handler.py    # File input processing
│   ├── preprocessor.py     # Image preprocessing
│   ├── ocr_engine.py       # OCR and number extraction
│   ├── numbering_system.py # Numbering scheme detection
│   ├── content_analyzer.py # Content-based ordering
│   ├── confidence_system.py # Confidence scoring
│   └── output_manager.py   # Output generation
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── logger.py          # Logging system
│   └── memory.py          # Learning memory system
├── data/                  # Data storage
│   ├── models/            # AI models
│   ├── temp/              # Temporary files
│   └── memory/            # User preferences and corrections
└── tests/                 # Unit tests
    └── __init__.py
```

## Configuration

Edit `config.json` to customize default settings:
- OCR confidence threshold
- Preprocessing options
- Output formats
- Memory retention settings
