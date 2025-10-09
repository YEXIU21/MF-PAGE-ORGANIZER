# Auto-Crop Validation System

## Overview

The Auto-Crop Validation System automatically detects problematic auto-crop results and flags pages that may need manual review. This ensures that important content is not accidentally cut off during automated cropping.

## Problem Solved

Auto-crop can fail or produce poor results when:
- ❌ **Cut-off paper scans**: Scanner bed edges visible in image
- ❌ **Very black scanner bed**: Large black areas from scanner background
- ❌ **Asymmetric borders**: One side has much larger margin than others
- ❌ **Content at edges**: Text or images very close to page borders
- ❌ **Failed detection**: Auto-crop doesn't detect borders properly

## How It Works

### 1. **Automatic Validation**
When auto-crop is enabled, the system automatically:
1. Crops the image using content detection
2. Validates the crop quality
3. Calculates confidence score (0-100%)
4. Detects specific issues
5. Flags problematic pages for review

### 2. **Issue Detection**

The validator checks for:

| Issue | Detection Criteria | Confidence Impact |
|-------|-------------------|-------------------|
| **Excessive Cropping** | >40% of image area removed | -30% |
| **Minimal Cropping** | <5% of image area removed | -10% |
| **Asymmetric Cropping** | Width vs height reduction differs by >30% | -15% |
| **Black Borders Remaining** | >15% of edges are dark | -25% |
| **Content Cut-off** | Significant text/content at image edges | -20% |

### 3. **Confidence Scoring**

- **100%**: Perfect crop, no issues
- **70-99%**: Good crop, minor issues
- **<70%**: Problematic crop, needs review (flagged)

## Generated Reports

### Text Report: `CROP_REVIEW_NEEDED.txt`

Human-readable report listing all problematic pages:

```
======================================================================
AUTO-CROP MANUAL REVIEW REQUIRED
======================================================================

Total pages needing review: 3

The following pages had auto-crop issues and may need manual cropping:

1. page_045.jpg
   Confidence: 55.0%
   Crop Stats: (2480, 3508) → (1200, 1600)
   Crop Ratio: 35.2% retained
   Issues:
      - Excessive cropping detected: 64.8% of image removed
      - Asymmetric cropping: width=51.6%, height=54.4%

2. page_087.jpg
   Confidence: 65.0%
   Crop Stats: (2480, 3508) → (2400, 3400)
   Crop Ratio: 95.2% retained
   Issues:
      - Significant black borders remain: 25.0% of edges are dark

3. page_123.jpg
   Confidence: 60.0%
   Crop Stats: (2480, 3508) → (2200, 3200)
   Crop Ratio: 82.1% retained
   Issues:
      - Potential content cut-off: Significant text/content detected at edges
```

### JSON Report: `crop_validation_report.json`

Programmatic access to validation results:

```json
{
  "total_problematic_pages": 3,
  "pages": [
    {
      "page_name": "page_045.jpg",
      "is_valid": false,
      "confidence": 55.0,
      "needs_review": true,
      "issues": [
        "Excessive cropping detected: 64.8% of image removed",
        "Asymmetric cropping: width=51.6%, height=54.4%"
      ],
      "crop_stats": {
        "original_size": [2480, 3508],
        "cropped_size": [1200, 1600],
        "crop_ratio": 0.352,
        "width_reduction": 0.516,
        "height_reduction": 0.544
      }
    }
  ]
}
```

## Usage

### Automatic (Recommended)

When auto-crop is enabled in GUI or config, validation runs automatically:

**GUI:**
1. Enable "Auto crop pages" checkbox
2. Run processing
3. Check output folder for `CROP_REVIEW_NEEDED.txt` if present

**Config:**
```json
{
  "preprocessing": {
    "auto_crop": true
  }
}
```

### Manual Review Workflow

If `CROP_REVIEW_NEEDED.txt` is generated:

1. **Open the report** to see flagged pages
2. **Locate the pages** in the output folder
3. **Visual inspection**:
   - Check if content is cut off
   - Verify black borders are acceptable
   - Confirm cropping is reasonable
4. **Manual correction** (if needed):
   - Open page in image editor
   - Manually crop to desired size
   - Save corrected version
5. **Re-run if necessary** with corrected pages

## Configuration

### Enable/Disable Validation

Validation runs automatically when auto-crop is enabled. No separate configuration needed.

### Adjust Sensitivity

To modify validation thresholds, edit `core/crop_validator.py`:

```python
# Excessive cropping threshold (default: 40%)
if crop_ratio < 0.6:  # Change 0.6 to adjust

# Black border threshold (default: 15%)
if black_border_score > 0.15:  # Change 0.15 to adjust

# Content at edges threshold (default: 30%)
if edge_content_score > 0.3:  # Change 0.3 to adjust
```

## Visual Indicators

In processing logs, cropped pages show:
- ✅ `auto_crop` - Successful crop, no issues
- ⚠️ `auto_crop(⚠️75%)` - Crop with warnings, 75% confidence

## Best Practices

### For Best Auto-Crop Results:

1. **Scan Quality**:
   - ✅ Place paper centered on scanner bed
   - ✅ Use clean scanner glass
   - ✅ Avoid shadows at edges
   - ✅ Ensure paper is flat

2. **Settings**:
   - ✅ Enable auto-rotate for orientation correction
   - ✅ Use at least 300 DPI for accurate detection
   - ✅ Enable deskew if pages are tilted

3. **Problem Prevention**:
   - ❌ Avoid scanning multiple pages in one image
   - ❌ Don't include scanner bed edges
   - ❌ Minimize text at very edge of paper
   - ❌ Avoid very dark or very light backgrounds

## Troubleshooting

### Issue: All pages flagged for review
**Cause**: Scans may have unusual characteristics
**Solution**: 
- Check scan quality
- Adjust validation thresholds
- Consider manual cropping before processing

### Issue: No pages flagged but crops look bad
**Cause**: Issues below detection thresholds
**Solution**:
- Manually inspect random samples
- Report false negatives for improvement
- Adjust thresholds to be more strict

### Issue: Too many false positives
**Cause**: Thresholds too strict for your document type
**Solution**:
- Adjust thresholds in `crop_validator.py`
- Consider your specific document characteristics
- Document-specific calibration may be needed

## Technical Details

### Validation Algorithm

1. **Calculate crop statistics**:
   - Original vs cropped dimensions
   - Area reduction percentage
   - Asymmetry measurement

2. **Border analysis**:
   - Extract 5% border regions
   - Calculate average intensity
   - Detect dark borders

3. **Edge content detection**:
   - Extract 3% edge regions
   - Apply Canny edge detection
   - Calculate edge density

4. **Confidence calculation**:
   - Start at 100%
   - Deduct points for each issue
   - Flag if below 70%

### Performance Impact

- **Minimal**: ~0.1-0.3 seconds per page
- **Memory**: <10MB additional RAM
- **No impact on output quality**: Only validation, not cropping itself

## Future Enhancements

Planned improvements:
- Machine learning for better issue detection
- Automatic correction suggestions
- Interactive review UI
- Batch manual review tools
- Custom validation profiles per document type
