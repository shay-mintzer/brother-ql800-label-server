# 🏷️ Brother QL-800 Label Printer Server

A Flask-based web server for printing labels on Brother QL-800 label printers with automatic ngrok tunneling for remote access.

## ✨ Features

- **🖨️ Direct USB Printing** - Works with Brother QL-800 and DK-22251 red/black tape
- **🌍 Remote Access** - Automatic ngrok tunnel for printing from anywhere
- **🎨 Smart Text Layout** - Elegant fonts with automatic text splitting and sizing
- **📅 Timestamped Labels** - Each label includes date/time in top-left corner
- **🔄 Dynamic Font Scaling** - Text automatically scales to use maximum label space
- **📱 REST API** - Simple JSON API for easy integration

## 🚀 Quick Start

### Prerequisites

```bash
# Install required packages
pip install flask pillow brother_ql requests

# Install ngrok (for remote access)
brew install ngrok
```

### Run the Server

```bash
python server.py
```

The server will:
- Start on `http://localhost:5000`
- Automatically create an ngrok tunnel for remote access
- Display the public URL in the console

## 📡 API Endpoints

### Print a Label
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"text": "Your label text here"}' \
  http://localhost:5000/print
```

### Check Printer Status
```bash
curl http://localhost:5000/devices
```

## 🎯 Label Features

- **Smart Text Splitting**: Long text (>25 chars) automatically splits into multiple lines
- **Elegant Fonts**: Uses beautiful fonts like Avenir, Futura, and Optima
- **Perfect Centering**: Text is perfectly centered both horizontally and vertically
- **Date Integration**: Small timestamp in top-left corner (YYYY-MM-DD HH:MM)
- **Maximum Space Usage**: Text scales to use 95% of available label space

## 🖨️ Printer Setup

1. **Connect** Brother QL-800 via USB
2. **Load** DK-22251 red/black continuous tape (62mm)
3. **Disable** Editor Lite mode (hold button until LED turns off)
4. **Power on** and ensure cover is closed

## 📝 Example Usage

```python
import requests

# Print a simple label
response = requests.post('http://localhost:5000/print', 
                        json={'text': 'Hello World!'})

# Print with automatic line splitting
response = requests.post('http://localhost:5000/print', 
                        json={'text': 'This is a longer message that will split across multiple lines'})
```

## 🛠️ Technical Details

- **Label Size**: 62mm continuous (696x271 pixels)
- **Font Scaling**: 32pt - 140pt (dynamic)
- **Text Threshold**: 25 characters for line splitting
- **Backends**: pyusb, network, linux_kernel
- **Image Format**: RGB with black text on white background

## 🌐 Remote Printing

With ngrok integration, you can:
- Print from your phone using the public URL
- Integrate with webhooks and automation
- Access from anywhere with internet connection
- Share the URL with team members

## 🔧 Troubleshooting

**Red Light Flashing:**
- Check if DK-22251 tape is loaded
- Ensure `red=True` setting for red/black tape
- Verify printer cover is closed

**Connection Issues:**
- Confirm Brother QL-800 is connected via USB
- Check that Editor Lite mode is disabled
- Verify printer is powered on

**Font Issues:**
- Server falls back gracefully to system fonts
- Works on macOS, Linux, and Windows

## 📊 Project Structure

```
labels/
├── server.py          # Main Flask server with ngrok
├── print.log          # Server logs
├── start_ngrok.sh     # Ngrok startup script
└── README.md          # This file
```

## 🎨 Customization

You can modify:
- **Fonts**: Edit `elegant_fonts` list in `create_label_image()`
- **Text Threshold**: Change `SINGLE_LINE_THRESHOLD` value
- **Label Size**: Modify `LABEL_SIZE` for different tape types
- **Margins**: Adjust `margin` values for spacing

## 📱 Integration Examples

**iOS Shortcuts**: Create a shortcut that sends text to your ngrok URL
**IFTTT/Zapier**: Trigger label printing from various events
**Home Assistant**: Print labels for organization and labeling
**Inventory Systems**: Generate labels for products and equipment

## 🏆 Perfect For

- Home organization and labeling
- Small business inventory
- Event name tags and labeling
- Cable management
- Food storage labels
- Remote printing needs

---

Made with ❤️ for seamless label printing anywhere! 