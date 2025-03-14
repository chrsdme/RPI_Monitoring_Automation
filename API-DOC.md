# Mushroom Tent Controller - API Documentation

This document provides comprehensive details about all available API endpoints in the Mushroom Tent Controller application. The API follows RESTful principles and uses JSON for data exchange.

## Base URL

All API endpoints are relative to the base URL of your controller:

```
http://<your-controller-ip>/ or http://<hostname>.local/
```

## Authentication

All API endpoints require HTTP Basic Authentication. The default credentials are set during the initial setup, and can be changed in the settings.

```
Username: admin
Password: (your configured password)
```

## API Endpoints

### Sensors

#### Get All Sensor Data

Retrieves current readings from all sensors.

- **URL**: `/api/sensors`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "upperDHT": {
        "temperature": 23.4,
        "humidity": 84.5
      },
      "lowerDHT": {
        "temperature": 22.9,
        "humidity": 86.2
      },
      "scd40": {
        "temperature": 23.1,
        "humidity": 85.3,
        "co2": 1250
      }
    }
    ```

#### Get Specific Sensor Data

Retrieves current readings from a specific sensor.

- **URL**: `/api/sensors/:sensorType`
- **Method**: `GET`
- **URL Parameters**:
  - `sensorType`: `upperDHT`, `lowerDHT`, or `scd40`
- **Success Response**:
  - **Code**: 200
  - **Content** (example for scd40):
    ```json
    {
      "temperature": 23.1,
      "humidity": 85.3,
      "co2": 1250
    }
    ```

#### Get Sensor History

Retrieves historical sensor data for a specified time range.

- **URL**: `/api/sensors/history`
- **Method**: `GET`
- **Query Parameters**:
  - `sensor`: Sensor type (`upperDHT`, `lowerDHT`, `scd40`, or `all`)
  - `start`: Start timestamp (ISO format)
  - `end`: End timestamp (ISO format)
  - `interval`: Aggregation interval in seconds (optional)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "timestamps": ["2023-01-01T12:00:00", "2023-01-01T12:05:00", ...],
      "data": {
        "upperDHT": {
          "temperature": [23.4, 23.5, ...],
          "humidity": [84.5, 84.6, ...]
        },
        "lowerDHT": {
          "temperature": [22.9, 23.0, ...],
          "humidity": [86.2, 86.3, ...]
        },
        "scd40": {
          "temperature": [23.1, 23.2, ...],
          "humidity": [85.3, 85.4, ...],
          "co2": [1250, 1255, ...]
        }
      }
    }
    ```

#### Export Sensor Data

Exports sensor data in CSV format.

- **URL**: `/api/sensors/export`
- **Method**: `GET`
- **Query Parameters**:
  - `start`: Start timestamp (ISO format)
  - `end`: End timestamp (ISO format)
  - `format`: Export format (`csv` or `json`)
- **Success Response**:
  - **Code**: 200
  - **Content Type**: `text/csv` or `application/json`
  - **Content**: CSV or JSON formatted sensor data

### Relays

#### Get All Relay Status

Retrieves the current status of all relays.

- **URL**: `/api/relays`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "1": {"name": "Main PSU", "status": true, "pin": 18, "automatic": true},
      "2": {"name": "UV Light", "status": false, "pin": 24, "automatic": true},
      "3": {"name": "Grow Light", "status": true, "pin": 25, "automatic": true},
      "4": {"name": "Tub Fans", "status": false, "pin": 6, "automatic": true},
      "5": {"name": "Humidifiers", "status": false, "pin": 0, "automatic": true},
      "6": {"name": "Heater", "status": false, "pin": 0, "automatic": true},
      "7": {"name": "IN/OUT Fans", "status": true, "pin": 0, "automatic": true},
      "8": {"name": "Reserved", "status": false, "pin": 0, "automatic": true}
    }
    ```

#### Get Specific Relay Status

Retrieves the current status of a specific relay.

- **URL**: `/api/relays/:relayId`
- **Method**: `GET`
- **URL Parameters**:
  - `relayId`: Relay ID (1-8)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "name": "Grow Light",
      "status": true,
      "pin": 25,
      "automatic": true
    }
    ```

#### Control Relay

Sets the state of a specific relay.

