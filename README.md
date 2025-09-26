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
