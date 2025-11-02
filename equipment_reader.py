"""
Equipment Reader Module

This module provides functionality to read equipment data from PLC via Modbus.
"""

import logging

logger = logging.getLogger(__name__)


class EquipmentReader:
    """
    Reads equipment data from PLC via Modbus communication.

    This class provides an interface to read equipment information
    (status and data) directly from PLC registers and coils. Equipment
    configuration is read from the ConfigManager.

    Attributes:
        config_manager: Configuration manager instance containing equipment config
        plc_reader: PLC communication instance for reading registers/coils
    """

    def __init__(self, config_manager, plc_reader):
        """
        Initialize the EquipmentReader.

        Args:
            config_manager: ConfigManager instance with equipment configuration
            plc_reader: DeltaPLC instance for PLC communication
        """
        self.config_manager = config_manager
        self.plc_reader = plc_reader

    def _parse_register(self, register_str):
        """
        Parse register string to extract type and address.

        Args:
            register_str (str): Register identifier (e.g., "Y0", "M5", "D10")

        Returns:
            tuple: (register_type, address) or (None, None) if invalid

        Examples:
            "Y0" -> ("Y", 0)
            "M10" -> ("M", 10)
            "D5" -> ("D", 5)
        """
        if not register_str or len(register_str) < 2:
            return None, None

        register_type = register_str[0].upper()
        try:
            address = int(register_str[1:])
            return register_type, address
        except ValueError:
            return None, None

    def _read_register(self, register_str, equipment_id):
        """
        Read a single register from PLC.

        Args:
            register_str (str): Register identifier (e.g., "Y0", "M5", "D10")
            equipment_id (str): Equipment ID for logging purposes

        Returns:
            Value from register (bool for coils, int for D registers), or None if read fails
        """
        # Parse register to determine type and address
        reg_type, address = self._parse_register(register_str)

        if reg_type is None or address is None:
            logger.error(f"Invalid register format '{register_str}' for {equipment_id}")
            return None

        # Read from PLC based on register type
        try:
            result = None
            if reg_type == 'Y':
                # Y outputs - read using read_y_outputs
                result = self.plc_reader.read_y_outputs(address, 1)
            elif reg_type == 'M':
                # M coils - read using read_m_coils
                result = self.plc_reader.read_m_coils(address, 1)
            elif reg_type == 'X':
                # X inputs - read using read_x_inputs
                result = self.plc_reader.read_x_inputs(address, 1)
            elif reg_type == 'D':
                # D registers - read using read_d_registers
                result = self.plc_reader.read_d_registers(address, 1)
            else:
                logger.error(f"Unsupported register type '{reg_type}' for {equipment_id}")
                return None

            if result is not None and len(result) > 0:
                return result[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Error reading {register_str} for {equipment_id}: {e}")
            return None

    def read(self):
        """
        Read and parse equipment status and data from PLC.

        Returns:
            list: A list of dictionaries, where each dictionary contains:
                  - 'id': Equipment ID
                  - 'status': Boolean status from Y/M/X registers (optional)
                  - 'data': Integer value from D registers (optional)
                  Returns an empty list if PLC cannot be read or on error.
        """
        try:
            # Get equipment configuration
            equipment_list = self.config_manager.equipment_config

            if not equipment_list:
                logger.info("No equipment configured")
                return []

            status_results = []

            # Iterate through each equipment
            for equipment in equipment_list:
                equipment_id = equipment.get('id', 'unknown')
                registers = equipment.get('registers', {})

                # Build equipment result
                equipment_result = {'id': equipment_id}

                # Read status register if configured
                status_register = registers.get('status')
                if status_register:
                    status_value = self._read_register(status_register, equipment_id)
                    if status_value is not None:
                        equipment_result['status'] = status_value
                    else:
                        logger.warning(f"Failed to read status register {status_register} for {equipment_id}")

                # Read data register if configured
                data_register = registers.get('data')
                if data_register:
                    data_value = self._read_register(data_register, equipment_id)
                    if data_value is not None:
                        equipment_result['data'] = data_value
                    else:
                        logger.warning(f"Failed to read data register {data_register} for {equipment_id}")

                # Only add to results if we successfully read at least one value
                if 'status' in equipment_result or 'data' in equipment_result:
                    status_results.append(equipment_result)

            return status_results

        except Exception as e:
            logger.error(f"Error reading equipment status from PLC: {e}")
            return []
