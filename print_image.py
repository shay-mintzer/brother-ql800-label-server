#!/usr/bin/env python3
"""
🖼️ Generic Image Printer for Brother QL-800
Prints any image with smart orientation handling

Usage:
    python print_image.py <image_path> [horizontal|vertical]
    
Examples:
    python print_image.py photo.jpg horizontal
    python print_image.py portrait.png vertical
    python print_image.py image.png  # defaults to horizontal
"""

import sys
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

def print_usage():
    """Print usage instructions"""
    print("🖼️ Generic Image Printer for Brother QL-800")
    print("=" * 50)
    print("Usage:")
    print("  python print_image.py <image_path> [horizontal|vertical]")
    print("")
    print("Examples:")
    print("  python print_image.py photo.jpg horizontal")
    print("  python print_image.py portrait.png vertical") 
    print("  python print_image.py image.png  # defaults to horizontal")
    print("")
    print("Modes:")
    print("  horizontal: Landscape orientation, height=696, width calculated → (width, 696)")
    print("  vertical:   Portrait orientation, width=696, height calculated → (696, height)")

def process_image(image_path, orientation="horizontal"):
    """Process image with smart orientation handling"""
    try:
        # Load the original image
        img = Image.open(image_path)
        original_width, original_height = img.size
        logging.info(f"📷 Loaded image: {original_width}x{original_height} pixels")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Determine current orientation
        is_currently_portrait = original_height > original_width
        is_currently_landscape = original_width > original_height
        
        if orientation == "vertical":
            # Want portrait orientation (height >= width)
            if is_currently_landscape:
                logging.info("🔄 Rotating landscape image 90° for vertical mode")
                img = img.rotate(90, expand=True)
            else:
                logging.info("📐 Keeping portrait orientation for vertical mode")
            
            # Set width=696, calculate proportional height
            target_width = 696
            img_width, img_height = img.size
            proportional_height = int((img_height * target_width) / img_width)
            final_size = (target_width, proportional_height)
            
        else:  # horizontal mode
            # Want landscape orientation (width >= height)  
            if is_currently_portrait:
                logging.info("🔄 Rotating portrait image 90° for horizontal mode")
                img = img.rotate(90, expand=True)
            else:
                logging.info("📐 Keeping landscape orientation for horizontal mode")
            
            # Set height=696, calculate proportional width
            target_height = 696
            img_width, img_height = img.size
            proportional_width = int((img_width * target_height) / img_height)
            final_size = (proportional_width, target_height)
        
        # Resize to final dimensions
        img = img.resize(final_size, Image.Resampling.LANCZOS)
        logging.info(f"📐 Final size: {final_size[0]}x{final_size[1]} pixels")
        
        if orientation == "vertical":
            logging.info(f"🎯 Mode: {orientation}, Result: (696, {final_size[1]})")
        else:
            logging.info(f"🎯 Mode: {orientation}, Result: ({final_size[0]}, 696)")
        
        return img
        
    except Exception as e:
        logging.error(f"❌ Error processing image: {e}")
        return None

def print_image(image_path, orientation="horizontal"):
    """Print the processed image"""
    try:
        logging.info(f"🖼️ Processing image in {orientation} mode...")
        
        # Process the image
        img = process_image(image_path, orientation)
        if img is None:
            return False
        
        # Save a preview
        preview_name = f"{orientation}_preview.png"
        img.save(preview_name)
        logging.info(f"📸 Preview saved as '{preview_name}'")
        
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
        logging.info(f"🎯 {orientation.title()} mode - Perfect fit!")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error printing: {e}")
        return False

def main():
    """Main function with command line argument handling"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    image_path = sys.argv[1]
    orientation = sys.argv[2] if len(sys.argv) > 2 else "horizontal"

    # Validate arguments
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        sys.exit(1)

    if orientation not in ["horizontal", "vertical"]:
        print(f"❌ Invalid orientation: {orientation}")
        print("   Valid options: horizontal, vertical")
        sys.exit(1)

    print(f"🖼️ Generic Image Printer - {orientation.title()} Mode")
    print("=" * 50)
    print(f"📷 Image: {image_path}")
    print(f"📐 Orientation: {orientation}")
    print("🖨️ Make sure your Brother QL-800 is connected!")
    print("=" * 50)

    try:
        if print_image(image_path, orientation):
            if orientation == "vertical":
                print(f"\n🎉 Success! Image printed in {orientation} mode!")
                print(f"📋 Result: (696, proportional_height)")
            else:
                print(f"\n🎉 Success! Image printed in {orientation} mode!")
                print(f"📋 Result: (proportional_width, 696)")
        else:
            print("\n❌ Failed to print image")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check printer is connected and powered on")
        print("2. Ensure labels are loaded correctly")
        print("3. Make sure printer cover is closed")

if __name__ == "__main__":
    main() 