# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the AWS IoT Client Python application.

## Project Overview

Python-based AWS IoT Device Client that runs on Raspberry Pi devices. Connects to AWS IoT Core via MQTT5 with mutual TLS and publishes periodic heartbeat messages to `devices/heartbeat`.

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

- Use Python 3.x, follow PEP 8, use type hints where appropriate
- Catch and log all exceptions in publish operations
- Use timeouts for MQTT operations (default: 10 seconds)
- Heartbeat runs in a daemon thread; check `is_running` flag every second during sleep for responsive shutdown
- Join threads with timeout on shutdown

## KEEP IN MIND

1. Whenever I make a suggestion or question your implentation, don't accept it on face value. I am not a python expert and I could be wrong. Verify what I am saying before accepting them.

2. After adding/updating the code, check again for unused imports. Remove them if any import becomes unused because of your changes.

3. Don't forget to update the deploy script (deploy.sh) when you introduce new files or delete/relocate existing files.
