# Mushroom Tent Controller - User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
   - [Hardware Setup](#hardware-setup)
   - [Software Installation](#software-installation)
   - [Initial Configuration](#initial-configuration)
3. [Features and Usage](#features-and-usage)
   - [Dashboard](#dashboard)
   - [Profiles](#profiles)
   - [Settings](#settings)
   - [Network Configuration](#network-configuration)
   - [System Information](#system-information)
   - [Tapo Smart Plug Integration](#tapo-smart-plug-integration)
4. [Advanced Configuration](#advanced-configuration)
   - [Relay Automation](#relay-automation)
   - [Environmental Thresholds](#environmental-thresholds)
   - [Custom Profiles](#custom-profiles)
5. [Maintenance](#maintenance)
   - [Software Updates](#software-updates)
   - [Backup and Restore](#backup-and-restore)
   - [System Logs](#system-logs)
6. [Troubleshooting](#troubleshooting)
   - [Common Issues](#common-issues)
   - [Sensor Problems](#sensor-problems)
   - [Relay Problems](#relay-problems)
   - [Network Issues](#network-issues)
   - [System Reset](#system-reset)
7. [Technical Reference](#technical-reference)
   - [GPIO Pin Assignments](#gpio-pin-assignments)
   - [Default Configuration](#default-configuration)
   - [Performance Considerations](#performance-considerations)

## Introduction

The Mushroom Tent Controller is a comprehensive environmental control system designed specifically for mushroom cultivation. It provides precise monitoring and automated control of temperature, humidity, and CO2 levels to create optimal growing conditions for various mushroom species.

This system integrates multiple sensors with relay-controlled components through an intuitive web interface, allowing both automated environmental control and manual operation when needed. The controller is built on a Raspberry Pi 3 B+ platform, providing reliability and versatility.

### Key Features

- Real-time monitoring of temperature, humidity, and CO2 levels
- Automated control of growing environment based on configurable thresholds
- Customizable profiles for different growing stages (colonization, fruiting)
- Web-based interface accessible from any device
- Data logging and visualization
- Remote control and monitoring
- Integration with Tapo P100 smart plugs for additional control options

## Installation

### Hardware Setup

#### Required Components

- Raspberry Pi 3 B+ with power supply
- MicroSD card (8GB minimum, Class 10 recommended)
- SCD40 CO2 sensor
- 2× DHT22 temperature and humidity sensors
- SSD1306 0.96" OLED display
- 3.3V cooling fan
- 8-channel relay module
- Breadboard and jumper wires
- Optional: Case for Raspberry Pi

#### Wiring Diagram

Connect the components according to the following pin assignments:

**Sensor Connections:**
- SCD40 sensor:
  - SDA → GPIO2 (Pin 3)
  - SCL → GPIO3 (Pin 5)
  - VCC → 3.3V
  - GND → Ground

- OLED Display:
  - SDA → GPIO4 (Pin 7)
  - SCL → GPIO5 (Pin 9)
  - VCC → 3.3V
  - GND → Ground

- Upper DHT22 Sensor:
  - Data → GPIO17 (Pin 11)
  - VCC → 3.3V
  - GND → Ground

- Lower DHT22 Sensor:
  - Data → GPIO23 (Pin 16)
  - VCC → 3.3V
  - GND → Ground

- Cooling Fan:
  - Control → GPIO12 (Pin 32)
  - VCC → 3.3V
  - GND → Ground

**Relay Connections:**
- Relay 1 (Main PSU) → GPIO18 (Pin 12)
- Relay 2 (UV Light) → GPIO24 (Pin 18)
- Relay 3 (Grow Light) → GPIO25 (Pin 22)
- Relay 4 (Tub Fans) → GPIO6 (Pin 31)
- Relay 5-8 → Other available GPIO pins

![Wiring Diagram Reference](/img/wiring_diagram.png)

### Software Installation

#### Preparing the Raspberry Pi

1. Download and install the latest Raspbian OS x64 Lite (without desktop) to your microSD card using the Raspberry Pi Imager.

2. Enable SSH for headless setup:
   - Create an empty file named `ssh` in the boot partition of the SD card.
   - For Wi-Fi setup, create a `wpa_supplicant.conf` file in the boot partition with the following content:
     ```
     country=US
     ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
     update_config=1
     
     network={
         ssid="YOUR_WIFI_SSID"
         psk="YOUR_WIFI_PASSWORD"
     }
     ```

3. Insert the microSD card into the Raspberry Pi and power it on.

4. Connect to the Raspberry Pi via SSH:
   ```
   ssh pi@raspberrypi.local
   ```
   Default password: `raspberry`

5. Update the system:
   ```
   sudo apt update
   sudo apt upgrade -y
   ```

#### Installing Required Packages

Install the necessary dependencies:

```bash
sudo apt install -y git python3-pip python3-venv i2c-tools libgpiod2

# Enable I2C and SPI interfaces
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Create a Python virtual environment
mkdir -p ~/mushroom-controller
cd ~/mushroom-controller
python3 -m venv venv
source venv/bin/activate

# Install Python libraries
pip install fastapi uvicorn RPi.GPIO adafruit-circuitpython-ssd1306 adafruit-circuitpython-dht adafruit-circuitpython-scd4x paho-mqtt
```

#### Installing the Mushroom Tent Controller

Clone the repository and install the application:

```bash
git clone https://github.com/yourusername/mushroom-tent-controller.git
cd mushroom-tent-controller

# Copy configuration files
cp config/config.example.json config/config.json

# Set up the service
sudo cp systemd/mushroom-controller.service /etc/systemd/system/
sudo systemctl enable mushroom-controller.service
sudo systemctl start mushroom-controller.service
```

### Initial Configuration

After installation, you'll need to perform initial configuration through the web interface.

1. Access the web interface by navigating to `http://raspberrypi.local` in your web browser (or use the IP address of your Raspberry Pi).

2. When first accessing the system, you'll be prompted to create an administrator account:
   - Enter a username and password
   - Configure WiFi settings (if not done during installation)
   - Set your preferred hostname
   - Configure timezone settings

3. After completing the initial setup, you'll be redirected to the main dashboard.

## Features and Usage

### Dashboard

The dashboard is the main screen of the Mushroom Tent Controller. It provides a real-time overview of your growing environment.

#### Dashboard Components

- **Temperature Graph**: Shows temperature readings from all three sensors over time
- **Humidity Graph**: Shows humidity readings from all three sensors over time
- **Sensor Readings**: Current temperature, humidity, and CO2 levels with color-coded status indicators
- **Relay Controls**: On/off toggles for each relay with status indicators
- **Clear Graph Button**: Clears the graph data without affecting stored logs
- **Light/Dark Mode Toggle**: Changes the interface theme

#### Interpreting the Display

- **Sensor Values**:
  - Green: Values are within ideal range
  - Orange: Values are approaching threshold limits
  - Red: Values are outside acceptable range

- **Indicators**:
  - Blinking dots next to graphs indicate data updates
  - Blinking dots next to sensor readings indicate sensor communication

- **Relay Toggles**:
  - Green: Relay is ON
  - Red: Relay is OFF
  - Manual toggles will override automatic control for the configured timeout period

### Profiles

The Profiles section allows you to save, load, and manage different configuration profiles for different growth stages.

#### Profile Management

- **Select Profile**: Choose from the dropdown menu (Test, Colonisation, Fruiting)
- **Load**: Load the selected profile settings into the system
- **Save**: Save current settings to the selected profile
- **Rename**: Change the name of the selected profile
- **Export ALL**: Export all profiles to a JSON file for backup
- **Import ALL**: Import profiles from a previously exported file

#### Profile Settings

- **Graphs**:
  - Graph Update Interval: How often the graphs are updated (seconds)
  - Graph Max Points: Maximum number of data points displayed

- **Sensors**:
  - DHT Sensor Interval: How often DHT sensors are read (seconds)
  - SCD40 Sensor Interval: How often the CO2 sensor is read (seconds)

- **Humidity Control**:
  - Low Threshold: Humidity level to trigger humidifier ON
  - High Threshold: Humidity level to trigger humidifier OFF
  - Time Settings: When humidity control should be active

- **Temperature Control**:
  - Low Threshold: Temperature to trigger heater ON
  - High Threshold: Temperature to trigger heater OFF

- **Fans Control**:
  - CO₂ Low Threshold: CO2 level to stop ventilation
  - CO₂ High Threshold: CO2 level to trigger ventilation
  - On Duration: How long fans run in each cycle (minutes)
  - Cycle Interval: How often fans cycle (minutes)
  - Time Settings: When fan control should be active

### Settings

The Settings section provides access to various system configuration options.

#### Log Settings

- **Log Level**: Select detail level (DEBUG, INFO, WARN, ERROR)
- **Max Log File Size**: Maximum size of log files (MB)
- **Log Listener Address**: Network address for remote logging (optional)
- **Log Flush Interval**: How often logs are written to storage (seconds)

#### Sensor Settings

- **Sensor Error Count**: Number of consecutive errors before triggering recovery

#### System Management

- **Sensor and Relay Testing**: Buttons to test hardware components
- **Reboot Scheduler**: Configure automatic weekly reboots
- **Reboot Now**: Immediately restart the system
- **Factory Reset**: Reset all settings to default (use with caution)

#### Power Management

- **Sleep Mode**: Configure power-saving options
  - No Sleep: System runs continuously
  - Modem Sleep: WiFi/Bluetooth off during specified hours
  - Light Sleep: WiFi/Bluetooth and CPU off during specified hours
  - Deep Sleep: Everything off except essential hardware
  - Hibernation: Everything off except RTC

#### Notifications

- **Enable Notifications**: Toggle notification system
- **Notification Type**: Select service (Telegram, Pushbullet)
- **Service-specific Settings**: Configure tokens, IDs, etc.

### Network Configuration

The Network section allows you to configure connectivity settings.

#### WiFi Settings

- **WiFi Networks**: Configure up to three WiFi networks for redundancy
- **WiFi Scanning**: Scan and select available networks
- **Network Credentials**: Store SSIDs and passwords

#### IP Configuration

- **DHCP**: Automatically obtain network settings (default)
- **Static IP**: Manually configure IP, netmask, gateway, and DNS

#### Network Services

- **mDNS Hostname**: Set the .local address for the device
- **Watchdog**: Configure minimum signal strength and check interval
- **MQTT**: Enable and configure MQTT for IoT integration

### System Information

The System page provides comprehensive information about the controller.

#### System Info

- **Network Information**: IP address, WiFi SSID, MAC address, signal strength
- **Resource Usage**: RAM, filesystem, and CPU usage with progress bars
- **System Status**: Uptime, temperature, and other metrics

#### OTA Updates

- **Current Versions**: Firmware and filesystem version information
- **Update Package**: Upload .pkg files for system updates
- **Update Progress**: Status of update process

#### System Logs

- **Live Log Display**: Real-time system logs
- **Automatic Scrolling**: Follows newest log entries

### Tapo Smart Plug Integration

The Tapo integration page allows you to control TP-Link Tapo P100 smart plugs.

#### Tapo Configuration

- **Account Settings**: Enter Tapo account credentials
- **Device Management**: Configure up to 3 smart plugs
- **Relay Mapping**: Associate smart plugs with specific relay functions

#### Tapo Control

- **Test Connection**: Verify communication with smart plugs
- **Manual Control**: Toggle smart plugs on/off independently
- **Status Display**: Current state of connected devices

## Advanced Configuration

### Relay Automation

The relay system includes sophisticated automation rules that can be customized for specific growing needs.

#### Relay Logic

- **Relay 1 (Main PSU)**: Powers on automatically when needed by dependent relays
- **Relay 2 & 3 (Lights)**: Alternating cycle within configured timeframe
- **Relay 4 (Tub Fans)**: Runs on schedule or when CO2 is below threshold
- **Relay 5 (Humidifiers)**: Runs when humidity is below threshold until it reaches high threshold
- **Relay 6 (Heater)**: Runs when temperature is below threshold until it reaches high threshold
- **Relay 7 (IN/OUT Fans)**: Runs on schedule or when CO2 exceeds high threshold

#### Dependencies

- Relays 2, 3, 4, 5, and 7 depend on Relay 1 (Main PSU)
- When a dependent relay needs to activate, it will automatically turn on Relay 1 first
- When all dependent relays are off, Relay 1 will automatically turn off

#### Override System

All relays can be manually controlled, which will override automatic operation for a configurable period (default: 5 minutes).

### Environmental Thresholds

Proper threshold configuration is critical for successful mushroom cultivation. The default profiles provide starting points, but you may need to adjust based on your specific mushroom species.

#### Colonization Stage (Typical Values)

- **Temperature**: 23-26°C (73-79°F)
- **Humidity**: 65-90%
- **CO2**: Higher levels are acceptable (1300-1800 ppm)
- **Light**: Minimal or none

#### Fruiting Stage (Typical Values)

- **Temperature**: 18-22°C (65-72°F)
- **Humidity**: 80-95%
- **CO2**: Lower levels required (800-1200 ppm)
- **Light**: Indirect light on a 12-hour cycle

### Custom Profiles

You can create custom profiles for specific species or growing techniques by saving modifications to the existing profiles or by importing custom profiles.

#### Creating a Custom Profile

1. Select an existing profile as a starting point
2. Modify the settings for your specific needs
3. Click "Save" to update the profile
4. Use "Rename" to give it a descriptive name

#### Profile Import/Export Format

Profiles are stored in JSON format. The structure includes:

```json
{
  "active": "ProfileName",
  "list": ["Profile1", "Profile2", "Profile3"],
  "data": {
    "Profile1": {
      "graph": { ... },
      "sensors": { ... },
      "relays": {
        "humidity": { ... },
        "temperature": { ... },
        "fans": { ... }
      }
    },
    "Profile2": { ... },
    "Profile3": { ... }
  }
}
```

## Maintenance

### Software Updates

The Mushroom Tent Controller supports Over-the-Air (OTA) updates to simplify maintenance.

#### Update Process

1. Navigate to the System page
2. Check your current firmware and filesystem versions
3. Download the latest package file (.pkg) from the project repository
4. Click "Choose File" and select the downloaded package
5. Check "Update & restart" if you want the system to automatically reboot after updating
6. Click "Upload PKG" to start the update process
7. Monitor the progress bar and status messages

#### Update Package Contents

Update packages may include:
- Firmware updates (core system functionality)
- Filesystem updates (web interface and configuration files)
- Database schema updates

### Backup and Restore

Regular backups are recommended to prevent data loss.

#### What to Back Up

- **Profiles**: Export all profiles from the Profiles page
- **Network Configuration**: Note your network settings
- **Custom Settings**: Document any custom configurations

#### Restore Process

In case of system failure or replacement:

1. Perform a fresh installation
2. Complete the initial setup
3. Import your backed-up profiles
4. Manually reconfigure network settings if needed

### System Logs

Logs are essential for troubleshooting and monitoring system performance.

#### Accessing Logs

- **Web Interface**: View logs on the System page
- **SSH Access**: Logs are stored in `/var/log/mushroom-controller/`

#### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General operational information
- **WARN**: Warning conditions that don't affect functionality
- **ERROR**: Error conditions that may require attention

#### Log Rotation

Logs are automatically rotated to prevent excessive storage usage. Old logs are compressed and retained according to the configured maximum log file size.

## Troubleshooting

### Common Issues

#### System Not Responding

1. Check if the Raspberry Pi is powered (power LED should be on)
2. Verify network connectivity (network LED should be blinking)
3. Try accessing the system via SSH: `ssh pi@raspberrypi.local`
4. Check system status: `sudo systemctl status mushroom-controller`
5. Restart the service: `sudo systemctl restart mushroom-controller`

#### Web Interface Not Loading

1. Verify you're using the correct address (hostname.local or IP address)
2. Check if the device is connected to the network
3. Verify that the service is running: `sudo systemctl status mushroom-controller`
4. Check firewall settings if applicable
5. Try clearing your browser cache or using a different browser

### Sensor Problems

#### Sensor Readings Not Updating

1. Check physical connections to sensors
2. Verify I2C and GPIO interfaces are enabled: `sudo raspi-config`
3. Test I2C devices: `sudo i2cdetect -y 1`
4. Check sensor logs for specific errors: System page → Logs
5. Run sensor diagnostics: Settings → Test Sensors

#### Inaccurate Readings

1. Verify sensor placement (away from heat sources, direct light, or drafts)
2. Check if sensors are clean and free from dust or moisture
3. Compare readings with a separate thermometer/hygrometer for calibration
4. Allow sufficient warmup time (especially for the CO2 sensor)

### Relay Problems

#### Relays Not Switching

1. Check physical connections to the relay module
2. Verify GPIO pin assignments in the configuration
3. Test relays manually: Settings → Test Relays
4. Check if Main PSU relay (Relay 1) is functioning (dependencies)
5. Verify relay triggers in logs (set log level to DEBUG)

#### Relays Switching Incorrectly

1. Check automation thresholds in the active profile
2. Verify time settings for scheduled operations
3. Check for manual overrides that might be active
4. Verify sensor readings that trigger automations
5. Check dependency configurations

### Network Issues

#### WiFi Connection Dropping

1. Check signal strength on the Network status page
2. Verify antenna placement and distance from router
3. Configure multiple WiFi networks for redundancy
4. Adjust the watchdog minimum RSSI value if needed
5. Check router settings (band, channel, security)

#### MQTT Not Connecting

1. Verify broker address and port are correct
2. Check username and password if authentication is required
3. Verify network connectivity to the broker
4. Check firewall settings (broker port typically 1883 or 8883)
5. Verify MQTT logs for specific errors

### System Reset

If the system becomes unresponsive or severely misconfigured, you may need to perform a reset.

#### Soft Reset

1. Navigate to Settings → Factory Reset
2. Confirm the reset operation
3. The system will revert to default settings and reboot

#### Hard Reset

If you cannot access the web interface:

1. Access the Raspberry Pi via SSH: `ssh pi@raspberrypi.local`
2. Navigate to the application directory: `cd ~/mushroom-controller`
3. Run the reset script: `sudo ./scripts/factory-reset.sh`
4. Wait for the system to reboot

#### Complete Reinstallation

As a last resort:

1. Back up any important data if possible
2. Reinstall the Raspbian OS on the SD card
3. Reinstall the Mushroom Tent Controller software
4. Reconfigure the system from scratch

## Technical Reference

### GPIO Pin Assignments

#### Default Assignments

| Component | GPIO | Pin | Notes |
|-----------|------|-----|-------|
| SCD40 SDA | 2 | 3 | I2C Data |
| SCD40 SCL | 3 | 5 | I2C Clock |
| Display SDA | 4 | 7 | I2C Data |
| Display SCL | 5 | 9 | I2C Clock |
| Upper DHT22 | 17 | 11 | Data pin |
| Lower DHT22 | 23 | 16 | Data pin |
| Cooling Fan | 12 | 32 | PWM capable |
| Relay 1 (Main PSU) | 18 | 12 | |
| Relay 2 (UV Light) | 24 | 18 | |
| Relay 3 (Grow Light) | 25 | 22 | |
| Relay 4 (Tub Fans) | 6 | 31 | |
| Relay 5-8 | Various | | Assigned dynamically |

#### Changing Pin Assignments

Pin assignments can be changed in the Settings page. After changing pins, a system reboot is required for changes to take effect.

### Default Configuration

#### System Defaults

| Setting | Default Value | Notes |
|---------|---------------|-------|
| Log Level | DEBUG | Higher detail during initial setup |
| Max Log Size | 5 MB | Adjust based on SD card size |
| Sensor Error Count | 3 | Attempts before recovery |
| Reboot Schedule | Sunday, 3:00 AM | Weekly maintenance |
| Sleep Mode | No Sleep | Full operation |

#### Profile Defaults

**Test Profile:**
- Graph Update: 10 seconds
- DHT Reading: 30 seconds
- SCD40 Reading: 60 seconds
- Humidity: 50-85%
- Temperature: 20-24°C
- CO2: 1100-1600 ppm

**Colonisation Profile:**
- Humidity: 65-90%
- Temperature: 23-26°C
- CO2: 1300-1800 ppm
- Lights: Disabled

**Fruiting Profile:**
- Humidity: 80-95%
- Temperature: 18-22°C
- CO2: 800-1200 ppm
- Lights: 12 hour cycle (8:00-20:00)

### Performance Considerations

#### Resource Usage

The Raspberry Pi 3 B+ has sufficient resources for normal operation, but consider the following:

- **CPU Usage**: Typically 10-20% during normal operation
- **Memory Usage**: ~200-300MB during normal operation
- **Storage**: Log rotation prevents excessive storage use
- **Network**: MQTT publishing frequency affects bandwidth usage

#### Optimization Tips

- Adjust sensor reading intervals based on need (longer intervals use less resources)
- Consider using Sleep modes during inactive periods
- Limit graph points to improve UI performance
- Use appropriate log levels (INFO for normal use, DEBUG only when troubleshooting)
- Schedule regular reboots for optimal performance