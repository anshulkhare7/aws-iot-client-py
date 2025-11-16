#!/usr/bin/env python3
"""
Delta DVP10SX PLC Communication Library
FINAL VERSION - Corrected for Actual Ladder Logic (M100-M103 support)
"""

from pymodbus.client import ModbusSerialClient
from pymodbus import Framer
from pymodbus.exceptions import ModbusException
import logging
import time

logger = logging.getLogger(__name__)

class DeltaPLC:
    """Delta DVP10SX PLC Communication Class"""
    
    D_OFFSET = 0x1000  # D registers
    M_OFFSET = 0x0800  # M coils
    X_OFFSET = 0x0400  # X inputs
    Y_OFFSET = 0x0500  # Y outputs
    
    def __init__(self, config=None):
        if config is None:
            config = {
                'port': '/dev/ttyACM0',
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
        
        # ========================================
        # ACTUAL LADDER LOGIC MAPPING:
        # X2 | M1 → M1  (REMOTE: X2 physical OR M1 software)
        # X1 | M2 → M2  (AUTO: X1 physical OR M2 software)
        # Y0 = M1 AND M100 AND (NOT M101)
        # Y1 = M1 AND M102 AND (NOT M103)
        # ========================================
        
        # X INPUTS (Physical Switches - READ ONLY)
        self.X_TRIGGER = 0      # X0 = Trigger (sets M1)
        self.X_AUTO = 1         # X1 = AUTO mode physical switch
        self.X_REMOTE = 2       # X2 = REMOTE mode physical switch
        
        # M COILS (Software Flags)
        self.M_REMOTE_CTRL = 1  # M1 = X2 OR M1 (REMOTE control)
        self.M_AUTO_CTRL = 2    # M2 = X1 OR M2 (AUTO control)
        self.M_MANUAL = 3       # M3 = MANUAL
        self.M_VIBRO_CTRL = 4   # M4 = Vibrofeeder control
        
        # CRITICAL M COILS FOR OUTPUT CONTROL:
        self.M_BLOWER_ENABLE = 100      # M100 = Blower enable (Y0 = M1 AND M100 AND NOT M101)
        self.M_BLOWER_INTERLOCK = 101   # M101 = Blower interlock (must be OFF)
        self.M_VIBRO_ENABLE = 102       # M102 = Vibrofeeder enable (Y1 = M1 AND M102 AND NOT M103)
        self.M_VIBRO_INTERLOCK = 103    # M103 = Vibrofeeder interlock (must be OFF)
        
        # Y OUTPUTS (Physical Devices)
        self.Y_BLOWER = 0       # Y0 = Blower motor
        self.Y_VIBRO = 1        # Y1 = Vibrofeeder motor
        
        # D REGISTERS (Data Values)
        self.D_VIBRO_GRAMS = 1  # D1 = Vibrofeeder grams/tonne (0-2000)
    
    def connect(self):
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
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Disconnected from PLC")
    
    def ensure_connected(self):
        if not self.connected:
            return self.connect()
        return True
    
    def read_d_registers(self, start, count):
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
        """Write M coil with verification"""
        if not self.ensure_connected():
            return False
        
        try:
            response = self.client.write_coils(
                address=self.M_OFFSET + address,
                values=[bool(state)],
                slave=self.config['slave_address']
            )
            
            if not response.isError():
                logger.info(f"Wrote M{address} = {'ON' if state else 'OFF'}")
                time.sleep(0.05)
                verify = self.read_m_coils(address, 1)
                if verify and verify[0] == state:
                    return True
                else:
                    logger.warning(f"M{address} write verification failed")
                    return self._write_m_coil_alt(address, state)
            
            logger.error(f"Error writing M{address}: {response}")
            return False
            
        except Exception as e:
            logger.error(f"Exception writing M{address}: {e}")
            return False
    
    def _write_m_coil_alt(self, address, state):
        """Alternative M coil write method"""
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
        except:
            return False
    
    def write_y_output(self, address, state):
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
        """Get complete PLC status"""
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
            # Read D registers (0-10)
            d_values = self.read_d_registers(0, 10)
            if d_values:
                for i, val in enumerate(d_values):
                    data['d_registers'][f'D{i}'] = val
            
            # Read M coils (0-10)
            m_values = self.read_m_coils(0, 10)
            if m_values:
                for i, val in enumerate(m_values):
                    data['m_coils'][f'M{i}'] = bool(val)
            
            # Read X inputs (0-8)
            x_values = self.read_x_inputs(0, 8)
            if x_values:
                for i, val in enumerate(x_values):
                    data['x_inputs'][f'X{i}'] = bool(val)
            
            # Read Y outputs (0-8)
            y_values = self.read_y_outputs(0, 8)
            if y_values:
                for i, val in enumerate(y_values):
                    data['y_outputs'][f'Y{i}'] = bool(val)
            
            return data
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None
