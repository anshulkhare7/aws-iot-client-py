"""
Equipment Status Reader Module

This module provides functionality to read equipment status data from a JSON file.

NOTE: This is a temporary implementation. In the future, this will be replaced
with serial communication to read real-time equipment status directly from hardware.
"""

import json
import os


class EquipmentStatusReader:
    """
    Reads equipment status data from a JSON file.

    This class provides a simple interface to read equipment status information
    from a JSON file. Each equipment entry contains an 'id' and 'status' field.

    NOTE: This is a temporary implementation that will be replaced with serial
    communication in future versions.

    Attributes:
        file_path (str): Path to the JSON file containing equipment status data.
    """

    def __init__(self, file_path="data/status.json"):
        """
        Initialize the EquipmentStatusReader.

        Args:
            file_path (str): Path to the JSON file containing equipment status.
                           Defaults to "data/status.json".
        """
        self.file_path = file_path

    def read_status(self):
        """
        Read and parse equipment status from the JSON file.

        Returns:
            list: A list of dictionaries, where each dictionary contains
                  equipment status information with 'id' and 'status' fields.
                  Returns an empty list if the file cannot be read or parsed.

        Raises:
            No exceptions are raised. Errors are printed to stdout and an
            empty list is returned.
        """
        try:
            if not os.path.exists(self.file_path):
                print(f"Error: Equipment status file not found: {self.file_path}")
                return []

            with open(self.file_path, 'r') as file:
                equipment_list = json.load(file)

            if not isinstance(equipment_list, list):
                print(f"Error: Expected array in {self.file_path}, got {type(equipment_list).__name__}")
                return []

            return equipment_list

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in {self.file_path}: {e}")
            return []
        except Exception as e:
            print(f"Error reading equipment status file: {e}")
            return []
