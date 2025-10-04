#!/usr/bin/env python3

import logging
from typing import Dict, Any
import RPi.GPIO as GPIO

class EquipmentController:
    """
    Stateless equipment controller that uses GPIO pins as the source of truth.
    No internal state is maintained - all state is read from hardware.
    """

    def __init__(self):
        """Initialize the equipment controller."""
        # Equipment configuration - maps types to GPIO pins
        self.equipment_config = {
            'blower': {'pin': 17, 'name': 'Blower'},
            'vibrofeeder': {'pin': 27, 'name': 'Vibrofeeder'}
        }

        self._setup_gpio()

        logging.info("EquipmentController initialized for Raspberry Pi GPIO")
        logging.info(f"Equipment configuration: {self.equipment_config}")

    def _setup_gpio(self):
        """Setup GPIO pins for equipment control."""
        logging.info("Setting up GPIO pins for Raspberry Pi")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for equipment_type, config in self.equipment_config.items():
            pin = config['pin']
            GPIO.setup(pin, GPIO.OUT)
            # Initialize to OFF (HIGH = OFF for active-low relays)
            GPIO.output(pin, GPIO.HIGH)
            logging.info(f"GPIO pin {pin} ({equipment_type}) initialized to OFF")

    def set_state(self, equipment_type: str, is_active: bool) -> bool:
        """
        Set the state of equipment. Returns the actual state after setting.

        Args:
            equipment_type: The type of equipment ('blower', 'vibrofeeder')
            is_active: True to turn on, False to turn off

        Returns:
            The actual state after setting (should match is_active unless error)
        """
        if equipment_type not in self.equipment_config:
            raise ValueError(f"Unknown equipment type: {equipment_type}")

        pin = self.equipment_config[equipment_type]['pin']

        # For active-low relays: LOW = ON, HIGH = OFF
        gpio_value = GPIO.LOW if is_active else GPIO.HIGH
        GPIO.output(pin, gpio_value)

        # Read back the actual state to verify
        actual_state = self.get_state(equipment_type)

        state_text = 'ON' if actual_state else 'OFF'
        logging.info(f"GPIO pin {pin} ({equipment_type}) set to {state_text}")

        return actual_state

    def get_state(self, equipment_type: str) -> bool:
        """
        Get the current state of equipment by reading from GPIO pin.
        This is the source of truth - no internal state is used.

        Args:
            equipment_type: The type of equipment ('blower', 'vibrofeeder')

        Returns:
            True if equipment is active (ON), False if inactive (OFF)
        """
        if equipment_type not in self.equipment_config:
            raise ValueError(f"Unknown equipment type: {equipment_type}")

        pin = self.equipment_config[equipment_type]['pin']

        # For active-low relays: LOW = ON, HIGH = OFF
        gpio_value = GPIO.input(pin)
        is_active = gpio_value == GPIO.LOW

        return is_active

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current state of all equipment by reading from GPIO pins.

        Returns:
            Dictionary with equipment states in shadow-compatible format:
            {
                'blower': {'is_active': True},
                'vibrofeeder': {'is_active': False}
            }
        """
        states = {}

        for equipment_type in self.equipment_config:
            is_active = self.get_state(equipment_type)
            states[equipment_type] = {'is_active': is_active}

        logging.debug(f"Current equipment states: {states}")
        return states

    def get_equipment_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed equipment information including current states.

        Returns:
            Dictionary with equipment info:
            {
                'blower': {
                    'name': 'Blower',
                    'pin': 17,
                    'is_active': True
                }
            }
        """
        info = {}

        for equipment_type, config in self.equipment_config.items():
            is_active = self.get_state(equipment_type)
            info[equipment_type] = {
                'name': config['name'],
                'pin': config['pin'],
                'is_active': is_active
            }

        return info

    def cleanup(self):
        """Clean up GPIO resources."""
        logging.info("Cleaning up GPIO")
        # Turn off all equipment before cleanup
        for equipment_type in self.equipment_config:
            self.set_state(equipment_type, False)
        GPIO.cleanup()

    def __del__(self):
        """Destructor to ensure GPIO cleanup."""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during cleanup