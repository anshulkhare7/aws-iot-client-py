# AWS IoT Shadow Flask Application

A Flask-based web application for Raspberry Pi that integrates GPIO equipment control with AWS IoT Device Shadows. This application provides stateless, hardware-centric control of blower and vibrofeeder equipment.

## Architecture

### Key Features
- **Stateless Design**: GPIO pins are the single source of truth
- **Device Shadow Integration**: Bidirectional sync with AWS IoT Core
- **Web API**: RESTful endpoints for equipment control and monitoring
- **Crash Recovery**: Automatic state recovery from hardware on startup

### Components

1. **EquipmentController**: Stateless GPIO management
2. **ShadowDeviceController**: AWS IoT Shadow client with MQTT
3. **Flask App**: Web API for control and monitoring
4. **Device Shadow**: AWS cloud state synchronization

## Installation

### Prerequisites
- Python 3.7+
- AWS IoT Core device certificates
- Raspberry Pi with relay modules
- Node.js and npm (for PM2)

### Setup

1. **Install UV (Python Package Manager)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR="/usr/local/bin" sh
   ```

2. **Create Virtual Environment**
   ```bash
   uv venv aws-iot
   ```

3. **Activate Virtual Environment**
   ```bash
   source aws-iot/bin/activate
   ```

4. **Install Python Dependencies**
   ```bash
   uv pip install awsiotsdk
   uv pip install RPi.GPIO
   uv pip install flask
   ```

5. **Configure Device**
   Update `config/device.json`:
   ```json
   {
     "deviceId": "raspi-bglr",
     "endpoint": "your-iot-endpoint.amazonaws.com",
     "region": "your-region",
     "heartbeatInterval": 60
   }
   ```

6. **AWS IoT Certificates**
   Place certificates in `certs/` directory:
   - `raspi-bglr.cert.pem`
   - `raspi-bglr.private.key`
   - `AmazonRootCA1.pem`

## Usage

### Running the Application

**Direct Python:**
```bash
python3 app.py
```

**With PM2 (Production):**
```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start ecosystem.config.js

# Enable auto-start on boot
pm2 startup
pm2 save

# Monitor
pm2 status
pm2 logs iot-shadow-app
pm2 restart iot-shadow-app
```

### Environment Variables
- `FLASK_PORT=5000`: Web server port
- `FLASK_HOST=0.0.0.0`: Web server host
- `FLASK_DEBUG=false`: Enable debug mode

## API Endpoints

### Health Check
```bash
GET /health
```

Returns application health status and initialization state.

### Equipment Status
```bash
GET /equipment/status
```

Returns the current status of all equipment (blower and vibrofeeder).

**Response example:**
```json
{
  "success": true,
  "data": {
    "equipment": {
      "blower": {"is_active": false},
      "vibrofeeder": {"is_active": false}
    },
    "timestamp": 1698123456
  }
}
```

### Equipment Control
```bash
POST /equipment/control
Content-Type: application/json
{
  "equipment_type": "blower",
  "is_active": true
}
```

Controls equipment (turn on/off). Equipment type must be either `"blower"` or `"vibrofeeder"`.

**Response example:**
```json
{
  "success": true,
  "data": {
    "equipment_type": "blower",
    "requested_state": true,
    "actual_state": true,
    "timestamp": 1698123456
  }
}
```

## Testing Strategies

### 1. Local Development Testing

**Start the Application:**
```bash
python3 app.py
```

**Test Equipment Control:**
```bash
# Turn on blower
curl -X POST http://localhost:5000/equipment/control \
  -H "Content-Type: application/json" \
  -d '{"equipment_type": "blower", "is_active": true}'

# Turn off vibrofeeder
curl -X POST http://localhost:5000/equipment/control \
  -H "Content-Type: application/json" \
  -d '{"equipment_type": "vibrofeeder", "is_active": false}'

# Check status
curl http://localhost:5000/equipment/status
```

### 2. AWS IoT Shadow Testing

**Using AWS IoT Console:**
1. Navigate to IoT Core > Manage > Things > raspi-bglr
2. Go to Device Shadow > Classic Shadow
3. Update desired state:
   ```json
   {
     "state": {
       "desired": {
         "blower": {"is_active": true}
       }
     }
   }
   ```
4. Watch for reported state update in shadow document
5. Verify equipment endpoint reflects the change

**Monitor Shadow Updates:**
```bash
# Check equipment status
curl http://localhost:5000/equipment/status
```

### 3. Recovery Testing

**Process Restart Recovery:**
```bash
# Start application
python3 app.py

# Control some equipment
curl -X POST http://localhost:5000/equipment/control \
  -H "Content-Type: application/json" \
  -d '{"equipment_type": "blower", "is_active": true}'

# Kill and restart process
# Ctrl+C, then python3 app.py again

# Check that shadow syncs with hardware state
curl http://localhost:5000/equipment/status
```

### 4. Hardware Integration Testing (Raspberry Pi)

**Deploy and Run with PM2:**
```bash
# Deploy to Raspberry Pi
scp -r . pi@your-pi:/home/pi/innocule/aws-iot-client-py/

# SSH and setup
ssh pi@your-pi
cd /home/pi/innocule/aws-iot-client-py/
pip3 install -r requirements.txt

# Start with PM2
pm2 start ecosystem.config.js

