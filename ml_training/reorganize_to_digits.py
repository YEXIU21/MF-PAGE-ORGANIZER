"""
Reorganize Training Data - From Page Numbers to Digit Level
Converts 400+ page number classes to ~40 digit/character classes

Example transformations:
  "73" → ["digit_7", "digit_3"]
  "A-45" → ["letter_a", "separator_dash", "digit_4", "digit_5"]
  "xiv" → ["letter_x", "letter_i", "letter_v"]
  "blank" → ["blank"]
"""

import os
import shutil
from pathlib import Path
from collections import Counter

def extract_characters(label):
    """
    Extract individual characters from labels and categorize them
    
    Args:
        label (str): Original label like "73", "A-45", "xiv", "blank"
    
    Returns:
        list: List of character categories like ["digit_7", "digit_3"]
    """
    characters = []
    
    # Handle blank special case
    if label.lower() == "blank":
        return ["blank"]
    
    # Process each character
    for char in label:
        if char.isdigit():
            characters.append(f"digit_{char}")
        elif char.isalpha():
            # Lowercase for consistency (roman numerals, letters)
            characters.append(f"letter_{char.lower()}")
        elif char == '-':
            characters.append("separator_dash")
        elif char == '_':
            characters.append("separator_underscore")
        elif char == '.':
            characters.append("separator_period")
        elif char == ' ':
            continue  # Skip spaces
        else:
            # Other characters
            characters.append(f"char_{char}")
    
    return characters


def reorganize_training_data(source_dir, dest_dir, dry_run=False):
    """
    Reorganize training data from page number classes to character classes
    
    Args:
        source_dir (Path): Source directory (corners/)
        dest_dir (Path): Destination directory (corners_digits/)
        dry_run (bool): If True, only print what would be done
    """
    source_dir = Path(source_dir)
    dest_dir = Path(dest_dir)
    
    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        return False
    
    # Statistics
    stats = {
        'total_classes_original': 0,
        'total_images_processed': 0,
        'total_images_created': 0,
        'character_classes': Counter(),
        'errors': []
    }
    
    print("=" * 70)
    print("TRAINING DATA REORGANIZATION - Page Numbers → Digits/Characters")
    print("=" * 70)
    print(f"\n📂 Source: {source_dir}")
    print(f"📂 Destination: {dest_dir}")
    print(f"🔍 Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify files)'}")
    print("\n" + "-" * 70)
    
    # Create destination directory if not dry run
    if not dry_run:
        dest_dir.mkdir(exist_ok=True)
        print(f"✅ Created destination directory: {dest_dir}\n")
    
    # Process each class directory
    for class_dir in sorted(source_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        
        label = class_dir.name
        stats['total_classes_original'] += 1
        
        # Get all images in this class
        images = list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.png"))
        
        if not images:
            print(f"⚠️  {label}: No images found")
            continue
        
        stats['total_images_processed'] += len(images)
        
        # Extract character categories
        characters = extract_characters(label)
        
        if not characters:
            error_msg = f"Could not extract characters from '{label}'"
            stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            continue
        
        # Print what we're doing
        char_str = ", ".join(characters)
        print(f"📝 {label:15} → {char_str:30} ({len(images)} images)")
        
        # Copy each image to each character class folder
        for image_path in images:
            for char_class in characters:
                # Count this character class
                stats['character_classes'][char_class] += 1
                
                if dry_run:
                    continue
                
                # Create character class directory
                char_dir = dest_dir / char_class
                char_dir.mkdir(exist_ok=True)
                
                # Create unique filename
                # Format: {char_class}_{original_label}_{original_filename}
                new_filename = f"{char_class}_from_{label}_{image_path.name}"
                dest_path = char_dir / new_filename
                
                try:
                    # Copy image
                    shutil.copy2(image_path, dest_path)
                    stats['total_images_created'] += 1
                except Exception as e:
                    error_msg = f"Failed to copy {image_path.name} to {char_class}: {e}"
                    stats['errors'].append(error_msg)
                    print(f"  ❌ {error_msg}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("REORGANIZATION SUMMARY")
    print("=" * 70)
    print(f"\n📊 Statistics:")
    print(f"   Original classes: {stats['total_classes_original']}")
    print(f"   Images processed: {stats['total_images_processed']}")
    print(f"   Images created:   {stats['total_images_created']}")
    
    print(f"\n🔤 Character Classes ({len(stats['character_classes'])}):")
    for char_class, count in sorted(stats['character_classes'].items()):
        print(f"   {char_class:25} : {count:4} samples")
    
    if stats['errors']:
        print(f"\n⚠️  Errors ({len(stats['errors'])}):")
        for error in stats['errors'][:10]:  # Show first 10
            print(f"   - {error}")
        if len(stats['errors']) > 10:
            print(f"   ... and {len(stats['errors']) - 10} more")
    
    print("\n" + "=" * 70)
    
    if dry_run:
        print("\n✅ DRY RUN COMPLETE - No files were modified")
        print("   To actually reorganize, run again with --live flag")
    else:
        print(f"\n✅ REORGANIZATION COMPLETE!")
        print(f"   New training data location: {dest_dir}")
        print(f"   Ready for training on {len(stats['character_classes'])} character classes")
    
    return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Reorganize training data from page numbers to digit/character level"
    )
    parser.add_argument(
        '--source',
        default='ml_training/manual_training_data/corners',
        help='Source directory (default: ml_training/manual_training_data/corners)'
    )
    parser.add_argument(
        '--dest',
        default='ml_training/manual_training_data/corners_digits',
        help='Destination directory (default: ml_training/manual_training_data/corners_digits)'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Actually perform reorganization (default is dry-run)'
    )
    
    args = parser.parse_args()
    
    # Run reorganization
    success = reorganize_training_data(
        source_dir=args.source,
        dest_dir=args.dest,
        dry_run=not args.live
    )
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()
