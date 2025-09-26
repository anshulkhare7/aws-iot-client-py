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
