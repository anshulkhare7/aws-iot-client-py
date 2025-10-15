#!/bin/bash

# AWS IoT Client Deployment Script
# Deploys aws-iot-client-py to Raspberry Pi and sets up PM2 autostart

set -e  # Exit on any error

# Configuration
REMOTE_USER="pi"
REMOTE_HOST="pi"
REMOTE_DIR="~/innocule/aws-iot-client-py"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we can connect to the Raspberry Pi
log_info "Checking connection to Raspberry Pi..."
log_info "Note: SSH password will only be required once (connection will be reused)"
if ! ssh -o ConnectTimeout=5 "$REMOTE_USER@$REMOTE_HOST" "echo 'Connection successful'" > /dev/null 2>&1; then
    log_error "Cannot connect to $REMOTE_USER@$REMOTE_HOST"
    log_error "Please ensure:"
    log_error "  1. The Raspberry Pi is powered on and connected to the network"
    log_error "  2. SSH is enabled on the Raspberry Pi"
    log_error "  3. You have SSH access configured (try: ssh $REMOTE_USER@$REMOTE_HOST)"
    exit 1
fi
log_info "Connection successful!"

# Create remote directory if it doesn't exist
log_info "Creating remote directory structure..."
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# Copy files to Raspberry Pi
log_info "Copying application files..."

# Copy main Python script
log_info "  - Copying iot_device_controller.py"
scp "$LOCAL_DIR/iot_device_controller.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# Copy constants file
log_info "  - Copying constants.py"
scp "$LOCAL_DIR/constants.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# Copy equipment status reader
log_info "  - Copying equipment_status_reader.py"
scp "$LOCAL_DIR/equipment_status_reader.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# Copy data directory
log_info "  - Copying data directory"
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR/data"
scp "$LOCAL_DIR/data/status.json" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/data/"

# Copy config module
log_info "  - Copying config module"
scp "$LOCAL_DIR/config/__init__.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/config/"
scp "$LOCAL_DIR/config/config_manager.py" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/config/"

# Copy ecosystem.config.js
log_info "  - Copying ecosystem.config.js"
scp "$LOCAL_DIR/ecosystem.config.js" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

log_info "File copy complete!"

# Setup PM2 process
log_info "Setting up PM2 process..."
ssh "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
    cd ~/innocule/aws-iot-client-py

    # Check if PM2 is installed
    if ! command -v pm2 &> /dev/null; then
        echo "PM2 not found. Installing PM2..."
        sudo npm install -g pm2
    fi

    # Stop existing process if running
    if pm2 list | grep -q "aws-iot-client"; then
        echo "Stopping existing aws-iot-client process..."
        pm2 stop aws-iot-client || true
        pm2 delete aws-iot-client || true
    fi

    # Start the process with ecosystem config
    echo "Starting aws-iot-client with PM2..."
    pm2 start ecosystem.config.js

    # Save PM2 process list
    echo "Saving PM2 process list..."
    pm2 save

    # Setup PM2 to start on boot
    echo "Setting up PM2 startup script..."
    pm2 startup systemd -u pi --hp /home/pi | tail -n 1 > /tmp/pm2_startup.sh
    if [ -s /tmp/pm2_startup.sh ]; then
        sudo bash /tmp/pm2_startup.sh
        rm /tmp/pm2_startup.sh
    fi

    # Display status
    echo ""
    echo "==================================="
    echo "PM2 Process Status:"
    echo "==================================="
    pm2 list
    echo ""
    pm2 info aws-iot-client
ENDSSH

log_info "Deployment complete!"
log_info ""
log_info "You can manage the service using:"
log_info "  ssh $REMOTE_USER@$REMOTE_HOST 'pm2 list'          - View process status"
log_info "  ssh $REMOTE_USER@$REMOTE_HOST 'pm2 logs aws-iot-client'  - View logs"
log_info "  ssh $REMOTE_USER@$REMOTE_HOST 'pm2 restart aws-iot-client'  - Restart service"
log_info "  ssh $REMOTE_USER@$REMOTE_HOST 'pm2 stop aws-iot-client'  - Stop service"
