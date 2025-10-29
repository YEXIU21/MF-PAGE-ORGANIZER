"""
Manual Training Data Labeler
Simple GUI tool for manually creating training data
"""

import cv2
import os
from pathlib import Path
import json

class ManualLabeler:
    """Interactive tool for manual data labeling"""
    
    def __init__(self, image_folder: str, output_folder: str = "ml_training/manual_training_data"):
        self.image_folder = Path(image_folder)
        self.output_folder = Path(output_folder)
        self.corners_dir = self.output_folder / "corners"
        self.corners_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'total_processed': 0,
            'total_cropped': 0,
            'labels_created': {}
        }
        
        print("=" * 70)
        print("MANUAL TRAINING DATA LABELER")
        print("=" * 70)
        print(f"Input folder: {self.image_folder}")
        print(f"Output folder: {self.output_folder}")
        print()
    
    def get_corner_crop(self, image, corner_name):
        """Get corner region based on name"""
        h, w = image.shape[:2]
        
        corner_configs = {
            'top_left': (0, 0, 200, 200),
            'top_right': (w-200, 0, w, 200),
            'bottom_left': (0, h-200, 200, h),
            'bottom_right': (w-200, h-200, w, h),
            'top_center': (w//2-100, 0, w//2+100, 200),
            'bottom_center': (w//2-100, h-200, w//2+100, h)
        }
        
        if corner_name in corner_configs:
            x1, y1, x2, y2 = corner_configs[corner_name]
            return image[y1:y2, x1:x2]
        
        return None
    
    def show_image_with_corners(self, image_path):
        """Show image with corner highlights"""
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"❌ Could not load: {image_path}")
            return None
        
        h, w = img.shape[:2]
        display = img.copy()
        
        # Draw corner boxes
        corners = {
            'top_left': (0, 0, 200, 200),
            'top_right': (w-200, 0, w, 200),
            'bottom_left': (0, h-200, 200, h),
            'bottom_right': (w-200, h-200, w, h),
            'top_center': (w//2-100, 0, w//2+100, 200),
            'bottom_center': (w//2-100, h-200, w//2+100, h)
        }
        
        colors = {
            'top_left': (255, 0, 0),      # Blue
            'top_right': (0, 255, 0),     # Green
            'bottom_left': (0, 0, 255),   # Red
            'bottom_right': (255, 255, 0), # Cyan
            'top_center': (255, 0, 255),  # Magenta
            'bottom_center': (0, 255, 255) # Yellow
        }
        
        for name, (x1, y1, x2, y2) in corners.items():
            color = colors.get(name, (128, 128, 128))
            cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
            cv2.putText(display, name, (x1+5, y1+20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return img, display
    
    def label_image(self, image_path):
        """Interactive labeling for single image"""
        print(f"\n📄 Processing: {image_path.name}")
        
        img, display = self.show_image_with_corners(image_path)
        if img is None:
            return
        
        # Resize for display if too large
        max_display_width = 1200
        h, w = display.shape[:2]
        if w > max_display_width:
            scale = max_display_width / w
            new_h, new_w = int(h * scale), int(w * scale)
            display = cv2.resize(display, (new_w, new_h))
        
        cv2.imshow('Page Image - Press ESC to skip, any other key to label', display)
        key = cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        if key == 27:  # ESC
            print("   ⏭️  Skipped")
            return
        
        # Ask which corner has page number
        print("\n   Which corner has the page number?")
        print("   1 = top_left")
        print("   2 = top_right")
        print("   3 = bottom_left")
        print("   4 = bottom_right")
        print("   5 = top_center")
        print("   6 = bottom_center")
        print("   0 = No number visible (skip)")
        
        corner_map = {
            '1': 'top_left',
            '2': 'top_right',
            '3': 'bottom_left',
            '4': 'bottom_right',
            '5': 'top_center',
            '6': 'bottom_center'
        }
        
        choice = input("   Enter choice (0-6): ").strip()
        
        if choice == '0':
            print("   ⏭️  No number - skipped")
            return
        
        if choice not in corner_map:
            print("   ❌ Invalid choice")
            return
        
        corner_name = corner_map[choice]
        
        # Get corner crop
        corner_img = self.get_corner_crop(img, corner_name)
        if corner_img is None:
            print("   ❌ Could not extract corner")
            return
        
        # Show corner
        cv2.imshow('Corner - What number do you see?', corner_img)
        cv2.waitKey(500)
        cv2.destroyAllWindows()
        
        # Ask for label
        label = input("   What is the page number? (or press Enter to skip): ").strip()
        
        if not label:
            print("   ⏭️  Skipped")
            return
        
        # Resize to 200x200
        corner_resized = cv2.resize(corner_img, (200, 200), interpolation=cv2.INTER_AREA)
        
        # Save
        class_dir = self.corners_dir / label
        class_dir.mkdir(exist_ok=True)
        
        # Filename: label_source_timestamp.jpg
        import time
        timestamp = str(int(time.time() * 1000))
        filename = f"{label}_{image_path.stem}_{timestamp}.jpg"
        save_path = class_dir / filename
        
        cv2.imwrite(str(save_path), corner_resized)
        
        # Update stats
        self.stats['total_cropped'] += 1
        if label not in self.stats['labels_created']:
            self.stats['labels_created'][label] = 0
        self.stats['labels_created'][label] += 1
        
        print(f"   ✅ Saved as: {label}/{filename}")
        
        self.stats['total_processed'] += 1
    
    def process_folder(self):
        """Process all images in folder"""
        # Get all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(list(self.image_folder.glob(ext)))
            image_files.extend(list(self.image_folder.glob(ext.upper())))
        
        image_files = sorted(image_files)
        
        if not image_files:
            print(f"❌ No images found in: {self.image_folder}")
            return
        
        print(f"📚 Found {len(image_files)} images")
        print()
        print("INSTRUCTIONS:")
        print("  - Image will be shown with colored boxes marking corners")
        print("  - Press ESC to skip image")
        print("  - Press any other key to label it")
        print("  - Select which corner has the page number")
        print("  - Type the page number you see")
        print("  - Press Ctrl+C anytime to stop and save progress")
        print()
        input("Press Enter to start...")
        
        try:
            for img_path in image_files:
                self.label_image(img_path)
        
        except KeyboardInterrupt:
            print("\n\n⏸️  Stopped by user")
        
        # Final stats
        self.show_stats()
        self.save_stats()
    
    def show_stats(self):
        """Show collection statistics"""
        print("\n" + "=" * 70)
        print("LABELING STATISTICS")
        print("=" * 70)
        print(f"📄 Images processed: {self.stats['total_processed']}")
        print(f"✂️  Corners cropped: {self.stats['total_cropped']}")
        print(f"🏷️  Unique labels: {len(self.stats['labels_created'])}")
        print()
        
        if self.stats['labels_created']:
            print("Label distribution:")
            for label, count in sorted(self.stats['labels_created'].items()):
                print(f"  {label:>10s} : {count:>3d} images")
        
        print("=" * 70)
        print(f"📁 Data saved to: {self.output_folder}")
        print("=" * 70)
    
    def save_stats(self):
        """Save statistics to JSON"""
        stats_file = self.output_folder / "labeling_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        print(f"📊 Stats saved to: {stats_file}")


def main():
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              MANUAL TRAINING DATA LABELER                            ║
╚══════════════════════════════════════════════════════════════════════╝

This tool helps you manually create training data by:
1. Showing each page image
2. Letting you select which corner has the page number
3. Labeling it with the correct number
4. Saving cropped 200x200 corner images

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    if len(sys.argv) < 2:
        print("USAGE:")
        print("  python ml_training/manual_labeler.py <folder_with_images>")
        print()
        print("EXAMPLE:")
        print('  python ml_training/manual_labeler.py "C:\\Books\\TestBook"')
        print()
        
        # Interactive mode
        folder = input("Enter path to folder with page images: ").strip().strip('"')
        if not folder:
            print("❌ No folder specified")
            return
    else:
        folder = sys.argv[1]
    
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return
    
    labeler = ManualLabeler(folder)
    labeler.process_folder()
    
    print("\n✅ Manual labeling complete!")
    print(f"\n🎯 NEXT STEP: Train model with your labeled data")
    print(f"   (Will create training script in Phase 2)")


if __name__ == "__main__":
    main()
