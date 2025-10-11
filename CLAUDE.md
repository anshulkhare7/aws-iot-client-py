# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the AWS IoT Client Python application.

## Project Overview

This is a **Python-based AWS IoT Device Client** that runs on Raspberry Pi devices to maintain connectivity with AWS IoT Core. The client publishes periodic heartbeat messages to indicate device online status.

## Architecture

### Core Component

- **iot_device_controller.py**: Main application class that manages AWS IoT connection and heartbeat publishing

### Key Features

- **AWS IoT Core Connection**: Uses AWS IoT SDK v2 with MQTT5 protocol and mutual TLS authentication
- **Heartbeat Publishing**: Configurable interval heartbeat messages to `devices/heartbeat` topic
- **Process Management**: PM2-based service management for automatic restarts and boot persistence
- **Graceful Shutdown**: Signal handlers for clean disconnection on SIGINT/SIGTERM

## Configuration

### Device Configuration (config/device.json)

```json
{
  "deviceId": "raspi-bglr",
  "endpoint": "a36lji27aqnmgm-ats.iot.ap-south-1.amazonaws.com",
  "region": "ap-south-1",
  "heartbeatInterval": 60
}
```

- **deviceId**: Unique identifier for the Raspberry Pi device
- **endpoint**: AWS IoT Core endpoint URL
- **region**: AWS region
- **heartbeatInterval**: Seconds between heartbeat messages (default: 60)

### TLS Certificates (certs/ directory)

Required certificates for mutual TLS authentication:
- `raspi-bglr.cert.pem`: Device certificate
- `raspi-bglr.private.key`: Device private key
- `AmazonRootCA1.pem`: Amazon Root CA certificate

## Project Structure

```
aws-iot-client-py/
├── iot_device_controller.py   # Main IoT client application
├── ecosystem.config.js         # PM2 process configuration
├── deploy.sh                   # Deployment script
├── config/
│   └── device.json            # Device configuration
├── certs/                     # TLS certificates (not in git)
│   ├── raspi-bglr.cert.pem
│   ├── raspi-bglr.private.key
│   └── AmazonRootCA1.pem
└── aws-iot/                   # Python virtual environment
```

## Setup and Installation

### Prerequisites

1. **Install UV (Python package manager)**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR="/usr/local/bin" sh
   ```

2. **Create and activate virtual environment**:
   ```bash
   uv venv aws-iot
   source aws-iot/bin/activate
   ```

3. **Install AWS IoT SDK v2**:
   ```bash
   uv pip install awsiotsdk
   ```

4. **Install PM2 globally**:
   ```bash
   npm install -g pm2
   ```

## Running the Application

### Development/Testing

```bash
# Activate virtual environment
source aws-iot/bin/activate

# Run directly
python3 iot_device_controller.py
```

### Production (PM2)

```bash
# Start the service
pm2 start ecosystem.config.js

# Enable auto-start on boot
pm2 startup
pm2 save

# Monitor and manage
pm2 status
pm2 logs aws-iot-client
pm2 restart aws-iot-client
pm2 stop aws-iot-client
```

## MQTT Topics

### Published Topics

- **devices/heartbeat**: Periodic heartbeat messages with device status
  ```json
  {
    "deviceId": "raspi-bglr",
    "timestamp": 1234567890,
    "status": "online"
  }
  ```

## Code Architecture

### IoTDeviceController Class

**Key Methods:**
- `__init__(config_file)`: Load configuration and initialize client
- `start()`: Connect to AWS IoT Core and start heartbeat thread
- `stop()`: Gracefully disconnect and stop heartbeat thread
- `_create_client()`: Create MQTT5 client with mTLS configuration
- `_publish_heartbeat()`: Publish heartbeat message to AWS IoT
- `_heartbeat_loop()`: Background thread for periodic heartbeat publishing

**Lifecycle Callbacks:**
- `_on_connection_success()`: Called when successfully connected
- `_on_connection_failure()`: Called on connection failure
- `_on_disconnection()`: Called when disconnected

## Development Guidelines

### Python Conventions

- Use Python 3.x
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Handle exceptions gracefully with informative logging

### Error Handling

- Catch and log all exceptions in publish operations
- Use timeouts for MQTT operations (default: 10 seconds)
- Implement graceful shutdown with signal handlers

### Threading

- Heartbeat runs in a daemon thread
- Check `is_running` flag every second during sleep intervals for responsive shutdown
- Join threads with timeout on shutdown

### Configuration Changes

- Modify `config/device.json` for device-specific settings
- Restart PM2 service after configuration changes: `pm2 restart aws-iot-client`

## Deployment

Use the provided `deploy.sh` script for deployment to Raspberry Pi devices. Ensure:
1. Device configuration is updated in `config/device.json`
2. TLS certificates are present in `certs/` directory
3. PM2 is configured for auto-start

## Troubleshooting

### Connection Issues

- Verify AWS IoT endpoint is correct
- Check certificate files exist and have correct permissions
- Ensure device has internet connectivity
- Check AWS IoT Core thing policy allows connection and publish

### PM2 Issues

- Check logs: `pm2 logs aws-iot-client`
- Verify virtual environment path in `ecosystem.config.js`
- Ensure PM2 has permission to run Python scripts

### Heartbeat Not Publishing

- Check `heartbeatInterval` in configuration
- Verify MQTT topic permissions in AWS IoT policy
- Monitor logs for publish errors

## Integration

This client integrates with the broader IoT monitoring system:
- **Frontend Dashboard**: Displays device online/offline status based on heartbeat messages
- **Backend API**: Processes heartbeat messages from AWS IoT Core
- **AWS IoT Core**: Central message broker and device registry

## Security Considerations

- Never commit certificates or private keys to version control
- Use AWS IAM policies to restrict IoT Core access
- Rotate device certificates periodically
- Use least-privilege policies for MQTT topics
