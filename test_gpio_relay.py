#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import sys

class RelayTester:
    def __init__(self):
        # GPIO pins for your relay connections
        self.RELAY1_PIN = 17  # Connected to IN1
        self.RELAY2_PIN = 27  # Connected to IN2

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
        GPIO.setup(self.RELAY1_PIN, GPIO.OUT)
        GPIO.setup(self.RELAY2_PIN, GPIO.OUT)

        # Initialize relays to OFF (HIGH = OFF for active-low relays)
        GPIO.output(self.RELAY1_PIN, GPIO.HIGH)
        GPIO.output(self.RELAY2_PIN, GPIO.HIGH)
        print("GPIO initialized. Relays OFF.")

    def relay1_on(self):
        """Turn Relay 1 ON"""
        GPIO.output(self.RELAY1_PIN, GPIO.LOW)
        print("Relay 1: ON")

    def relay1_off(self):
        """Turn Relay 1 OFF"""
        GPIO.output(self.RELAY1_PIN, GPIO.HIGH)
        print("Relay 1: OFF")

    def relay2_on(self):
        """Turn Relay 2 ON"""
        GPIO.output(self.RELAY2_PIN, GPIO.LOW)
        print("Relay 2: ON")

    def relay2_off(self):
        """Turn Relay 2 OFF"""
        GPIO.output(self.RELAY2_PIN, GPIO.HIGH)
        print("Relay 2: OFF")

    def test_sequence(self):
        """Run a test sequence"""
        print("\n=== Starting Relay Test Sequence ===")

        # Test Relay 1
        print("Testing Relay 1...")
        self.relay1_on()
        time.sleep(2)
        self.relay1_off()
        time.sleep(1)

        # Test Relay 2
        print("Testing Relay 2...")
        self.relay2_on()
        time.sleep(2)
        self.relay2_off()
        time.sleep(1)

        # Test both together
        print("Testing both relays...")
        self.relay1_on()
        self.relay2_on()
        time.sleep(2)
        self.relay1_off()
        self.relay2_off()

        print("=== Test sequence complete ===")

    def interactive_mode(self):
        """Interactive mode for manual testing"""
        print("\n=== Interactive Mode ===")
        print("Commands: 1on, 1off, 2on, 2off, both_on, both_off, test, quit")

        while True:
            try:
                cmd = input("Enter command: ").strip().lower()

                if cmd == "1on":
                    self.relay1_on()
                elif cmd == "1off":
                    self.relay1_off()
                elif cmd == "2on":
                    self.relay2_on()
                elif cmd == "2off":
                    self.relay2_off()
                elif cmd == "both_on":
                    self.relay1_on()
                    self.relay2_on()
                elif cmd == "both_off":
                    self.relay1_off()
                    self.relay2_off()
                elif cmd == "test":
                    self.test_sequence()
                elif cmd == "quit":
                    break
                else:
                    print("Unknown command!")

            except KeyboardInterrupt:
                break

    def cleanup(self):
        """Clean up GPIO"""
        GPIO.output(self.RELAY1_PIN, GPIO.HIGH)  # Turn off relays
        GPIO.output(self.RELAY2_PIN, GPIO.HIGH)
        GPIO.cleanup()
        print("GPIO cleaned up.")

def main():
    tester = RelayTester()

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "interactive":
            tester.interactive_mode()
        else:
            tester.test_sequence()

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()