# Check application status
pm2 status
pm2 logs iot-shadow-app
```

**GPIO Verification:**
```bash
# Test GPIO control
curl -X POST http://pi-ip:5000/equipment/control \
  -H "Content-Type: application/json" \
  -d '{"equipment_type": "blower", "is_active": true}'

# Check logs for GPIO operations
pm2 logs iot-shadow-app --lines 20

# Physically verify relay clicks and LED indicators
```

### 5. PM2 Production Testing

**Service Management:**
```bash
# Test auto-restart on crash
pm2 restart iot-shadow-app

# Test memory management
pm2 monit

# Test log rotation and monitoring
pm2 logs iot-shadow-app --lines 100
```

**Boot Testing:**
```bash
# Verify auto-start on boot
sudo reboot
# After reboot:
pm2 status
curl http://localhost:5000/health
```

## Equipment Configuration

### GPIO Pin Mapping
- **Blower**: GPIO Pin 17 (Physical Pin 11)
- **Vibrofeeder**: GPIO Pin 27 (Physical Pin 13)

### Relay Logic
- **Active Low**: LOW = Equipment ON, HIGH = Equipment OFF
- **Safe Default**: All equipment starts in OFF state
- **Hardware Source of Truth**: GPIO state is read to determine actual status

## Device Shadow Document Structure

### Complete Shadow Document
```json
{
  "state": {
    "desired": {
      "blower": {"is_active": false},
      "vibrofeeder": {"is_active": false}
    },
    "reported": {
      "blower": {"is_active": false},
      "vibrofeeder": {"is_active": false}
    }
  },
  "metadata": {
    "desired": {
      "blower": {"is_active": {"timestamp": 1698123456}},
      "vibrofeeder": {"is_active": {"timestamp": 1698123456}}
    },
    "reported": {
      "blower": {"is_active": {"timestamp": 1698123456}},
      "vibrofeeder": {"is_active": {"timestamp": 1698123456}}
    }
  }
}
```

## Control Flow

### 1. Web API Control Flow
```
HTTP Request → Flask App → EquipmentController → GPIO → Shadow Report
```

### 2. Shadow Delta Flow
```
AWS Shadow Update → Shadow Client → EquipmentController → GPIO → Shadow Report
```

### 3. Startup Recovery Flow
```
App Start → Read GPIO States → Update Shadow Reported → Ready
```

## Troubleshooting

### Common Issues

**1. GPIO Permission Error**
```bash
sudo usermod -a -G gpio pi
# Logout and login again
```

**2. AWS IoT Connection Issues**
- Verify certificates are in `certs/` directory
- Check AWS IoT endpoint in `config/device.json`
- Ensure device policy allows shadow operations

**3. Shadow Not Updating**
- Check AWS CloudWatch logs for IoT Core
- Verify shadow permissions in device policy
- Monitor Flask application logs

**4. Mock Mode Not Working**
- Ensure `MOCK_GPIO=true` environment variable is set
- Check that RPi.GPIO import errors are handled gracefully

### Logging
The application provides detailed logging for:
- Shadow delta processing
- Equipment state changes
- GPIO operations
- AWS IoT connectivity

## Production Deployment

### PM2 Process Manager

**Install PM2 globally:**
```bash
npm install -g pm2
```

**Deploy Application:**
```bash
# Clone/copy application to Raspberry Pi
scp -r . pi@your-pi:/home/pi/innocule/aws-iot-client-py/

# SSH to Raspberry Pi
ssh pi@your-pi
cd /home/pi/innocule/aws-iot-client-py/

# Install Python dependencies
pip3 install -r requirements.txt

# Update paths in ecosystem.config.js if needed
nano ecosystem.config.js
```

**Start with PM2:**
```bash
# Start application
pm2 start ecosystem.config.js

# Check status
pm2 status
pm2 logs iot-shadow-app

# Enable auto-start on boot
pm2 startup
pm2 save
```

**PM2 Management Commands:**
```bash
# View logs
pm2 logs iot-shadow-app
pm2 logs iot-shadow-app --lines 50

# Restart application
pm2 restart iot-shadow-app

# Stop application
pm2 stop iot-shadow-app

# Delete application from PM2
pm2 delete iot-shadow-app

# Monitor resources
pm2 monit

# Reload application (zero downtime)
pm2 reload iot-shadow-app
```

**Log Files:**
- Error logs: `/var/log/pm2/iot-shadow-app-error.log`
- Output logs: `/var/log/pm2/iot-shadow-app-out.log`
- Combined logs: `/var/log/pm2/iot-shadow-app.log`

## Legacy Application

The legacy IoT device controller (`iot_device_controller.py`) is included in the PM2 configuration but **disabled by default**. The Flask-based shadow application is the recommended approach.

To enable the legacy application if needed:
```bash
# Edit ecosystem.config.js and set disabled: false for aws-iot-client-legacy
pm2 start ecosystem.config.js
```

## Security Considerations

- AWS IoT certificates should be properly secured (`chmod 600`)
- Flask application should run behind a reverse proxy in production
- Device policies should follow principle of least privilege
- Consider implementing API authentication for production use

## Next Steps

1. **Backend Integration**: Update backend to support shadow operations
2. **Frontend Integration**: Add equipment control UI to dashboard
3. **Monitoring**: Add metrics and alerting for equipment status
4. **Automation**: Implement equipment scheduling and automation rules
