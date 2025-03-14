#!/bin/bash
# Installation script for Mushroom Tent Controller

echo "=== Mushroom Tent Controller Installation ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

# Install dependencies
echo "Installing dependencies..."
apt-get update
apt-get install -y python3-pip python3-venv git i2c-tools python3-smbus libgpiod2 hostapd dnsmasq

# Enable I2C
echo "Enabling I2C interface..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
  echo "dtparam=i2c_arm=on" >> /boot/config.txt
fi

# Create application directory
APP_DIR="/opt/mushroom-controller"
echo "Creating application directory at $APP_DIR..."
mkdir -p $APP_DIR

# Copy all files
echo "Copying application files..."
cp -r ./* $APP_DIR/

# Create Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt

# Create data directory
echo "Creating data directory..."
mkdir -p $APP_DIR/data

# Create service file
echo "Creating systemd service..."
cat > /etc/systemd/system/mushroom-controller.service << EOF
[Unit]
Description=Mushroom Tent Controller
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python3 $APP_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "Enabling service..."
systemctl enable mushroom-controller.service

echo "Starting service..."
systemctl start mushroom-controller.service

echo ""
echo "=== Installation Complete ==="
echo "The application should now be running."
echo "Please open a web browser and navigate to http://mushroom-controller.local/"
echo "If mDNS doesn't work, check the IP address of your Raspberry Pi."
echo ""