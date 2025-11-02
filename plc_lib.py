#!/usr/bin/env python3
"""
Delta DVP10SX PLC Communication Library

This module provides communication interface for Delta DVP10SX PLC via Modbus RTU protocol.
Supports reading/writing D registers, M coils, X inputs, and Y outputs.
"""

from pymodbus.client import ModbusSerialClient
from pymodbus import Framer
from pymodbus.exceptions import ModbusException
import logging
import time

logger = logging.getLogger(__name__)


class DeltaPLC:
    """
    Delta DVP10SX PLC Communication Class.

    Provides methods to communicate with Delta DVP10SX PLC using Modbus RTU protocol
    over serial connection. Supports reading and writing various PLC memory areas.

    Attributes:
        config (dict): PLC connection configuration
        client (ModbusSerialClient): Modbus client instance
        connected (bool): Connection status flag
    """
    
    D_OFFSET = 0x1000  # D registers
    M_OFFSET = 0x0800  # M coils
    X_OFFSET = 0x0400  # X inputs
    Y_OFFSET = 0x0500  # Y outputs
    
    def __init__(self, config=None):
        """
        Initialize PLC connection handler.

        Args:
            config (dict, optional): PLC connection configuration. If None, uses default settings.
                Required keys:
                - port (str): Serial port path (e.g., '/dev/ttyUSB0')
                - baudrate (int): Communication baud rate (default: 9600)
                - bytesize (int): Data bits (default: 7)
                - parity (str): Parity setting (default: 'E' for Even)
                - stopbits (int): Stop bits (default: 1)
                - timeout (int): Communication timeout in seconds (default: 3)
                - slave_address (int): Modbus slave address (default: 1)
        """
        if config is None:
            config = {
                'port': '/dev/ttyUSB0',
                'baudrate': 9600,
                'bytesize': 7,
                'parity': 'E',
                'stopbits': 1,
                'timeout': 3,
                'slave_address': 1
            }
        self.config = config
        self.client = None
        self.connected = False
    
    def connect(self):
        """
        Establish serial connection to the PLC.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            self.client = ModbusSerialClient(
                port=self.config['port'],
                framer=Framer.ASCII,
                baudrate=self.config['baudrate'],
                bytesize=self.config['bytesize'],
                parity=self.config['parity'],
                stopbits=self.config['stopbits'],
                timeout=self.config['timeout']
            )
            
            if self.client.connect():
                self.connected = True
                logger.info(f"Connected to PLC at {self.config['port']}")
                return True
            else:
                self.connected = False
                logger.error(f"Failed to connect to {self.config['port']}")
                return False
        except Exception as e:
            self.connected = False
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close the serial connection to the PLC."""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Disconnected from PLC")
    
    def ensure_connected(self):
        """
        Ensure PLC connection is active, attempt reconnection if needed.

        Returns:
            bool: True if connected, False otherwise.
        """
        if not self.connected:
            return self.connect()
        return True
    
    def read_d_registers(self, start, count):
        """
        Read D registers from PLC.

        D registers are 16-bit data registers used for storing numerical values.

        Args:
            start (int): Starting D register address (e.g., 0 for D0)
            count (int): Number of consecutive registers to read

        Returns:
            list: List of register values, or None if read fails.
        """
        if not self.ensure_connected():
            return None
        try:
            response = self.client.read_holding_registers(
                address=self.D_OFFSET + start,
                count=count,
                slave=self.config['slave_address']
            )
            if hasattr(response, 'registers'):
                return response.registers
            logger.error(f"Error reading D{start}: {response}")
            return None
        except Exception as e:
            logger.error(f"Exception reading D{start}: {e}")
            return None
    
    def read_m_coils(self, start, count):
        """
        Read M coils (auxiliary relays) from PLC.

        M coils are binary (ON/OFF) internal relays used for control logic.

        Args:
            start (int): Starting M coil address (e.g., 0 for M0)
            count (int): Number of consecutive coils to read

        Returns:
            list: List of boolean values, or None if read fails.
        """
        if not self.ensure_connected():
            return None
        try:
            response = self.client.read_coils(
                address=self.M_OFFSET + start,
                count=count,
                slave=self.config['slave_address']
            )
            if hasattr(response, 'bits'):
                return response.bits[:count]
            logger.error(f"Error reading M{start}: {response}")
            return None
        except Exception as e:
            logger.error(f"Exception reading M{start}: {e}")
            return None
    
    def read_x_inputs(self, start, count):
        """
        Read X inputs (digital inputs) from PLC.

        Args:
            start (int): Starting X input address
            count (int): Number of consecutive inputs to read

        Returns:
            list: List of boolean values, or None if read fails.
        """
        if not self.ensure_connected():
            return None
        try:
            response = self.client.read_discrete_inputs(
                address=self.X_OFFSET + start,
                count=count,
                slave=self.config['slave_address']
            )
            if hasattr(response, 'bits'):
                return response.bits[:count]
            logger.error(f"Error reading X{start}: {response}")
            return None
        except Exception as e:
            logger.error(f"Exception reading X{start}: {e}")
            return None
    
    def read_y_outputs(self, start, count):
        """
        Read Y outputs (digital outputs) from PLC.

        Args:
            start (int): Starting Y output address
            count (int): Number of consecutive outputs to read

        Returns:
            list: List of boolean values, or None if read fails.
        """
        if not self.ensure_connected():
            return None
        try:
            response = self.client.read_coils(
                address=self.Y_OFFSET + start,
                count=count,
                slave=self.config['slave_address']
            )
            if hasattr(response, 'bits'):
                return response.bits[:count]
            logger.error(f"Error reading Y{start}: {response}")
            return None
        except Exception as e:
            logger.error(f"Exception reading Y{start}: {e}")
            return None
    
    def write_d_register(self, address, value):
        """
        Write value to a D register.

        Args:
            address (int): D register address
            value (int): Value to write (0-65535)

        Returns:
            bool: True if write successful, False otherwise.
        """
        if not self.ensure_connected():
            return False
        try:
            response = self.client.write_register(
                address=self.D_OFFSET + address,
                value=value,
                slave=self.config['slave_address']
            )
            if not response.isError():
                logger.info(f"Wrote D{address} = {value}")
                return True
            logger.error(f"Error writing D{address}: {response}")
            return False
        except Exception as e:
            logger.error(f"Exception writing D{address}: {e}")
            return False
    
    def write_m_coil(self, address, state):
        """
        Write state to an M coil with verification.

        Uses write_coils method for better compatibility with Delta DVP PLC.
        Automatically verifies the write operation and retries with alternative method if needed.

        Args:
            address (int): M coil address
            state (bool): State to write (True/False or 1/0)

        Returns:
            bool: True if write successful, False otherwise.
        """
        if not self.ensure_connected():
            return False
        
        try:
            # Try Method 1: write_coils (plural) - works better with Delta
            response = self.client.write_coils(
                address=self.M_OFFSET + address,
                values=[bool(state)],
                slave=self.config['slave_address']
            )
            
            if not response.isError():
                logger.info(f"Wrote M{address} = {'ON' if state else 'OFF'}")
                # Verify
                time.sleep(0.05)
                verify = self.read_m_coils(address, 1)
                if verify and verify[0] == state:
                    return True
                else:
                    logger.warning(f"M{address} write verification failed")
                    # Try alternative method
                    return self._write_m_coil_alt(address, state)
            
            logger.error(f"Error writing M{address}: {response}")
            return False
            
        except Exception as e:
            logger.error(f"Exception writing M{address}: {e}")
            return False
    
    def _write_m_coil_alt(self, address, state):
        """
        Alternative M coil write method using write_coil (singular).

        Args:
            address (int): M coil address
            state (bool): State to write

        Returns:
            bool: True if write successful, False otherwise.
        """
        try:
            response = self.client.write_coil(
                address=self.M_OFFSET + address,
                value=bool(state),
                slave=self.config['slave_address']
            )

            if not response.isError():
                logger.info(f"Wrote M{address} = {'ON' if state else 'OFF'} (alt method)")
                return True
            return False
        except Exception as e:
            logger.error(f"Exception in alternative M coil write: {e}")
            return False
    
    def write_y_output(self, address, state):
        """
        Write state to a Y output.

        Args:
            address (int): Y output address
            state (bool): State to write (True/False or 1/0)

        Returns:
            bool: True if write successful, False otherwise.
        """
        if not self.ensure_connected():
            return False
        try:
            response = self.client.write_coil(
                address=self.Y_OFFSET + address,
                value=state,
                slave=self.config['slave_address']
            )
            if not response.isError():
                logger.info(f"Wrote Y{address} = {'ON' if state else 'OFF'}")
                return True
            logger.error(f"Error writing Y{address}: {response}")
            return False
        except Exception as e:
            logger.error(f"Exception writing Y{address}: {e}")
            return False
    
    def get_all_status(self):
        """
        Read all PLC memory areas and return comprehensive status.

        Returns:
            dict: Dictionary containing timestamp, connection status, and all memory values,
                  or None if read fails.
        """
        from datetime import datetime
        data = {
            'timestamp': datetime.now().isoformat(),
            'connected': self.connected,
            'd_registers': {},
            'm_coils': {},
            'x_inputs': {},
            'y_outputs': {}
        }
        try:
            d_values = self.read_d_registers(0, 100)
            if d_values:
                for i, val in enumerate(d_values):
                    data['d_registers'][f'D{i}'] = val
            
            m_values = self.read_m_coils(0, 100)
            if m_values:
                for i, val in enumerate(m_values):
                    data['m_coils'][f'M{i}'] = bool(val)
            
            x_values = self.read_x_inputs(0, 8)
            if x_values:
                for i, val in enumerate(x_values):
                    data['x_inputs'][f'X{i}'] = bool(val)
            
            y_values = self.read_y_outputs(0, 8)
            if y_values:
                for i, val in enumerate(y_values):
                    data['y_outputs'][f'Y{i}'] = bool(val)
            
            return data
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None
