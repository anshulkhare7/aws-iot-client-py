# Install UV

```
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR="/usr/local/bin" sh
```

# Create virtual env aws-iot

```
uv venv aws-iot
```

# Activate virtual env aws-iot

```
source aws-iot/bin/activate
```

# Install aws-iot-sdk-v2

```
uv pip install awsiotsdk
```

# Install pm2

```
npm install -g pm2
```

# Configure pm2

## Add the following to ecosystem.config.js

```
module.exports = {
    apps: [{
      name: 'aws-iot-client',
      script: 'iot_device_controller.py',
      interpreter: '/home/pi/innocule/aws-iot-client-py/aws-iot/bin/python',  // Adjust pathto your venv
      cwd: '/home/pi/innocule/aws-iot-client-py',         // Adjust to yourproject path
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production'
      }
    }]
  }
```

# Start and manage pm2 service

## Start the service

```
pm2 start ecosystem.config.js
```

## Enable auto-start on boot

```
pm2 startup
pm2 save
```

## Monitor

```
pm2 status
pm2 logs aws-iot-client
pm2 restart aws-iot-client
```
