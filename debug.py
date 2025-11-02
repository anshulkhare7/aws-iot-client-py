#!/usr/bin/env python3
"""
Blower Control Debug Utility

Simple command-line utility to turn the blower (Y0 register) ON or OFF.

Usage:
    python debug.py on    # Turn blower ON
    python debug.py off   # Turn blower OFF
    python debug.py status # Read current blower status
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plc_lib import DeltaPLC
from config.config_manager import ConfigManager


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug.py [on|off|status]")
        print()
        print("Commands:")
        print("  on      - Turn blower ON (Y0=True)")
        print("  off     - Turn blower OFF (Y0=False)")
        print("  status  - Read current blower status")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command not in ['on', 'off', 'status']:
        print(f"Error: Invalid command '{command}'")
        print("Valid commands: on, off, status")
        sys.exit(1)

    try:
        # Load configuration and initialize PLC
        print("Loading configuration...")
        config = ConfigManager()

        print(f"Connecting to PLC at {config.plc_config.get('port', 'unknown')}...")
        plc = DeltaPLC(config.plc_config)

        if not plc.connect():
            print("ERROR: Failed to connect to PLC")
            print("Check:")
            print("  - PLC is powered on")
            print("  - Serial cable is connected")
            print("  - Port configuration in device.json is correct")
            sys.exit(1)

        print("✓ Connected to PLC")
        print()

        # Execute command
        if command == 'status':
            # Read current status
            print("Reading Y0 (Blower) status...")
            result = plc.read_y_outputs(0, 1)

            if result is None or len(result) == 0:
                print("ERROR: Failed to read Y0 register")
                sys.exit(1)

            status = result[0]
            status_text = "ON" if status else "OFF"
            print(f"✓ Blower (Y0) is currently: {status_text}")

        elif command == 'on':
            # Turn blower ON
            print("Turning blower ON (Y0=True)...")
            success = plc.write_y_output(0, True)

            if success:
                print("✓ Blower turned ON successfully")

                # Verify
                result = plc.read_y_outputs(0, 1)
                if result and result[0]:
                    print("✓ Verified: Y0 is ON")
                else:
                    print("⚠ Warning: Could not verify Y0 status")
            else:
                print("ERROR: Failed to turn blower ON")
                sys.exit(1)

        elif command == 'off':
            # Turn blower OFF
            print("Turning blower OFF (Y0=False)...")
            success = plc.write_y_output(0, False)

            if success:
                print("✓ Blower turned OFF successfully")

                # Verify
                result = plc.read_y_outputs(0, 1)
                if result and not result[0]:
                    print("✓ Verified: Y0 is OFF")
                else:
                    print("⚠ Warning: Could not verify Y0 status")
            else:
                print("ERROR: Failed to turn blower OFF")
                sys.exit(1)

        # Disconnect
        plc.disconnect()
        print()
        print("Disconnected from PLC")

    except FileNotFoundError as e:
        print(f"ERROR: Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
