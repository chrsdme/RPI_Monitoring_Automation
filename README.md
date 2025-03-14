# Mushroom Tent Controller

A comprehensive control system for mushroom cultivation environments using a Raspberry Pi 3 B+.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)

## Overview

The Mushroom Tent Controller is a fully featured environmental control system designed for mushroom cultivation. It integrates multiple sensors (temperature, humidity, CO2) with relay-controlled components to create an ideal growing environment with automated management.

This system provides precise control over growing conditions, data visualization, and remote monitoring capabilities, all accessible through an intuitive web interface.

## Features

- **Environmental Monitoring**
  - Temperature and humidity monitoring via dual DHT22 sensors
  - CO2 level monitoring via SCD40 sensor
  - Real-time data visualization with configurable graphs
  - Historical data logging and export

- **Automated Control**
  - Configurable relay control for various equipment:
    - Grow lights & UV lights
    - Humidifiers
    - Heaters
    - Ventilation fans (tub and in/out)
  - Automated schedules and environmental triggers
  - Manual override capabilities

- **Profile Management**
  - Save, load, and export cultivation profiles
  - Preconfigured profiles for different growing stages (colonization, fruiting)
  - Easily adjustable parameters for each growth stage

- **Network Integration**
  - WiFi configuration with multiple network support
  - MQTT integration for IoT connectivity
  - Smart outlet (Tapo P100) integration

- **System Management**
  - Web-based configuration interface (responsive for all devices)
  - Remote debugging and logging
  - OTA (Over-the-Air) updates
  - System monitoring and diagnostics

## Hardware Requirements

- Raspberry Pi 3 B+ (running Raspbian OS x64 without desktop)
- SCD40 CO2 sensor
- 2× DHT22 temperature/humidity sensors
- SSD1306 0.96" mini OLED display
- 3.3V mini cooling fan
- 8-channel relay module
- Various growing equipment (lights, fans, humidifiers, etc.)
- Power supply

## Installation

Please refer to the [Installation Guide](INSTALL.md) for detailed setup instructions.

## Configuration

The system can be configured through the web interface. Core settings include:

- Sensor configurations and reading intervals
- Relay assignments and schedules
- Environmental thresholds
- Network settings and WiFi connections
- Profile management

## Documentation

- [User Manual](docs/USER_MANUAL.md) - Complete guide to using the system
- [API Documentation](docs/API_DOCUMENTATION.md) - Details on all available API endpoints
- [Hardware Setup](docs/HARDWARE_SETUP.md) - Instructions for hardware connections
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Development

### Prerequisites

- VSCode with PlatformIO extension
- Basic knowledge of Python and JavaScript
- Understanding of GPIO pins on Raspberry Pi

### Building

```bash
# Clone the repository
git clone https://github.com/yourusername/mushroom-tent-controller.git

# Open the project in VSCode with PlatformIO

# Build the project
pio run

# Upload to Raspberry Pi
pio run --target upload
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the various open-source libraries that made this project possible
- Inspired by the mushroom cultivation community and their dedication to precision growing

## Release Notes - v1.0.0

Initial release of the Mushroom Tent Controller with all core features implemented:

- Complete sensor integration
- Relay control system
- Web interface
- Profile management
- Network connectivity

Known issues:
- None at this time

Planned features for future releases:
- Mobile application
- Additional sensor types
- Enhanced data analytics
- Cloud integration
