#!/usr/bin/env python3

import json
import time
import threading
import signal
import sys
import os
from awsiot import mqtt5_client_builder
from awscrt import mqtt5, io
from concurrent.futures import Future

class IoTDeviceController:
    def __init__(self, config_file="config/device.json"):
        self.config = self._load_config(config_file)
        self.client = None
        self.is_running = False
        self.heartbeat_thread = None

    def _load_config(self, config_file):
        """Load device configuration from JSON file"""
        with open(config_file, 'r') as f:
            return json.load(f)

    def _on_connection_success(self, connack_packet):
        """Callback when connection succeeds"""
        print(f"Connected to AWS IoT Core at {self.config['endpoint']}")

    def _on_connection_failure(self, connack_packet):
        """Callback when connection fails"""
        print(f"Connection failed: {connack_packet}")

    def _on_disconnection(self, disconnect_packet):
        """Callback when disconnected"""
        print("Disconnected from AWS IoT Core")

    def _create_client(self):
        """Create and configure MQTT5 client"""
        # Create client builder
        client_bootstrap = io.ClientBootstrap.get_or_create_static_default()

        # Create the client directly
        client = mqtt5_client_builder.mtls_from_path(
            endpoint=self.config['endpoint'],
            cert_filepath="certs/raspi-bglr.cert.pem",
            pri_key_filepath="certs/raspi-bglr.private.key",
            ca_filepath="certs/AmazonRootCA1.pem",
            client_bootstrap=client_bootstrap,
            client_id=self.config['deviceId'],
            on_publish_callback_fn=None,
            on_lifecycle_event_stopped_fn=None,
            on_lifecycle_event_attempting_connect_fn=None,
            on_lifecycle_event_connection_success_fn=self._on_connection_success,
            on_lifecycle_event_connection_failure_fn=self._on_connection_failure,
            on_lifecycle_event_disconnection_fn=self._on_disconnection,
        )

        return client

    def _publish_heartbeat(self):
        """Publish heartbeat message"""
        if not self.client:
            return

        heartbeat_payload = {
            "deviceId": self.config['deviceId'],
            "timestamp": int(time.time()),
            "status": "online"
        }

        publish_packet = mqtt5.PublishPacket(
            topic="devices/heartbeat",
            payload=json.dumps(heartbeat_payload),
            qos=mqtt5.QoS.AT_LEAST_ONCE
        )

        try:
            publish_future = self.client.publish(publish_packet)
            # Wait for publish to complete
            publish_future.result(timeout=10)
            print(f"Heartbeat published: {heartbeat_payload}")
        except Exception as e:
            print(f"Failed to publish heartbeat: {e}")

    def _heartbeat_loop(self):
        """Background thread for sending heartbeats at configured interval"""
        interval = self.config.get('heartbeatInterval', 60)  # Default to 60 seconds
        while self.is_running:
            self._publish_heartbeat()
            # Sleep for configured interval, but check every second if we should stop
            for _ in range(interval):
                if not self.is_running:
                    break
                time.sleep(1)

    def start(self):
        """Start the IoT client and heartbeat publishing"""
        try:
            print(f"Starting IoT client for device: {self.config['deviceId']}")

            # Create and start client
            self.client = self._create_client()
            self.client.start()

            # Wait for connection with a simple delay
            print("Waiting for connection...")
            time.sleep(5)  # Give time for connection to establish

            # Start heartbeat thread
            self.is_running = True
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()

            interval = self.config.get('heartbeatInterval', 60)
            print(f"IoT client started successfully. Publishing heartbeats every {interval} seconds...")
            return True

        except Exception as e:
            print(f"Failed to start IoT client: {e}")
            return False

    def stop(self):
        """Stop the IoT client and heartbeat publishing"""
        print("Stopping IoT client...")

        self.is_running = False

        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)

        if self.client:
            self.client.stop()

        print("IoT client stopped")

def signal_handler(_signum, _frame):
    """Handle SIGINT (Ctrl+C) gracefully"""
    print("\nReceived interrupt signal. Shutting down...")
    if 'client_instance' in globals():
        client_instance.stop()
    sys.exit(0)

def main():
    global client_instance

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start IoT device controller
    client_instance = IoTDeviceController()

    if client_instance.start():
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    client_instance.stop()

if __name__ == "__main__":
    main()