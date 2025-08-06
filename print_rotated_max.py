#!/usr/bin/env python3
"""
📐 Fit & Print - No Rotation Image Printer
Keeps original orientation and fits image to label with width=696
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

# Label dimensions (62mm continuous - proportional for 1024x1536 image)
LABEL_WIDTH = 696
LABEL_HEIGHT = 1044  # Correct proportional height for 1024x1536 image

def fit_image_no_rotation(image_path):
    """Fit image to label size without rotation"""
    try:
        # Load the original image
        img = Image.open(image_path)
        logging.info(f"📷 Loaded image: {img.size[0]}x{img.size[1]} pixels")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # No rotation - keep original orientation
        logging.info("📐 Keeping original orientation (no rotation)")
        
        # Resize to exact label dimensions (proportional fit)
        img = img.resize((LABEL_WIDTH, LABEL_HEIGHT), Image.Resampling.LANCZOS)
        logging.info(f"📐 Resized to: {LABEL_WIDTH}x{LABEL_HEIGHT} pixels")
        logging.info(f"🎯 Perfect proportional fit!")
        
        return img
        
    except Exception as e:
        logging.error(f"❌ Error processing image: {e}")
        return None

def print_fitted_image(image_path):
    """Print the fitted image without rotation"""
    try:
        logging.info("🖼️ Processing image for maximum coverage...")
        
        # Process the image
        img = fit_image_no_rotation(image_path)
        if img is None:
            return False
        
        # Save a preview
        img.save("proportional_fit_preview.png")
        logging.info("📸 Preview saved as 'proportional_fit_preview.png'")
        
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
    print("📐 Proportional Fit - No Rotation")
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
    
    print(f"📷 Proportional fit (696x1044): {image_path}")
    print("🖨️ Make sure your Brother QL-800 is connected!")
    print("=" * 40)
    
    try:
        if print_fitted_image(image_path):
            print("\n🎉 Success! Image fitted proportionally and printed!")
        else:
            print("\n❌ Failed to print image")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check printer is connected and powered on")
        print("2. Ensure labels are loaded correctly")
        print("3. Make sure printer cover is closed") 