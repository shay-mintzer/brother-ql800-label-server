#!/usr/bin/env python3
"""
🖼️ Image Splitter for Brother QL-800 Labels
Splits any image into multiple labels that form a complete picture when lined up
"""

import logging
from PIL import Image, ImageDraw, ImageFont
import os
import math

from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send

# Configure logging
logging.basicConfig(level=logging.INFO)

# Printer configuration
PRINTER_USB = "usb://0x04f9:0x209b"
MODEL = "QL-800"
LABEL_SIZE = "62"

# Label dimensions (62mm continuous)
LABEL_WIDTH = 696
LABEL_HEIGHT = 271

def load_and_prepare_image(image_path, target_height=None, num_labels_desired=5):
    """Load image and prepare it for splitting"""
    try:
        # Load the original image
        img = Image.open(image_path)
        logging.info(f"📷 Loaded image: {img.size[0]}x{img.size[1]} pixels")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate target height (use label height if not specified)
        if target_height is None:
            target_height = LABEL_HEIGHT
        
        # Calculate minimum width to span desired number of labels
        min_width = LABEL_WIDTH * num_labels_desired
        
        # Calculate width maintaining aspect ratio
        aspect_ratio = img.size[0] / img.size[1]
        natural_width = int(target_height * aspect_ratio)
        
        # Use the larger of natural width or minimum width
        target_width = max(natural_width, min_width)
        
        # Resize image
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        logging.info(f"📐 Resized to: {img.size[0]}x{img.size[1]} pixels")
        logging.info(f"🎯 Will span {math.ceil(target_width / LABEL_WIDTH)} labels")
        
        return img
        
    except Exception as e:
        logging.error(f"❌ Error loading image: {e}")
        return None

def split_image_into_labels(img):
    """Split image into label-sized pieces"""
    img_width, img_height = img.size
    
    # Calculate how many labels we need
    num_labels = math.ceil(img_width / LABEL_WIDTH)
    logging.info(f"🔪 Splitting into {num_labels} labels")
    
    labels = []
    
    for i in range(num_labels):
        # Calculate the crop area for this label
        left = i * LABEL_WIDTH
        right = min(left + LABEL_WIDTH, img_width)
        
        # Create a new label-sized image with white background
        label_img = Image.new('RGB', (LABEL_WIDTH, LABEL_HEIGHT), 'white')
        
        # Crop the portion of the original image
        if left < img_width:
            crop_width = right - left
            cropped = img.crop((left, 0, right, img_height))
            
            # Center the cropped image vertically on the label
            y_offset = (LABEL_HEIGHT - img_height) // 2
            label_img.paste(cropped, (0, y_offset))
        
        labels.append(label_img)
        
        # Save preview
        preview_path = f"label_part_{i+1}_of_{num_labels}.png"
        label_img.save(preview_path)
        logging.info(f"💾 Saved preview: {preview_path}")
    
    return labels

def print_label_sequence(labels):
    """Print all labels in sequence"""
    total_labels = len(labels)
    
    for i, label_img in enumerate(labels, 1):
        try:
            logging.info(f"🖨️ Printing label {i} of {total_labels}...")
            
            # Convert to printer instructions
            qlr = BrotherQLRaster(MODEL)
            qlr.exception_on_warning = True
            
            instructions = convert(
                qlr=qlr,
                images=[label_img],
                label=LABEL_SIZE,
                rotate='0',
                threshold=70.0,
                dither=False,
                compress=True,
                red=True,  # For DK-22251 red/black tape
                dpi_600=False
            )
            
            # Send to printer
            send(
                instructions=instructions,
                printer_identifier=PRINTER_USB,
                backend_identifier="pyusb",
                blocking=False
            )
            
            logging.info(f"✅ Label {i}/{total_labels} printed!")
            
            # Brief pause between prints
            import time
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"❌ Error printing label {i}: {e}")
            raise

def split_and_print_image(image_path, num_labels=5):
    """Main function to split and print an image"""
    # Load and prepare the image
    img = load_and_prepare_image(image_path, num_labels_desired=num_labels)
    if img is None:
        return False
    
    # Split into labels
    labels = split_image_into_labels(img)
    
    # Print all labels
    print_label_sequence(labels)
    
    logging.info(f"🎉 Successfully printed {len(labels)} labels!")
    logging.info("📋 Line them up in order to see the complete image!")
    
    return True

if __name__ == "__main__":
    print("🖼️ Image Splitter for Brother QL-800 Labels")
    print("=" * 50)
    
    # You can change this to any image file
    image_path = "takeYourShoes2.png"  # Use the takeYourShoes2 image
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        print("Available files:")
        for f in os.listdir("."):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                print(f"  📄 {f}")
        exit(1)
    
    print(f"📷 Splitting image: {image_path}")
    print("🖨️ Make sure your Brother QL-800 is connected!")
    print("=" * 50)
    
    try:
        split_and_print_image(image_path)
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check printer is connected and powered on")
        print("2. Ensure labels are loaded correctly")
        print("3. Make sure printer cover is closed") 