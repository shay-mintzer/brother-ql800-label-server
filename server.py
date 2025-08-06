import logging
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import subprocess
import threading
import time
import requests
import os
import platform

from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends import backend_factory, available_backends
from brother_ql.backends.helpers import send

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

PRINTER_USB = "usb://0x04f9:0x209b"
MODEL = "QL-800"
LABEL_SIZE = "62"  # Changed back to 62mm continuous labels

def get_system_fonts():
    """Get appropriate font paths based on the operating system"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        elegant_fonts = [
            "/System/Library/Fonts/Avenir.ttc",
            "/System/Library/Fonts/Futura.ttc", 
            "/System/Library/Fonts/Optima.ttc",
            "/System/Library/Fonts/Palatino.ttc",
            "/System/Library/Fonts/Supplemental/Baskerville.ttc",
            "/System/Library/Fonts/Supplemental/Garamond.ttc",
            "/Library/Fonts/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Hoefler Text.ttc"
        ]
        date_fonts = [
            "/System/Library/Fonts/Helvetica.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Avenir.ttc"
        ]
    else:  # Linux/Raspberry Pi
        elegant_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
        ]
        date_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
    
    return elegant_fonts, date_fonts

def start_ngrok():
    """Start ngrok tunnel for the Flask server"""
    try:
        # Kill any existing ngrok processes
        subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
        time.sleep(2)
        
        # Start ngrok tunnel
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", "5000", "--log", "stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for ngrok to start
        time.sleep(3)
        
        # Get the public URL
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            tunnels = response.json()
            if tunnels["tunnels"]:
                public_url = tunnels["tunnels"][0]["public_url"]
                logging.info(f"🌍 Ngrok tunnel active: {public_url}")
                logging.info(f"🖨️ Print endpoint: {public_url}/print")
                logging.info(f"📱 Devices endpoint: {public_url}/devices")
            else:
                logging.warning("Ngrok started but no tunnels found")
        except Exception as e:
            logging.warning(f"Could not get ngrok URL: {e}")
            
    except Exception as e:
        logging.error(f"Failed to start ngrok: {e}")
        system = platform.system().lower()
        if system == "darwin":
            logging.info("Install ngrok with: brew install ngrok")
        else:
            logging.info("Install ngrok with: sudo apt install ngrok")

def create_label_image(text: str):
    # 62mm continuous labels are 696 pixels wide
    label_width = 696
    label_height = 271
    
    img = Image.new("RGB", (label_width, label_height), "white")
    draw = ImageDraw.Draw(img)
    
    # Date formatting without seconds
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Get cross-platform fonts
    elegant_fonts, date_fonts = get_system_fonts()
    
    # Draw date in top-left corner with clean font
    date_font_size = 40
    date_font = None
    
    try:
        for font_path in date_fonts:
            try:
                if os.path.exists(font_path):
                    date_font = ImageFont.truetype(font_path, date_font_size)
                    break
            except:
                continue
        if date_font is None:
            date_font = ImageFont.load_default()
    except:
        date_font = ImageFont.load_default()
    
    # Draw date in top-left corner with minimal margin
    margin = 4
    draw.text((margin, margin), now_str, font=date_font, fill="black")
    
    # Calculate available space for main text
    date_bbox = draw.textbbox((margin, margin), now_str, font=date_font)
    date_height = date_bbox[3] - date_bbox[1]
    
    # Main text area
    text_start_y = date_height + margin + 8
    available_height = label_height - text_start_y - margin
    available_width = label_width - (margin * 2)
    
    # Smart text splitting based on character count threshold
    SINGLE_LINE_THRESHOLD = 25  # Characters - adjust based on testing
    
    # Prepare text - split into lines if too long
    if len(text) > SINGLE_LINE_THRESHOLD:
        # Smart splitting: try to split at word boundaries
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if len(test_line) <= SINGLE_LINE_THRESHOLD:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
            
        display_text = "\n".join(lines)
    else:
        display_text = text
    
    # Find optimal font size using elegant fonts
    max_font_size = 140
    min_font_size = 32
    
    font_size = max_font_size
    main_font = None
    
    while font_size >= min_font_size:
        try:
            # Try to load elegant fonts
            font_loaded = False
            for font_path in elegant_fonts:
                try:
                    if os.path.exists(font_path):
                        main_font = ImageFont.truetype(font_path, font_size)
                        font_loaded = True
                        break
                except:
                    continue
            
            # Fallback to regular fonts if elegant fonts fail
            if not font_loaded:
                for font_path in date_fonts:
                    try:
                        if os.path.exists(font_path):
                            main_font = ImageFont.truetype(font_path, font_size)
                            font_loaded = True
                            break
                    except:
                        continue
            
            if not font_loaded:
                main_font = ImageFont.load_default()
        except:
            main_font = ImageFont.load_default()
        
        # Check if text fits within available dimensions
        bbox = draw.textbbox((0, 0), display_text, font=main_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Use 95% of available space for maximum utilization
        max_width = available_width * 0.95
        max_height = available_height * 0.95
        
        if text_width <= max_width and text_height <= max_height:
            break
            
        font_size -= 2
    
    # Center the main text perfectly
    bbox = draw.textbbox((0, 0), display_text, font=main_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Perfect horizontal centering
    x = (label_width - text_width) // 2
    
    # Perfect vertical centering in available area
    y = text_start_y + (available_height - text_height) // 2
    
    # Draw the elegant main text
    draw.text((x, y), display_text, font=main_font, fill="black")
    
    return img

def get_available_devices():
    """List all available Brother QL printers"""
    try:
        backend_info = backend_factory("pyusb")
        list_devices = backend_info['list_available_devices']
        devices = list_devices()
        return [device['identifier'] for device in devices]
    except Exception as e:
        logging.error(f"Error listing devices: {e}")
        return []

def check_printer_connection():
    """Check if the specified printer is connected and available"""
    try:
        import usb.core
        # Check if any Brother devices are connected
        brother_devices = usb.core.find(find_all=True, idVendor=0x04f9)
        brother_device_list = list(brother_devices)
        
        if not brother_device_list:
            return {
                "connected": False,
                "message": "No Brother devices found. Please check if the printer is connected and powered on.",
                "available_devices": []
            }
        
        # Check if our specific printer is connected
        target_vendor = 0x04f9
        target_product = 0x209b  # Changed from 0x209e to match PRINTER_USB
        
        for device in brother_device_list:
            if device.idVendor == target_vendor and device.idProduct == target_product:
                return {
                    "connected": True,
                    "message": f"Printer found: Vendor 0x{device.idVendor:04x}, Product 0x{device.idProduct:04x}",
                    "available_devices": [f"usb://0x{device.idVendor:04x}:0x{device.idProduct:04x}"]
                }
        
        # If we found Brother devices but not our specific one
        available_devices = [f"usb://0x{device.idVendor:04x}:0x{device.idProduct:04x}" for device in brother_device_list]
        return {
            "connected": False,
            "message": f"Brother devices found but not the expected one. Available: {available_devices}",
            "available_devices": available_devices
        }
        
    except Exception as e:
        return {
            "connected": False,
            "message": f"Error checking printer connection: {str(e)}",
            "available_devices": []
        }

@app.route("/devices", methods=["GET"])
def list_devices():
    """List available Brother QL printers"""
    devices = get_available_devices()
    connection_status = check_printer_connection()
    return jsonify({
        "devices": devices, 
        "available_backends": available_backends,
        "connection_status": connection_status
    })

@app.route("/print", methods=["POST"])
def print_label():
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' in request body"}), 400

        # Apply title case formatting: "apple juice" -> "Apple Juice"
        text = data['text'].title()
        logging.info(f"Creating label for: {text}")

        # Check printer connection first
        connection_status = check_printer_connection()
        if not connection_status["connected"]:
            return jsonify({
                "error": "Printer not connected", 
                "details": connection_status["message"]
            }), 503

        # Step 1: Create the image
        img = create_label_image(text)

        # Step 2: Convert image to printer instructions
        qlr = BrotherQLRaster(MODEL)
        qlr.exception_on_warning = True
        instructions = convert(
            qlr=qlr,
            images=[img],
            label=LABEL_SIZE,
            rotate='0',  # Changed from '90' to '0' for proper orientation
            threshold=70.0,
            dither=False,
            compress=True,
            red=True,  # CRITICAL: Set to True for DK-22251 red/black tape
            dpi_600=False
        )

        # Step 3: Send to printer using pyusb
        try:
            send(
                instructions=instructions, 
                printer_identifier=PRINTER_USB, 
                backend_identifier="pyusb", 
                blocking=False  # Changed to False to avoid USB status warnings
            )
        except Exception as e:
            logging.error(f"Printer error: {e}")
            return jsonify({"error": f"Printer error: {str(e)}"}), 500

        logging.info("Label printed successfully.")
        return jsonify({"status": "printed", "text": text}), 200

    except Exception as e:
        logging.exception("Error during printing.")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Start ngrok in a separate thread
    logging.info("🚀 Starting label printer server...")
    ngrok_thread = threading.Thread(target=start_ngrok)
    ngrok_thread.daemon = True  # Allow main thread to exit even if ngrok fails
    ngrok_thread.start()

    # Give ngrok a moment to start before starting Flask
    time.sleep(1)
    
    logging.info("🖨️ Label printer server running on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)
