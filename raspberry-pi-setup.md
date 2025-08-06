# 🍓 Raspberry Pi Setup Guide for Brother QL-800 Label Printer

## 🚀 Quick Setup Commands

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y

# Install system dependencies for USB and fonts
sudo apt install libusb-1.0-0-dev udev fonts-liberation fonts-dejavu-core -y

# Install ngrok
sudo apt install snapd -y
sudo snap install ngrok

# Clone the repository
git clone https://github.com/shay-mintzer/brother-ql800-label-server.git
cd brother-ql800-label-server

# Create virtual environment
python3 -m venv label-printer-env
source label-printer-env/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Set up USB permissions for the printer
sudo usermod -a -G dialout $USER
sudo usermod -a -G lp $USER

# Create udev rule for Brother QL-800
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04f9", ATTR{idProduct}=="209b", MODE="0666", GROUP="lp"' | sudo tee /etc/udev/rules.d/99-brother-ql800.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Reboot to apply all changes
sudo reboot
```

## 🔧 Post-Reboot Setup

```bash
# Navigate to project and activate environment
cd brother-ql800-label-server
source label-printer-env/bin/activate

# Test the setup
python server.py
```

## 🖨️ Printer Connection Checklist

1. **Physical Connection**:
   - Connect Brother QL-800 via USB
   - Power on the printer
   - Load DK-22251 red/black tape

2. **Verify USB Detection**:
   ```bash
   lsusb | grep Brother
   # Should show: Bus XXX Device XXX: ID 04f9:209b Brother Industries, Ltd
   ```

3. **Test Printer Access**:
   ```bash
   # Check if printer is accessible
   python -c "import usb.core; print(usb.core.find(idVendor=0x04f9, idProduct=0x209b))"
   ```

## 🌐 Running as a Service (Optional)

Create a systemd service to auto-start the label printer server:

```bash
# Create service file
sudo tee /etc/systemd/system/label-printer.service > /dev/null <<EOF
[Unit]
Description=Brother QL-800 Label Printer Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/brother-ql800-label-server
Environment=PATH=/home/pi/brother-ql800-label-server/label-printer-env/bin
ExecStart=/home/pi/brother-ql800-label-server/label-printer-env/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable label-printer.service
sudo systemctl start label-printer.service

# Check status
sudo systemctl status label-printer.service
```

## 🔍 Troubleshooting

### Permission Issues
```bash
# If you get USB permission errors:
sudo chmod 666 /dev/bus/usb/XXX/XXX  # Replace XXX with actual bus/device numbers
```

### Font Issues
```bash
# Install additional fonts if needed:
sudo apt install fonts-liberation fonts-dejavu fonts-noto -y
```

### Ngrok Alternative (if snap doesn't work)
```bash
# Download ngrok manually:
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz
tar xvzf ngrok-v3-stable-linux-arm.tgz
sudo mv ngrok /usr/local/bin/
```

## 📱 Access Your Printer

Once running, your label printer will be available at:
- **Local Network**: `http://YOUR_PI_IP:5000`
- **Internet (via ngrok)**: Check the server logs for the public URL

## ✅ Verification Steps

1. **Check server status**: Server should start without errors
2. **Test devices endpoint**: `curl http://localhost:5000/devices`
3. **Print test label**: `curl -X POST -H "Content-Type: application/json" -d '{"text": "Raspberry Pi Test"}' http://localhost:5000/print`
4. **Verify ngrok tunnel**: Check server logs for public URL

## 🎯 Key Differences from macOS

- **Fonts**: Uses Liberation and DejaVu fonts instead of macOS system fonts
- **USB Permissions**: Requires udev rules and group membership
- **Package Manager**: Uses `apt` instead of `brew`
- **Service Management**: Uses systemd instead of launchd

Your Raspberry Pi is now a dedicated label printing station! 🎉 