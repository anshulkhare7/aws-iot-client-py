#!/usr/bin/env python3

import json
import time
import threading
import signal
import sys
import os
import logging
from typing import Dict, Any, Callable, Optional
from awsiot import mqtt5_client_builder, iotshadow
from awscrt import mqtt5, io
from concurrent.futures import Future
from equipment_controller import EquipmentController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ShadowDeviceController:
    """
    IoT Device Controller with AWS IoT Device Shadow support.
    Integrates with EquipmentController for stateless GPIO management.
    """

    def __init__(self, config_file="config/device.json", equipment_controller=None):
        """
        Initialize the Shadow Device Controller.

        Args:
            config_file: Path to device configuration JSON file
            equipment_controller: EquipmentController instance (optional)
        """
        self.config = self._load_config(config_file)
        self.device_id = self.config['deviceId']
        self.shadow_name = self.device_id  # Use device ID as shadow name

        # MQTT client
        self.client = None
        self.is_running = False
        self.heartbeat_thread = None

        # Shadow client
        self.shadow_client = None
        self.connection_future = None

        # Equipment controller
        self.equipment_controller = equipment_controller or EquipmentController()

        # Shadow topics
        self._setup_shadow_topics()

        logger.info(f"ShadowDeviceController initialized for device: {self.device_id}")

    def _load_config(self, config_file):
        """Load device configuration from JSON file"""
        with open(config_file, 'r') as f:
            return json.load(f)

    def _setup_shadow_topics(self):
        """Setup shadow topic names"""
        self.shadow_topics = {
            'get': f"$aws/things/{self.shadow_name}/shadow/get",
            'get_accepted': f"$aws/things/{self.shadow_name}/shadow/get/accepted",
            'get_rejected': f"$aws/things/{self.shadow_name}/shadow/get/rejected",
            'update': f"$aws/things/{self.shadow_name}/shadow/update",
            'update_accepted': f"$aws/things/{self.shadow_name}/shadow/update/accepted",
            'update_rejected': f"$aws/things/{self.shadow_name}/shadow/update/rejected",
            'update_delta': f"$aws/things/{self.shadow_name}/shadow/update/delta"
        }

    def _on_connection_success(self, connack_packet):
        """Callback when connection succeeds"""
        logger.info(f"Connected to AWS IoT Core at {self.config['endpoint']}")

        # Initialize shadow client
        self._initialize_shadow_client()

    def _on_connection_failure(self, connack_packet):
        """Callback when connection fails"""
        logger.error(f"Connection failed: {connack_packet}")

    def _on_disconnection(self, disconnect_packet):
        """Callback when disconnected"""
        logger.warning("Disconnected from AWS IoT Core")

    def _initialize_shadow_client(self):
        """Initialize the shadow client after MQTT connection is established"""
        try:
            self.shadow_client = iotshadow.IotShadowClient(self.client)

            # Subscribe to shadow topics
            self._subscribe_to_shadow_topics()

            # Get current shadow state and sync with hardware
            self._sync_shadow_with_hardware()

            logger.info("Shadow client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize shadow client: {e}")

    def _subscribe_to_shadow_topics(self):
        """Subscribe to shadow update delta and response topics"""
        try:
            # Subscribe to delta updates (desired state changes)
            delta_request = iotshadow.ShadowDeltaUpdatedSubscriptionRequest()
            delta_request.thing_name = self.shadow_name

            logger.info(f"Subscribing to shadow delta updates for {self.shadow_name}")
            delta_future = self.shadow_client.subscribe_to_shadow_delta_updated_events(
                request=delta_request,
                qos=mqtt5.QoS.AT_LEAST_ONCE,
                callback=self._on_shadow_delta_updated
            )
            delta_future.result(timeout=10)

            # Subscribe to get shadow responses
            get_request = iotshadow.GetShadowSubscriptionRequest()
            get_request.thing_name = self.shadow_name

            get_future = self.shadow_client.subscribe_to_get_shadow_accepted(
                request=get_request,
                qos=mqtt5.QoS.AT_LEAST_ONCE,
                callback=self._on_get_shadow_accepted
            )
            get_future.result(timeout=10)

            # Subscribe to update responses
            update_request = iotshadow.UpdateShadowSubscriptionRequest()
            update_request.thing_name = self.shadow_name

            update_future = self.shadow_client.subscribe_to_update_shadow_accepted(
                request=update_request,
                qos=mqtt5.QoS.AT_LEAST_ONCE,
                callback=self._on_update_shadow_accepted
            )
            update_future.result(timeout=10)

            logger.info("Successfully subscribed to shadow topics")

        except Exception as e:
            logger.error(f"Failed to subscribe to shadow topics: {e}")

    def _sync_shadow_with_hardware(self):
        """Sync shadow reported state with current hardware state (GPIO pins)"""
        try:
            # Get current equipment states from GPIO
            current_states = self.equipment_controller.get_all_states()

            logger.info(f"Current hardware states: {current_states}")

            # Update shadow reported state to match hardware
            self._update_shadow_reported_state(current_states)

            # Also get the current shadow document to check for any pending desired states
            self._get_shadow_document()

        except Exception as e:
            logger.error(f"Failed to sync shadow with hardware: {e}")

    def _get_shadow_document(self):
        """Request the current shadow document"""
        try:
            request = iotshadow.GetShadowRequest()
            request.thing_name = self.shadow_name

            logger.debug("Requesting current shadow document")
            future = self.shadow_client.publish_get_shadow(
                request=request,
                qos=mqtt5.QoS.AT_LEAST_ONCE
            )
            future.result(timeout=10)

        except Exception as e:
            logger.error(f"Failed to get shadow document: {e}")

    def _on_get_shadow_accepted(self, response):
        """Handle get shadow response"""
        try:
            logger.info(f"Received shadow document: {response.state}")

            # Check if there are any desired states that differ from reported states
            if response.state and response.state.desired:
                current_reported = response.state.reported or {}

                # Process any differences between desired and reported
                for equipment_type, desired_state in response.state.desired.items():
                    if equipment_type in ['blower', 'vibrofeeder']:
                        current_state = current_reported.get(equipment_type, {})
                        if desired_state.get('is_active') != current_state.get('is_active'):
                            logger.info(f"Processing pending desired state for {equipment_type}: {desired_state}")
                            self._process_shadow_delta({equipment_type: desired_state})

        except Exception as e:
            logger.error(f"Error processing get shadow response: {e}")

    def _on_shadow_delta_updated(self, delta):
        """Handle shadow delta updates (desired state changes)"""
        try:
            logger.info(f"Received shadow delta: {delta.state}")
            self._process_shadow_delta(delta.state)

        except Exception as e:
            logger.error(f"Error processing shadow delta: {e}")

    def _process_shadow_delta(self, delta_state: Dict[str, Any]):
        """
        Process shadow delta by updating equipment states and reporting back.

        Args:
            delta_state: The delta state changes from shadow
        """
        try:
            updated_states = {}

            for equipment_type, desired_state in delta_state.items():
                if equipment_type in ['blower', 'vibrofeeder']:
                    desired_active = desired_state.get('is_active', False)

                    logger.info(f"Setting {equipment_type} to {'ON' if desired_active else 'OFF'}")

                    # Apply the change to GPIO (source of truth)
                    actual_state = self.equipment_controller.set_state(equipment_type, desired_active)

                    # Read back the actual state from GPIO
                    verified_state = self.equipment_controller.get_state(equipment_type)

                    updated_states[equipment_type] = {'is_active': verified_state}

                    if verified_state == desired_active:
                        logger.info(f"Successfully set {equipment_type} to {'ON' if verified_state else 'OFF'}")
                    else:
                        logger.warning(f"Failed to set {equipment_type}. Desired: {desired_active}, Actual: {verified_state}")

            # Update shadow reported state with actual hardware states
            if updated_states:
                self._update_shadow_reported_state(updated_states)

        except Exception as e:
            logger.error(f"Error processing shadow delta: {e}")

    def _update_shadow_reported_state(self, states: Dict[str, Dict[str, Any]]):
        """
        Update shadow reported state.

        Args:
            states: Dictionary of equipment states to report
        """
        try:
            request = iotshadow.UpdateShadowRequest()
            request.thing_name = self.shadow_name
            request.state = iotshadow.ShadowState()
            request.state.reported = states

            logger.info(f"Updating shadow reported state: {states}")

            future = self.shadow_client.publish_update_shadow(
                request=request,
                qos=mqtt5.QoS.AT_LEAST_ONCE
            )
            future.result(timeout=10)

        except Exception as e:
            logger.error(f"Failed to update shadow reported state: {e}")

    def _on_update_shadow_accepted(self, response):
        """Handle successful shadow update"""
        logger.debug(f"Shadow update accepted: {response.state}")

    def _create_client(self):
        """Create and configure MQTT5 client"""
        client_bootstrap = io.ClientBootstrap.get_or_create_static_default()

        client = mqtt5_client_builder.mtls_from_path(
            endpoint=self.config['endpoint'],
            cert_filepath="certs/raspi-bglr.cert.pem",
            pri_key_filepath="certs/raspi-bglr.private.key",
            ca_filepath="certs/AmazonRootCA1.pem",
            client_bootstrap=client_bootstrap,
            client_id=f"{self.config['deviceId']}-shadow",
            on_publish_callback_fn=None,
            on_lifecycle_event_stopped_fn=None,
            on_lifecycle_event_attempting_connect_fn=None,
            on_lifecycle_event_connection_success_fn=self._on_connection_success,
            on_lifecycle_event_connection_failure_fn=self._on_connection_failure,
            on_lifecycle_event_disconnection_fn=self._on_disconnection,
        )

        return client

    def _publish_heartbeat(self):
        """Publish heartbeat message with equipment status"""
        if not self.client:
            return

        try:
            # Get current equipment states
            equipment_states = self.equipment_controller.get_all_states()

            heartbeat_payload = {
                "deviceId": self.config['deviceId'],
                "timestamp": int(time.time()),
                "status": "online",
                "equipment": equipment_states
            }

            publish_packet = mqtt5.PublishPacket(
                topic="devices/heartbeat",
                payload=json.dumps(heartbeat_payload),
                qos=mqtt5.QoS.AT_LEAST_ONCE
            )

            publish_future = self.client.publish(publish_packet)
            publish_future.result(timeout=10)
            logger.debug(f"Heartbeat published: {heartbeat_payload}")

        except Exception as e:
            logger.error(f"Failed to publish heartbeat: {e}")

    def _heartbeat_loop(self):
        """Background thread for sending heartbeats at configured interval"""
        interval = self.config.get('heartbeatInterval', 60)
        while self.is_running:
            self._publish_heartbeat()
            # Sleep for configured interval, but check every second if we should stop
            for _ in range(interval):
                if not self.is_running:
                    break
                time.sleep(1)

    def update_equipment_state_and_shadow(self, equipment_type: str, is_active: bool) -> bool:
        """
        Update equipment state via GPIO and report to shadow.
        This method is called from the web application.

        Args:
            equipment_type: The type of equipment
            is_active: Desired state

        Returns:
            Actual state after update
        """
        try:
            # Update GPIO (source of truth)
            actual_state = self.equipment_controller.set_state(equipment_type, is_active)

            # Report actual state to shadow
            states = {equipment_type: {'is_active': actual_state}}
            self._update_shadow_reported_state(states)

            return actual_state

        except Exception as e:
            logger.error(f"Failed to update equipment state and shadow: {e}")
            return self.equipment_controller.get_state(equipment_type)

    def get_equipment_states(self) -> Dict[str, Dict[str, Any]]:
        """Get current equipment states from GPIO (source of truth)"""
        return self.equipment_controller.get_all_states()

    def get_equipment_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed equipment information"""
        return self.equipment_controller.get_equipment_info()

    def start(self):
        """Start the IoT client, shadow client, and heartbeat publishing"""
        try:
            logger.info(f"Starting Shadow IoT client for device: {self.config['deviceId']}")

            # Create and start MQTT client
            self.client = self._create_client()
            self.client.start()

            # Wait for connection
            logger.info("Waiting for connection...")
            time.sleep(5)

            # Start heartbeat thread
            self.is_running = True
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()

            interval = self.config.get('heartbeatInterval', 60)
            logger.info(f"Shadow IoT client started. Publishing heartbeats every {interval} seconds")
            return True

        except Exception as e:
            logger.error(f"Failed to start Shadow IoT client: {e}")
            return False

    def stop(self):
        """Stop the IoT client and cleanup"""
        logger.info("Stopping Shadow IoT client...")

        self.is_running = False

        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)

        if self.client:
            self.client.stop()

        # Cleanup equipment controller
        if self.equipment_controller:
            self.equipment_controller.cleanup()

        logger.info("Shadow IoT client stopped")

def signal_handler(_signum, _frame):
    """Handle SIGINT (Ctrl+C) gracefully"""
    logger.info("Received interrupt signal. Shutting down...")
    if 'client_instance' in globals():
        client_instance.stop()
    sys.exit(0)

def main():
    global client_instance

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start Shadow IoT device controller
    client_instance = ShadowDeviceController()

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