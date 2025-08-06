#!/usr/bin/env python3
"""
🚪 SHOES STAY OUTSIDE Sign Printer
Prints a professional "SHOES STAY OUTSIDE" sign with shoe icon and arrow
"""

import logging
from PIL import Image, ImageDraw, ImageFont
import os
import platform

from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send

# Configure logging
logging.basicConfig(level=logging.INFO)

# Printer configuration
PRINTER_USB = "usb://0x04f9:0x209b"
MODEL = "QL-800"
LABEL_SIZE = "62"

def get_system_fonts():
    """Get appropriate font paths based on the operating system"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        fonts = [
            "/System/Library/Fonts/Helvetica.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Avenir.ttc"
        ]
    else:  # Linux/Raspberry Pi
        fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
    
    return fonts

def draw_shoe_icon(draw, x, y, size=80):
    """Draw a simple sneaker icon"""
    # Shoe body (main part)
    shoe_body = [
        (x, y + size//2),
        (x + size//4, y + size//3),
        (x + size*3//4, y + size//3),
        (x + size, y + size//2),
        (x + size, y + size*3//4),
        (x + size//8, y + size*3//4)
    ]
    draw.polygon(shoe_body, fill="black")
    
    # Shoe sole
    sole = [
        (x, y + size*3//4),
        (x + size, y + size*3//4),
        (x + size + size//8, y + size),
        (x - size//8, y + size)
    ]
    draw.polygon(sole, fill="black")
    
    # Laces (white dots)
    lace_positions = [
        (x + size//3, y + size//2),
        (x + size//2, y + size//2 - 8),
        (x + size*2//3, y + size//2),
        (x + size*3//4, y + size//2 - 8)
    ]
    
    for lace_x, lace_y in lace_positions:
        draw.ellipse([lace_x-3, lace_y-3, lace_x+3, lace_y+3], fill="white")
    
    # Shoe stripe (white line)
    draw.line([(x + size//4, y + size*2//3), (x + size*3//4, y + size*2//3)], 
              fill="white", width=3)

def draw_arrow(draw, start_x, start_y, end_x, end_y, width=8):
    """Draw a red arrow pointing down"""
    # Arrow shaft
    shaft_left = start_x - width//2
    shaft_right = start_x + width//2
    draw.rectangle([shaft_left, start_y, shaft_right, end_y - 20], fill="red")
    
    # Arrow head (triangle)
    arrow_head = [
        (start_x, end_y),  # tip
        (start_x - width*2, end_y - 25),  # left
        (start_x + width*2, end_y - 25)   # right
    ]
    draw.polygon(arrow_head, fill="red")

def create_shoes_sign():
    """Create the 'SHOES STAY OUTSIDE' sign"""
    # Label dimensions for 62mm continuous
    label_width = 696
    label_height = 271
    
    # Create white background with black border
    img = Image.new("RGB", (label_width, label_height), "white")
    draw = ImageDraw.Draw(img)
    
    # Draw black border
    border_width = 4
    draw.rectangle([0, 0, label_width-1, label_height-1], 
                   outline="black", width=border_width)
    
    # Get fonts
    fonts = get_system_fonts()
    
    # Load fonts
    try:
        title_font = None
        subtitle_font = None
        
        for font_path in fonts:
            try:
                if os.path.exists(font_path):
                    title_font = ImageFont.truetype(font_path, 48)
                    subtitle_font = ImageFont.truetype(font_path, 56)
                    break
            except:
                continue
        
        if title_font is None:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Draw shoe icon (top center)
    shoe_x = label_width//2 - 40
    shoe_y = 20
    draw_shoe_icon(draw, shoe_x, shoe_y, size=80)
    
    # Draw arrow pointing down from shoe
    arrow_start_x = label_width//2
    arrow_start_y = shoe_y + 90
    arrow_end_y = shoe_y + 140
    draw_arrow(draw, arrow_start_x, arrow_start_y, arrow_start_x, arrow_end_y)
    
    # Draw "SHOES STAY" text (black)
    shoes_text = "SHOES STAY"
    shoes_bbox = draw.textbbox((0, 0), shoes_text, font=title_font)
    shoes_width = shoes_bbox[2] - shoes_bbox[0]
    shoes_x = (label_width - shoes_width) // 2
    shoes_y = 160
    draw.text((shoes_x, shoes_y), shoes_text, font=title_font, fill="black")
    
    # Draw "OUTSIDE" text (red)
    outside_text = "OUTSIDE"
    outside_bbox = draw.textbbox((0, 0), outside_text, font=subtitle_font)
    outside_width = outside_bbox[2] - outside_bbox[0]
    outside_x = (label_width - outside_width) // 2
    outside_y = 210
    draw.text((outside_x, outside_y), outside_text, font=subtitle_font, fill="red")
    
    return img

def print_shoes_sign():
    """Print the shoes sign to Brother QL-800"""
    try:
        logging.info("🚪 Creating SHOES STAY OUTSIDE sign...")
        
        # Create the image
        img = create_shoes_sign()
        
        # Save a copy for verification
        img.save("shoes_sign_preview.png")
        logging.info("📸 Preview saved as 'shoes_sign_preview.png'")
        
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
        
        logging.info("✅ SHOES STAY OUTSIDE sign printed successfully!")
        logging.info("🏠 Perfect for your entryway!")
        
    except Exception as e:
        logging.error(f"❌ Error printing sign: {e}")
        raise

if __name__ == "__main__":
    print("🚪 SHOES STAY OUTSIDE Sign Printer")
    print("=" * 40)
    print("This will print a professional entrance sign")
    print("Make sure your Brother QL-800 is connected!")
    print("=" * 40)
    
    try:
        print_shoes_sign()
    except Exception as e:
        print(f"\n❌ Failed to print: {e}")
        print("\nTroubleshooting:")
        print("1. Check printer is connected and powered on")
        print("2. Ensure DK-22251 tape is loaded")
        print("3. Make sure printer cover is closed")
        print("4. Run: python -c \"import usb.core; print(usb.core.find(idVendor=0x04f9, idProduct=0x209b))\"") 