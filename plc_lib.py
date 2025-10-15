#!/usr/bin/env python3
"""
Delta DVP10SX PLC Communication Library
Shared between test script and API server
"""

from pymodbus.client import ModbusSerialClient
from pymodbus import Framer
from pymodbus.exceptions import ModbusException
import logging

logger = logging.getLogger(__name__)

class DeltaPLC:
    """Delta DVP10SX PLC Communication Class"""
    
    # Delta DVP Modbus Address Offsets
    D_OFFSET = 0x1000  # D registers
    M_OFFSET = 0x0800  # M coils
    X_OFFSET = 0x0400  # X inputs
    Y_OFFSET = 0x0500  # Y outputs
    
    def __init__(self, config=None):
        """
        Initialize PLC connection
        
        Args:
            config: Dict with connection parameters
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
        """Connect to PLC"""
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
        """Disconnect from PLC"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Disconnected from PLC")
    
    def ensure_connected(self):
        """Ensure connection is active, reconnect if needed"""
        if not self.connected:
            return self.connect()
        return True
    
    # ==================== READ OPERATIONS ====================
    
    def read_d_registers(self, start, count):
        """
        Read D registers
        
        Args:
            start: Starting address (0 for D0)
            count: Number of registers
            
        Returns:
            list: Register values or None on error
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
        """Read M coils (internal relays)"""
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
        """Read X inputs (digital inputs)"""
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
        """Read Y outputs (digital outputs)"""
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
    
    # ==================== WRITE OPERATIONS ====================
    
    def write_d_register(self, address, value):
        """
        Write single D register
        
        Args:
            address: D register number (100 for D100)
            value: Value to write (0-65535)
            
        Returns:
            bool: Success status
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
        Write single M coil
        
        Args:
            address: M coil number (0 for M0)
            state: True (ON) or False (OFF)
            
        Returns:
            bool: Success status
        """
        if not self.ensure_connected():
            return False
        
        try:
            response = self.client.write_coil(
                address=self.M_OFFSET + address,
                value=state,
                slave=self.config['slave_address']
            )
            
            if not response.isError():
                logger.info(f"Wrote M{address} = {'ON' if state else 'OFF'}")
                return True
            
            logger.error(f"Error writing M{address}: {response}")
            return False
            
        except Exception as e:
            logger.error(f"Exception writing M{address}: {e}")
            return False
    
    def write_y_output(self, address, state):
        """
        Write single Y output
        
        Args:
            address: Y output number (0 for Y0)
            state: True (ON) or False (OFF)
            
        Returns:
            bool: Success status
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
    
    # ==================== BULK OPERATIONS ====================
    
    def get_all_status(self):
        """
        Get complete PLC status
        
        Returns:
            dict: All PLC data or None on error
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
            # Read D0-D99
            d_values = self.read_d_registers(0, 100)
            if d_values:
                for i, val in enumerate(d_values):
                    data['d_registers'][f'D{i}'] = val
            
            # Read M0-M99
            m_values = self.read_m_coils(0, 100)
            if m_values:
                for i, val in enumerate(m_values):
                    data['m_coils'][f'M{i}'] = bool(val)
            
            # Read X0-X7
            x_values = self.read_x_inputs(0, 8)
            if x_values:
                for i, val in enumerate(x_values):
                    data['x_inputs'][f'X{i}'] = bool(val)
            
            # Read Y0-Y7
            y_values = self.read_y_outputs(0, 8)
            if y_values:
                for i, val in enumerate(y_values):
                    data['y_outputs'][f'Y{i}'] = bool(val)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None
