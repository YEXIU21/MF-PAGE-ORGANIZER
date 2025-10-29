# ML Training - Ultra-Fast Page Number Detection

This directory contains tools to train a custom machine learning model for ultra-fast page number detection.

## 🎯 Goal

Train a specialized neural network that detects page numbers **50x faster** than PaddleOCR (0.1s vs 5s per page).

## 📋 Overview

**Phase 1: Data Collection** ← YOU ARE HERE  
**Phase 2: Model Training**  
**Phase 3: Integration**  
**Phase 4: Deployment**  

---

## Phase 1: Data Collection (Current)

### What You Need

- 50+ books to process (the more, the better!)
- Your existing page automation system
- ~500MB disk space for training data

### How to Collect Data

#### Step 1: Start Collection Mode

```python
# In Python console or script:
from ml_training.enable_data_collection import start_collection, stop_collection

# Enable data collection
start_collection()
```

#### Step 2: Process Books Normally

```bash
# Run your normal book processing
# Data will be collected automatically in the background
python main.py --input "C:\path\to\books" --output "C:\path\to\output"
```

#### Step 3: Stop Collection

```python
# After processing is complete
stop_collection()

# This will show:
# - Total images collected
# - Class distribution
# - Dataset quality report
```

### What Gets Collected

For each page processed:
- ✅ Corner image where number was found (positive example)
- ✅ Corner images where number was NOT found (negative examples)
- ✅ Label (the actual page number: "1", "2", "i", "ii", etc.)
- ✅ Metadata (confidence, location, source book, etc.)

### Expected Results

After processing 50 books (~10,000 pages):

```
Training Data Structure:
├── ml_training/training_data/
│   ├── corners/
│   │   ├── 1/          (500+ images of "1")
│   │   ├── 2/          (500+ images of "2")
│   │   ├── i/          (300+ images of "i")
│   │   ├── ii/         (300+ images of "ii")
│   │   ├── none/       (5000+ images of blank corners)
│   │   └── ...
│   └── metadata/
│       ├── dataset_info.json
│       └── collection_report.txt

Total: ~2,500 labeled classes
Total Images: ~50,000
```

---

## Phase 2: Model Training (Next)

### Prerequisites

```bash
# Install ML libraries
pip install tensorflow>=2.10 
# OR
pip install torch>=2.0

# Install additional tools
pip install scikit-learn matplotlib
```

### Training Process

```bash
# Train the model (will be created in Phase 2)
python ml_training/train_model.py \
    --data ml_training/training_data \
    --output ml_training/models \
    --epochs 50

# Expected time: 1-2 hours on CPU, 15 minutes on GPU
```

### Model Output

```
ml_training/models/
├── page_detector.h5        (2MB - TensorFlow)
├── page_detector.pth       (2MB - PyTorch)
├── training_history.json
├── accuracy_report.pdf
└── model_config.json
```

---

## Phase 3: Integration (After Training)

Replace PaddleOCR with custom model:

```python
# In paddle_number_detector.py
from ml_training.model_predictor import PageNumberPredictor

# Initialize once
model = PageNumberPredictor('ml_training/models/page_detector.h5')

# Use for detection
def detect_page_number(self, corner_image):
    # Ultra-fast prediction (0.001s)
    result = model.predict(corner_image)
    return result
```

---

## Phase 4: Deployment

### Testing

```bash
# Test on new books
python ml_training/test_model.py \
    --model ml_training/models/page_detector.h5 \
    --test_books "C:\path\to\test\books"
```

### Performance Benchmarks

| Metric | PaddleOCR (Current) | Custom Model (Target) |
|--------|-------------------|----------------------|
| Speed per page | 5-8 seconds | 0.1 seconds |
| 470 pages | 40-60 minutes | 47 seconds |
| Accuracy | 95% | 98%+ |
| Model size | 100MB+ | 2MB |

---

## 📊 Current Status

### ✅ Completed

- [x] Data collector script (`data_collector.py`)
- [x] Collection mode enabler (`enable_data_collection.py`)
- [x] Integration hooks
- [x] Documentation

### ⏳ In Progress

- [ ] Collect training data from books
- [ ] Verify dataset quality

### 📝 Todo (Phase 2)

- [ ] Design model architecture
- [ ] Create training script
- [ ] Train initial model
- [ ] Evaluate accuracy
- [ ] Fine-tune hyperparameters

---

## 🚀 Quick Start

### Simplest Way to Start

1. **Open Python console in your project directory:**

```python
# Start collection
from ml_training.enable_data_collection import start_collection, stop_collection
start_collection()
```

2. **Process books using GUI or command line** - Collection happens automatically!

3. **Stop collection when done:**

```python
# See results
stop_collection()
```

4. **Check results:**

```bash
# View collected data
dir ml_training\training_data\corners

# Read report
type ml_training\training_data\metadata\collection_report.txt
```

---

## 💡 Tips

### For Best Results

1. **Diverse Books**
   - Mix of old and new books
   - Different publishers
   - Various numbering styles

2. **Quality Over Quantity**
   - Better to have 50 well-scanned books
   - Than 100 poor-quality scans

3. **Check Progress**
   - Monitor collection report
   - Ensure balanced classes
   - Aim for 10+ examples per number

### Troubleshooting

**Problem:** Too few examples for some numbers
**Solution:** Process more books, or focus on books with those numbers

**Problem:** Class imbalance (many "1"s, few "50"s)
**Solution:** Normal! Model will still work. Can balance during training.

**Problem:** Disk space running out
**Solution:** Use external drive or clean up after collecting from a batch

---

## 📁 File Structure

```
ml_training/
├── README.md                      ← You are here
├── data_collector.py              ← Collects corner images + labels
├── enable_data_collection.py      ← Enables collection mode
├── train_model.py                 ← (Phase 2) Train the model
├── model_predictor.py             ← (Phase 3) Use trained model
├── test_model.py                  ← (Phase 4) Test accuracy
├── training_data/                 ← Collected data goes here
│   ├── corners/                   ← Corner images organized by class
│   └── metadata/                  ← Dataset info and reports
└── models/                        ← Trained models go here
```

---

## 🎯 Success Criteria

### Data Collection Phase Complete When:

- ✅ 1000+ total images collected
- ✅ 50+ unique number classes
- ✅ 10+ examples per common number (1-20)
- ✅ 5+ examples per less common number (21+)
- ✅ 500+ "none" (blank) examples
- ✅ Dataset validation passes

### Ready for Training When:

```
Dataset Report shows:
📊 Total Images: 1000+
🏷️ Total Classes: 50+
✅ Class balance: Reasonable (max/min < 10x)
✅ Quality check: PASSED
```

---

## 📞 Questions?

Check the main documentation: `LIGHTWEIGHT_MODEL_SOLUTION.md`

---

**Created:** 2025-10-29  
**Status:** Phase 1 - Data Collection Ready  
**Next:** Collect data from your book library!
