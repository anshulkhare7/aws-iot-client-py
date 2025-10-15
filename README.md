# AWS IoT Client for Raspberry Pi

This application connects a Raspberry Pi device to AWS IoT Core and publishes heartbeat and equipment status data via MQTT.

## Features

- **Heartbeat Publishing**: Sends periodic heartbeat messages to indicate device online status
- **Equipment Status Publishing**: Publishes real-time equipment status data for connected devices
- **MQTT Communication**: Uses AWS IoT Core with MQTT5 protocol
- **Automatic Reconnection**: Handles connection failures gracefully
- **PM2 Process Management**: Runs as a managed background service with auto-restart

## Installation

### Install UV

```
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR="/usr/local/bin" sh
```

### Create virtual env aws-iot

```
uv venv aws-iot
```

### Activate virtual env aws-iot

```
source aws-iot/bin/activate
```

### Install aws-iot-sdk-v2

```
uv pip install awsiotsdk
```

### Install pm2

```
npm install -g pm2
```

## Configuration

### Device Configuration

Create a configuration file at `config/device.json`:

```json
{
  "deviceId": "device-001",
  "endpoint": "your-aws-iot-endpoint.iot.region.amazonaws.com",
  "certPath": "certs/device-certificate.pem.crt",
  "privateKeyPath": "certs/device-private.pem.key",
  "rootCaPath": "certs/AmazonRootCA1.pem",
  "heartbeatInterval": 60
}
```

### Equipment Status Data

The equipment status is read from `data/status.json`. This file contains an array of equipment objects:

```json
[
  {
    "id": "EQ-BGLR-001-BLOWER",
    "status": true
  },
  {
    "id": "EQ-BGLR-001-VIBROFEEDER",
    "status": false
  }
]
```

**Note**: Currently, equipment status is read from this JSON file. This is a temporary implementation that will be replaced with serial communication to read real-time status from hardware in future versions.

The status file is reloaded before each publish cycle (every 30 seconds by default), allowing you to update equipment status by modifying the JSON file.

## MQTT Topics and Messages

### Heartbeat Messages

- **Topic**: `devices/heartbeat`
- **QoS**: 1 (AT_LEAST_ONCE)
- **Interval**: Configured in `device.json` (default: 60 seconds)
- **Payload**:
  ```json
  {
    "deviceId": "device-001",
    "timestamp": 1234567890,
    "status": "online"
  }
  ```

### Equipment Status Messages

- **Topic**: `device/data`
- **QoS**: 1 (AT_LEAST_ONCE)
- **Interval**: 30 seconds (configurable in `constants.py`)
- **Payload** (one message per equipment):
  ```json
  {
    "deviceId": "device-001",
    "timestamp": 1234567890,
    "equipmentId": "EQ-BGLR-001-BLOWER",
    "status": true
  }
  ```

## PM2 Process Management

### Start the service

```bash
pm2 start ecosystem.config.js
```

### Enable auto-start on boot

```bash
pm2 startup
pm2 save
```

### Monitor and manage the service

```bash
# View process status
pm2 status

# View real-time logs
pm2 logs aws-iot-client

# Restart the service
pm2 restart aws-iot-client

# Stop the service
pm2 stop aws-iot-client
```

## Deployment

Use the provided deployment script to deploy to a Raspberry Pi:

```bash
./deploy.sh
```

The script will:
- Copy all necessary files to the Raspberry Pi
- Set up the PM2 process
- Configure auto-start on boot
- Display the service status

## Project Structure

```
aws-iot-client-py/
├── iot_device_controller.py    # Main application entry point
├── constants.py                 # Application constants (topics, intervals, etc.)
├── equipment_status_reader.py   # Module to read equipment status from JSON
├── config/
│   ├── __init__.py
│   ├── config_manager.py        # Configuration management
│   └── device.json              # Device configuration file
├── data/
│   └── status.json              # Equipment status data (temporary)
├── certs/                       # AWS IoT certificates
├── ecosystem.config.js          # PM2 configuration
├── deploy.sh                    # Deployment script
└── README.md
```

## Future Enhancements

- Replace JSON file-based equipment status reading with serial communication for real-time hardware status
- Add support for additional sensors and equipment types
- Implement local caching and offline queuing for improved reliability
