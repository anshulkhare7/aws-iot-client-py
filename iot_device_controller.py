#!/usr/bin/env python3
"""
IoT Device Controller with PLC Integration

This module controls AWS IoT device communication and publishes equipment status
and data read from PLC via Modbus RTU.

PLC Configuration Requirements:
-------------------------------
The device.json configuration file must include the following sections:

1. PLC Connection Settings (required):
   "plc": {
     "port": "/dev/ttyUSB0",        # Serial port for PLC connection
     "baudrate": 9600,               # Communication speed (default: 9600)
     "bytesize": 7,                  # Data bits (default: 7 for Delta PLC)
     "parity": "E",                  # Parity bit (E=Even, default for Delta)
     "stopbits": 1,                  # Stop bits (default: 1)
     "timeout": 3,                   # Communication timeout in seconds
     "slaveAddress": 1               # Modbus slave address (default: 1)
   }

2. Equipment Configuration (required):
   "equipments": [
     {
       "id": "EQ-SITE-001-BLOWER",   # Unique equipment identifier
       "registers": {
         "status": "Y0",              # Status register (Y/M/X for boolean, D for integer)
         "data": "D0"                 # Data register (optional, typically D registers)
       }
     }
   ]

Register Types Supported:
- Y (Outputs): Boolean values from PLC output coils
- M (Coils): Boolean values from PLC internal relays
- X (Inputs): Boolean values from PLC input contacts
- D (Data): Integer values (0-65535) from PLC data registers

Example equipment status published to AWS IoT:
{
  "deviceId": "site-001",
  "timestamp": 1234567890,
  "equipmentId": "EQ-SITE-001-BLOWER",
  "status": true,
  "data": 1250
}
"""

import json
import time
import threading
import signal
import sys
from awsiot import mqtt5_client_builder
from awscrt import mqtt5, io
from concurrent.futures import Future
from config import ConfigManager
from equipment_reader import EquipmentReader
from plc_lib import DeltaPLC
from constants import (
    TOPIC_HEARTBEAT,
    TOPIC_EQUIPMENT_STATUS,
    TIMEOUT_MQTT_PUBLISH,
    TIMEOUT_CONNECTION_WAIT,
    TIMEOUT_THREAD_JOIN,
    STATUS_ONLINE,
    SLEEP_INTERVAL_MAIN_LOOP,
    SLEEP_INTERVAL_HEARTBEAT_CHECK,
    SLEEP_INTERVAL_EQUIPMENT_STATUS,
    DEFAULT_CONFIG_FILE
)

class IoTDeviceController:
    def __init__(self, config_file=DEFAULT_CONFIG_FILE):
        self.config_manager = ConfigManager(config_file)
        self.client = None
        self.is_running = False
        self.heartbeat_thread = None

        # Initialize PLC reader with configuration
        self.plc_reader = DeltaPLC(self.config_manager.plc_config)

        # Initialize equipment reader with config manager and PLC reader
        self.equipment_reader = EquipmentReader(self.config_manager, self.plc_reader)
        self.equipment_status_thread = None

    def _on_connection_success(self, connack_packet):
        """Callback when connection succeeds"""
        print(f"Connected to AWS IoT Core at {self.config_manager.endpoint}")

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
            endpoint=self.config_manager.endpoint,
            cert_filepath=self.config_manager.cert_path,
            pri_key_filepath=self.config_manager.private_key_path,
            ca_filepath=self.config_manager.root_ca_path,
            client_bootstrap=client_bootstrap,
            client_id=self.config_manager.device_id,
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
            "deviceId": self.config_manager.device_id,
            "timestamp": int(time.time()),
            "status": STATUS_ONLINE
        }

        publish_packet = mqtt5.PublishPacket(
            topic=TOPIC_HEARTBEAT,
            payload=json.dumps(heartbeat_payload),
            qos=mqtt5.QoS.AT_LEAST_ONCE
        )

        try:
            publish_future = self.client.publish(publish_packet)
            # Wait for publish to complete
            publish_future.result(timeout=TIMEOUT_MQTT_PUBLISH)
            print(f"Heartbeat published: {heartbeat_payload}")
        except Exception as e:
            print(f"Failed to publish heartbeat: {e}")

    def _heartbeat_loop(self):
        """Background thread for sending heartbeats at configured interval"""
        interval = self.config_manager.heartbeat_interval
        while self.is_running:
            self._publish_heartbeat()
            # Sleep for configured interval, but check every second if we should stop
            for _ in range(interval):
                if not self.is_running:
                    break
                time.sleep(SLEEP_INTERVAL_HEARTBEAT_CHECK)

    def _publish_equipment_status(self):
        """Publish equipment status messages"""
        if not self.client:
            return

        # Read equipment status from file
        equipment_list = self.equipment_reader.read()

        if not equipment_list:
            print("No equipment status data to publish")
            return

        # Publish status for each equipment
        for equipment in equipment_list:
            equipment_payload = {
                "deviceId": self.config_manager.device_id,
                "timestamp": int(time.time()),
                "equipmentId": equipment.get("id", "unknown"),
                "status": equipment.get("status", False)
            }

            publish_packet = mqtt5.PublishPacket(
                topic=TOPIC_EQUIPMENT_STATUS,
                payload=json.dumps(equipment_payload),
                qos=mqtt5.QoS.AT_LEAST_ONCE
            )

            try:
                publish_future = self.client.publish(publish_packet)
                # Wait for publish to complete
                publish_future.result(timeout=TIMEOUT_MQTT_PUBLISH)
                print(f"Equipment status published: {equipment_payload}")
            except Exception as e:
                print(f"Failed to publish equipment status: {e}")

    def _equipment_status_loop(self):
        """Background thread for publishing equipment status at regular intervals"""
        while self.is_running:
            self._publish_equipment_status()
            # Sleep for configured interval, but check every second if we should stop
            for _ in range(SLEEP_INTERVAL_EQUIPMENT_STATUS):
                if not self.is_running:
                    break
                time.sleep(SLEEP_INTERVAL_HEARTBEAT_CHECK)

    def start(self):
        """Start the IoT client and heartbeat publishing"""
        try:
            print(f"Starting IoT client for device: {self.config_manager.device_id}")

            # Create and start client
            self.client = self._create_client()
            self.client.start()

            # Wait for connection with a simple delay
            print("Waiting for connection...")
            time.sleep(TIMEOUT_CONNECTION_WAIT)  # Give time for connection to establish

            # Start heartbeat thread
            self.is_running = True
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()

            # Start equipment status thread
            self.equipment_status_thread = threading.Thread(target=self._equipment_status_loop, daemon=True)
            self.equipment_status_thread.start()

            print(f"IoT client started successfully. Publishing heartbeats every {self.config_manager.heartbeat_interval} seconds...")
            print(f"Publishing equipment status every {SLEEP_INTERVAL_EQUIPMENT_STATUS} seconds...")
            return True

        except Exception as e:
            print(f"Failed to start IoT client: {e}")
            return False

    def stop(self):
        """Stop the IoT client and heartbeat publishing"""
        print("Stopping IoT client...")

        self.is_running = False

        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=TIMEOUT_THREAD_JOIN)

        if self.equipment_status_thread:
            self.equipment_status_thread.join(timeout=TIMEOUT_THREAD_JOIN)

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
                time.sleep(SLEEP_INTERVAL_MAIN_LOOP)
        except KeyboardInterrupt:
            pass

    client_instance.stop()

if __name__ == "__main__":
    main()