- **URL**: `/api/relays/:relayId`
- **Method**: `POST`
- **URL Parameters**:
  - `relayId`: Relay ID (1-8)
- **Request Body**:
  ```json
  {
    "state": true,
    "override": true
  }
  ```
  - `state`: Boolean indicating desired relay state (true = ON, false = OFF)
  - `override`: Boolean indicating if this is a manual override
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "relayId": "3",
      "state": true,
      "message": "Relay state updated"
    }
    ```

#### Reset Relay Override

Resets a relay from manual override back to automatic control.

- **URL**: `/api/relays/:relayId/reset-override`
- **Method**: `POST`
- **URL Parameters**:
  - `relayId`: Relay ID (1-8)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "relayId": "3",
      "state": true,
      "message": "Relay reset to automatic control"
    }
    ```

### Profiles

#### Get All Profiles

Retrieves all available profiles.

- **URL**: `/api/profiles`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "active": "Test",
      "list": ["Test", "Colonisation", "Fruiting"],
      "data": {
        "Test": {
          "graph": {
            "updateInterval": 10,
            "maxPoints": 100
          },
          "sensors": {
            "dhtInterval": 30,
            "scdInterval": 60
          },
          "relays": {
            "humidity": {
              "lowThreshold": 50,
              "highThreshold": 85,
              "startTime": "00:00",
              "endTime": "23:59"
            },
            "temperature": {
              "lowThreshold": 20,
              "highThreshold": 24
            },
            "fans": {
              "co2LowThreshold": 1100,
              "co2HighThreshold": 1600,
              "onDuration": 10,
              "cycleInterval": 60,
              "startTime": "00:00",
              "endTime": "23:59"
            }
          }
        },
        "Colonisation": { ... },
        "Fruiting": { ... }
      }
    }
    ```

#### Get Specific Profile

Retrieves a specific profile by name.

- **URL**: `/api/profiles/:profileName`
- **Method**: `GET`
- **URL Parameters**:
  - `profileName`: Name of the profile
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "graph": {
        "updateInterval": 10,
        "maxPoints": 100
      },
      "sensors": {
        "dhtInterval": 30,
        "scdInterval": 60
      },
      "relays": {
        "humidity": {
          "lowThreshold": 50,
          "highThreshold": 85,
          "startTime": "00:00",
          "endTime": "23:59"
        },
        "temperature": {
          "lowThreshold": 20,
          "highThreshold": 24
        },
        "fans": {
          "co2LowThreshold": 1100,
          "co2HighThreshold": 1600,
          "onDuration": 10,
          "cycleInterval": 60,
          "startTime": "00:00",
          "endTime": "23:59"
        }
      }
    }
    ```

#### Create or Update Profile

Creates a new profile or updates an existing one.

- **URL**: `/api/profiles/:profileName`
- **Method**: `POST`
- **URL Parameters**:
  - `profileName`: Name of the profile
- **Request Body**: Profile data (see format in Get Specific Profile)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Profile saved successfully"
    }
    ```

#### Apply Profile

Applies a specific profile to the system.

- **URL**: `/api/profiles/:profileName/apply`
- **Method**: `POST`
- **URL Parameters**:
  - `profileName`: Name of the profile
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Profile applied successfully"
    }
    ```

#### Rename Profile

Renames an existing profile.

- **URL**: `/api/profiles/:profileName/rename`
- **Method**: `POST`
- **URL Parameters**:
  - `profileName`: Current name of the profile
- **Request Body**:
  ```json
  {
    "newName": "New Profile Name"
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Profile renamed successfully"
    }
    ```

#### Import Profiles

Imports profiles from a JSON object.

- **URL**: `/api/profiles/import`
- **Method**: `POST`
- **Request Body**: Complete profiles object (see format in Get All Profiles)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Profiles imported successfully"
    }
    ```

### Configuration

#### Get Sensor Configuration

Retrieves sensor configuration.

- **URL**: `/api/config/sensors`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "dhtInterval": 30,
      "scdInterval": 60,
      "graphUpdateInterval": 10,
      "graphMaxPoints": 100,
      "thresholds": {
        "temperature": {
          "low": 18,
          "high": 26
        },
        "humidity": {
          "low": 50,
          "high": 85
        },
        "co2": {
          "low": 1000,
          "high": 1600
        }
      }
    }
    ```

#### Update Sensor Configuration

