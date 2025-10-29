# Manual Training Data Labeling Guide

Quick guide to manually create training data for the ML model.

## 🎯 Goal

Manually label 50-100 page images to create initial training dataset.

## 📋 Prerequisites

- Folder with page images from your book
- 10-15 minutes of your time
- Python with OpenCV installed

## 🚀 Quick Start

### Step 1: Prepare Images

Put 50-100 page images in a folder. For example:
```
C:\TrainingImages\
├── page_001.jpg
├── page_002.jpg
├── page_003.jpg
...
├── page_050.jpg
```

### Step 2: Run Manual Labeler

```bash
python ml_training/manual_labeler.py "C:\TrainingImages"
```

### Step 3: Label Each Image

For each image:

1. **Image shown with colored boxes** marking corners
   - Blue = top_left
   - Green = top_right
   - Red = bottom_left
   - Cyan = bottom_right
   - Magenta = top_center
   - Yellow = bottom_center

2. **Press ESC to skip** or **any key to label**

3. **Select corner** where page number is:
   ```
   1 = top_left
   2 = top_right
   3 = bottom_left
   4 = bottom_right
   5 = top_center
   6 = bottom_center
   0 = No number (skip)
   ```

4. **Type the page number** you see (e.g., "23" or "i" or "xv")

5. **Press Enter** - saved!

6. **Repeat** for next image

### Step 4: Review Results

After labeling:
```
ml_training/manual_training_data/
├── corners/
│   ├── 1/          (images labeled "1")
│   ├── 2/          (images labeled "2")
│   ├── 23/         (images labeled "23")
│   ├── i/          (images labeled "i")
│   └── ...
└── labeling_stats.json
```

## 💡 Tips

### Quality Over Quantity

- **50 well-labeled images** better than 500 rushed
- **Focus on clarity** - only label if number is clear
- **Skip if unsure** - better to skip than mislabel

### Diverse Samples

Try to get variety:
- Different number ranges (1-10, 11-50, 51-100)
- Different positions (corners, center, edges)
- Roman numerals if present (i, ii, iii, etc.)
- Different page styles

### Keyboard Shortcuts

- **ESC**: Skip current image
- **Ctrl+C**: Stop labeling and save progress
- **Any key**: Start labeling current image

## 📊 Recommended Minimum

For good initial training:

| Category | Minimum | Recommended |
|----------|---------|-------------|
| Common numbers (1-20) | 3 each | 5 each |
| Medium numbers (21-100) | 1 each | 2 each |
| Large numbers (100+) | As available | 1+ each |
| Roman numerals | 2 each | 3 each |
| **Total images** | **50+** | **100+** |

## ⏱️ Time Estimate

- **50 images**: ~10-15 minutes
- **100 images**: ~20-25 minutes
- **Per image**: ~15-20 seconds

## ✅ Success Criteria

After labeling, you should have:

- [ ] 50+ labeled corner images
- [ ] 10+ unique number classes
- [ ] At least 3 examples of common numbers (1-10)
- [ ] Clear, correctly labeled samples

## 🎯 Next Steps

### After Labeling:

1. **Check stats:**
   - `ml_training/manual_training_data/labeling_stats.json`

2. **Review samples:**
   - Browse `ml_training/manual_training_data/corners/`

3. **Ready for training:**
   - Once you have 50+ images
   - Move to Phase 2: Model Training

## 🐛 Troubleshooting

**Image won't display:**
- Make sure OpenCV is installed: `pip install opencv-python`
- Check image format (JPG, PNG supported)

**Corner boxes wrong position:**
- Tool assumes standard page size
- Works best with scanned book pages
- Skip if image is unusual size

**Can't see page number:**
- Press ESC to skip
- Not all pages have visible numbers
- That's okay!

## 🔄 Example Session

```
$ python ml_training/manual_labeler.py "C:\MyBook"

Found 75 images

Image 1/75: page_001.jpg
Which corner? 4 (bottom_right)
Page number? 1
✅ Saved

Image 2/75: page_002.jpg  
Which corner? 4 (bottom_right)
Page number? 2
✅ Saved

...

STATISTICS:
Images processed: 75
Corners cropped: 68
Unique labels: 42

✅ Complete!
```

## 🎓 Training Data Quality

**Good training data has:**
- ✅ Correct labels (most important!)
- ✅ Clear, readable numbers
- ✅ Diverse styles
- ✅ Multiple examples per number

**Avoid:**
- ❌ Blurry images
- ❌ Incorrect labels
- ❌ Duplicate samples
- ❌ Non-page-number text

---

**Ready to start?** Just run the command and start labeling! 🚀

**Questions?** Check the main documentation: `ml_training/README.md`
