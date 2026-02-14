# AWS IoT Client (Python)

A Python-based AWS IoT Device Client that runs on Raspberry Pi devices to maintain connectivity with AWS IoT Core. The client publishes periodic heartbeat messages to indicate device online status.

## Key Features

- **AWS IoT Core Connection**: Uses AWS IoT SDK v2 with MQTT5 protocol and mutual TLS authentication
- **Heartbeat Publishing**: Configurable interval heartbeat messages to `devices/heartbeat` topic
- **Process Management**: PM2-based service management for automatic restarts and boot persistence
- **Graceful Shutdown**: Signal handlers for clean disconnection on SIGINT/SIGTERM

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

## Running the Application

### Development/Testing

```bash
source aws-iot/bin/activate
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

## Deployment

Use the provided `deploy.sh` script for deployment to Raspberry Pi devices. Ensure:

1. Device configuration is updated in `config/device.json`
2. TLS certificates are present in `certs/` directory
3. PM2 is configured for auto-start

## Integration

This client integrates with the broader IoT monitoring system:

- **Frontend Dashboard**: Displays device online/offline status based on heartbeat messages
- **Backend API**: Processes heartbeat messages from AWS IoT Core
- **AWS IoT Core**: Central message broker and device registry

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

## Security Considerations

- Never commit certificates or private keys to version control
- Use AWS IAM policies to restrict IoT Core access
- Rotate device certificates periodically
- Use least-privilege policies for MQTT topics