Updates sensor configuration.

- **URL**: `/api/config/sensors`
- **Method**: `POST`
- **Request Body**: Sensor configuration (see format in Get Sensor Configuration)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Sensor configuration updated"
    }
    ```

#### Get Relay Configuration

Retrieves relay configuration.

- **URL**: `/api/config/relays`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "relays": {
        "1": {
          "name": "Main PSU",
          "pin": 18,
          "status": false,
          "dependency": [],
          "visible": false,
          "schedule": {
            "start": "00:00",
            "end": "23:59"
          },
          "overrideTimeout": 300
        },
        "2": { ... },
        "3": { ... },
        ...
      },
      "automation": {
        "humidifier": {
          "lowThreshold": 50,
          "highThreshold": 85
        },
        "heater": {
          "lowThreshold": 20,
          "highThreshold": 24
        },
        "co2": {
          "lowThreshold": 1100,
          "highThreshold": 1600
        },
        "fans": {
          "onDuration": 10,
          "cycleInterval": 60
        }
      }
    }
    ```

#### Update Relay Configuration

Updates relay configuration.

- **URL**: `/api/config/relays`
- **Method**: `POST`
- **Request Body**: Relay configuration (see format in Get Relay Configuration)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Relay configuration updated"
    }
    ```

### Network

#### Get Network Configuration

Retrieves network configuration.

- **URL**: `/api/network/config`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "wifi": {
        "networks": [
          {
            "ssid": "MyWiFi",
            "password": "********",
            "mac": "AA:BB:CC:DD:EE:FF"
          },
          { ... },
          { ... }
        ],
        "currentNetwork": 0
      },
      "ip": {
        "mode": "dhcp",
        "static": {
          "ip": "",
          "netmask": "",
          "gateway": "",
          "dns1": "",
          "dns2": ""
        }
      },
      "mdns": {
        "hostname": "mushroom-controller"
      },
      "watchdog": {
        "minRssi": -80,
        "checkInterval": 60
      },
      "mqtt": {
        "enabled": false,
        "broker": "",
        "port": 1883,
        "topic": "mushroom/tent",
        "username": "",
        "password": ""
      }
    }
    ```

#### Update Network Configuration

Updates network configuration.

- **URL**: `/api/network/config`
- **Method**: `POST`
- **Request Body**: Network configuration (see format in Get Network Configuration)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Network configuration updated",
      "restartRequired": true
    }
    ```

#### Scan WiFi Networks

Scans for available WiFi networks.

- **URL**: `/api/network/scan-wifi`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "networks": [
        {
          "ssid": "MyWiFi",
          "rssi": -45,
          "mac": "AA:BB:CC:DD:EE:FF",
          "security": "WPA2"
        },
        { ... },
        { ... }
      ]
    }
    ```

#### Get Network Status

Retrieves current network status.

- **URL**: `/api/network/status`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "connected": true,
      "ssid": "MyWiFi",
      "ip": "192.168.1.100",
      "mac": "AA:BB:CC:DD:EE:FF",
      "rssi": -45,
      "mqtt": {
        "enabled": true,
        "connected": true,
        "broker": "mqtt.example.com",
        "topic": "mushroom/tent"
      }
    }
    ```

#### Restart Network Services

Restarts network services.

- **URL**: `/api/network/restart`
- **Method**: `POST`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Network services restarting"
    }
    ```

### System

#### Get System Information

Retrieves system information.

- **URL**: `/api/system/info`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "system": {
        "hostname": "mushroom-controller",
        "uptime": 86400,
        "cpuTemp": 45.2,
        "cpuFreq": 1400,
        "cpuUsage": 15.3,
        "memory": {
          "total": 1024,
          "free": 512,
          "used": 512
        },
        "storage": {
          "total": 16384,
          "free": 8192,
          "used": 8192
        }
      },
      "versions": {
        "firmware": "1.0.0",
        "filesystem": "1.0.0"
      }
    }
    ```

#### Get System Logs

Retrieves system logs.

- **URL**: `/api/system/logs`
- **Method**: `GET`
- **Query Parameters**:
  - `level`: Log level (`DEBUG`, `INFO`, `WARN`, `ERROR`)
  - `limit`: Maximum number of log entries to return
  - `start`: Start timestamp (ISO format)
  - `end`: End timestamp (ISO format)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "logs": [
        {
          "timestamp": "2023-01-01T12:00:00",
          "level": "INFO",
          "module": "main",
          "message": "System started"
        },
        { ... },
        { ... }
      ]
    }
    ```

