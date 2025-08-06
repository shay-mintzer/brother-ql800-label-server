#!/usr/bin/env python3
"""
🔄 Rotate & Print - Simple Image Printer
Rotates image 90 degrees and prints it as one label covering maximum area
"""

import logging
from PIL import Image
import os

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

def rotate_and_fit_image(image_path):
    """Rotate image 90 degrees and fit to label size"""
    try:
        # Load the original image
        img = Image.open(image_path)
        logging.info(f"📷 Loaded image: {img.size[0]}x{img.size[1]} pixels")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Rotate 90 degrees
        img = img.rotate(90, expand=True)
        logging.info(f"🔄 Rotated 90°: {img.size[0]}x{img.size[1]} pixels")
        
        # Calculate the best fit while maintaining aspect ratio
        img_width, img_height = img.size
        
        # Calculate scaling factors for both dimensions
        width_scale = LABEL_WIDTH / img_width
        height_scale = LABEL_HEIGHT / img_height
        
        # Use the smaller scale to ensure image fits entirely
        scale = min(width_scale, height_scale)
        
        # Calculate new dimensions
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        logging.info(f"📐 Resized to: {new_width}x{new_height} pixels")
        
        # Create label-sized canvas with white background
        label_img = Image.new('RGB', (LABEL_WIDTH, LABEL_HEIGHT), 'white')
        
        # Center the image on the label
        x_offset = (LABEL_WIDTH - new_width) // 2
        y_offset = (LABEL_HEIGHT - new_height) // 2
        
        label_img.paste(img, (x_offset, y_offset))
        logging.info(f"📋 Centered on label: {LABEL_WIDTH}x{LABEL_HEIGHT} pixels")
        
        return label_img
        
    except Exception as e:
        logging.error(f"❌ Error processing image: {e}")
        return None

def print_rotated_image(image_path):
    """Print the rotated and fitted image"""
    try:
        logging.info("🖼️ Processing image for maximum coverage...")
        
        # Process the image
        img = rotate_and_fit_image(image_path)
        if img is None:
            return False
        
        # Save a preview
        img.save("rotated_max_preview.png")
        logging.info("📸 Preview saved as 'rotated_max_preview.png'")
        
        # Convert to printer instructions
        qlr = BrotherQLRaster(MODEL)
        qlr.exception_on_warning = True
        
        instructions = convert(
            qlr=qlr,
            images=[img],
            label=LABEL_SIZE,
            rotate='0',
            threshold=70.0,
            dither=False,
            compress=True,
            red=True,  # For DK-22251 red/black tape
            dpi_600=False
        )
        
        # Send to printer
        logging.info("🖨️ Sending to printer...")
        send(
            instructions=instructions,
            printer_identifier=PRINTER_USB,
            backend_identifier="pyusb",
            blocking=False
        )
        
        logging.info("✅ Image printed successfully!")
        logging.info("🎯 Maximum coverage achieved!")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error printing: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Rotate & Print - Maximum Coverage")
    print("=" * 40)
    
    # Use the takeYourShoes2 image
    image_path = "takeYourShoes2.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        print("Available files:")
        for f in os.listdir("."):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                print(f"  📄 {f}")
        exit(1)
    
    print(f"📷 Rotating and printing: {image_path}")
    print("🖨️ Make sure your Brother QL-800 is connected!")
    print("=" * 40)
    
    try:
        if print_rotated_image(image_path):
            print("\n🎉 Success! Image rotated and printed with maximum coverage!")
        else:
            print("\n❌ Failed to print image")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check printer is connected and powered on")
        print("2. Ensure labels are loaded correctly")
        print("3. Make sure printer cover is closed") 