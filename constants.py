"""Constants for the AWS IoT device controller."""

# MQTT Topics
TOPIC_HEARTBEAT = "devices/heartbeat"

# Timeouts (in seconds)
TIMEOUT_MQTT_PUBLISH = 10
TIMEOUT_CONNECTION_WAIT = 5
TIMEOUT_THREAD_JOIN = 5

# Status values
STATUS_ONLINE = "online"
STATUS_OFFLINE = "offline"

# Sleep intervals (in seconds)
SLEEP_INTERVAL_MAIN_LOOP = 1
SLEEP_INTERVAL_HEARTBEAT_CHECK = 1

# Default configuration
DEFAULT_CONFIG_FILE = "config/device.json"