#### Test Sensors

Tests all sensors.

- **URL**: `/api/system/test-sensors`
- **Method**: `POST`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "results": {
        "upperDHT": {
          "status": "OK",
          "values": {
            "temperature": 23.4,
            "humidity": 84.5
          }
        },
        "lowerDHT": {
          "status": "OK",
          "values": {
            "temperature": 22.9,
            "humidity": 86.2
          }
        },
        "scd40": {
          "status": "OK",
          "values": {
            "temperature": 23.1,
            "humidity": 85.3,
            "co2": 1250
          }
        }
      }
    }
    ```

#### Test Relays

Tests all relays.

- **URL**: `/api/system/test-relays`
- **Method**: `POST`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "results": {
        "1": true,
        "2": true,
        "3": true,
        "4": true,
        "5": true,
        "6": true,
        "7": true,
        "8": true
      }
    }
    ```

#### Reboot System

Reboots the system.

- **URL**: `/api/system/reboot`
- **Method**: `POST`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "System rebooting"
    }
    ```

#### Factory Reset

Performs a factory reset.

- **URL**: `/api/system/factory-reset`
- **Method**: `POST`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Factory reset initiated"
    }
    ```

### Firmware Updates

#### Get Firmware Version

Retrieves current firmware version information.

- **URL**: `/api/ota/version`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "firmware": "1.0.0",
      "filesystem": "1.0.0",
      "buildDate": "2023-01-01T12:00:00"
    }
    ```

#### Upload Firmware Package

Uploads a firmware package for installation.

- **URL**: `/api/ota/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `package`: The firmware package file (.pkg)
  - `restart`: Boolean indicating whether to restart after updating (default: false)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Update successful",
      "restarting": true
    }
    ```

### Tapo P100 Integration

#### Get Tapo Device Configuration

Retrieves Tapo device configuration.

- **URL**: `/api/tapo/config`
- **Method**: `GET`
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "credentials": {
        "username": "user@example.com",
        "password": "********"
      },
      "devices": [
        {
          "name": "Heater",
          "ip": "192.168.1.101",
          "relayMapping": 6
        },
        {
          "name": "Main PSU",
          "ip": "192.168.1.102",
          "relayMapping": 1
        }
      ]
    }
    ```

#### Update Tapo Device Configuration

Updates Tapo device configuration.

- **URL**: `/api/tapo/config`
- **Method**: `POST`
- **Request Body**: Tapo configuration (see format in Get Tapo Device Configuration)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "message": "Tapo configuration updated"
    }
    ```

#### Test Tapo Device Connection

Tests connection to a Tapo device.

- **URL**: `/api/tapo/test`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "ip": "192.168.1.101",
    "username": "user@example.com",
    "password": "password"
  }
  ```
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "device": {
        "name": "TP-Link Smart Plug",
        "model": "P100",
        "firmware": "1.0.0",
        "state": "ON"
      }
    }
    ```

#### Control Tapo Device

Controls a Tapo device.

- **URL**: `/api/tapo/control`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "ip": "192.168.1.101",
    "state": true
  }
  ```
  - `ip`: IP address of the Tapo device
  - `state`: Boolean indicating desired device state (true = ON, false = OFF)
- **Success Response**:
  - **Code**: 200
  - **Content**:
    ```json
    {
      "success": true,
      "device": "192.168.1.101",
      "state": true
    }
    ```

## Error Responses

All endpoints can return the following error responses:

### Bad Request

- **Code**: 400
- **Content**:
  ```json
  {
    "error": "Bad request",
    "message": "Detailed error message"
  }
  ```

### Unauthorized

- **Code**: 401
- **Content**:
  ```json
  {
    "error": "Unauthorized",
    "message": "Authentication required"
  }
  ```

### Not Found

- **Code**: 404
- **Content**:
  ```json
  {
    "error": "Not found",
    "message": "The requested resource was not found"
  }
  ```

### Internal Server Error

- **Code**: 500
- **Content**:
  ```json
  {
    "error": "Internal server error",
    "message": "Detailed error message"
  }
  ```
