#!/usr/bin/env python3

import os
import json
import logging
import signal
import sys
import threading
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from shadow_device_controller import ShadowDeviceController
from equipment_controller import EquipmentController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
app = Flask(__name__)
CORS(app)
shadow_controller = None
startup_complete = False

def initialize_shadow_controller():
    """Initialize the shadow controller in a background thread"""
    global shadow_controller, startup_complete

    try:
        logger.info("Initializing Shadow Device Controller...")

        # Create equipment controller
        equipment_controller = EquipmentController()

        # Create shadow controller
        shadow_controller = ShadowDeviceController(
            config_file="config/device.json",
            equipment_controller=equipment_controller
        )

        # Start the shadow controller
        success = shadow_controller.start()

        if success:
            logger.info("Shadow Device Controller started successfully")
            startup_complete = True
        else:
            logger.error("Failed to start Shadow Device Controller")

    except Exception as e:
        logger.error(f"Error initializing Shadow Device Controller: {e}")

def cleanup_on_exit():
    """Cleanup function for graceful shutdown"""
    global shadow_controller

    logger.info("Cleaning up...")

    if shadow_controller:
        shadow_controller.stop()

    logger.info("Cleanup complete")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}. Shutting down...")
    cleanup_on_exit()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    global startup_complete

    status = "healthy" if startup_complete and shadow_controller else "initializing"

    return jsonify({
        'status': status,
        'startup_complete': startup_complete,
        'shadow_controller': shadow_controller is not None,
        'timestamp': int(time.time())
    })

# Equipment status endpoint
@app.route('/equipment/status', methods=['GET'])
def get_equipment_status():
    """Get status of all equipment"""
    try:
        if not shadow_controller:
            return jsonify({
                'success': False,
                'error': 'Shadow controller not initialized',
                'message': 'Service is still starting up'
            }), 503

        # Get states directly from GPIO (source of truth)
        states = shadow_controller.get_equipment_states()

        return jsonify({
            'success': True,
            'data': {
                'equipment': states,
                'timestamp': int(time.time())
            }
        })

    except Exception as e:
        logger.error(f"Error getting equipment status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get equipment status',
            'message': str(e)
        }), 500

# Equipment control endpoint
@app.route('/equipment/control', methods=['POST'])
def control_equipment():
    """Control equipment (turn on/off)"""
    try:
        if not shadow_controller:
            return jsonify({
                'success': False,
                'error': 'Shadow controller not initialized',
                'message': 'Service is still starting up'
            }), 503

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'message': 'Request body must contain equipment control data'
            }), 400

        # Validate required fields
        if 'equipment_type' not in data or 'is_active' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields',
                'message': 'Request body must contain "equipment_type" and "is_active" fields'
            }), 400

        equipment_type = data['equipment_type']
        is_active = bool(data['is_active'])

        if equipment_type not in ['blower', 'vibrofeeder']:
            return jsonify({
                'success': False,
                'error': 'Invalid equipment type',
                'message': 'Equipment type must be "blower" or "vibrofeeder"'
            }), 400

        logger.info(f"Control request: {equipment_type} -> {'ON' if is_active else 'OFF'}")

        # Update equipment state and shadow
        actual_state = shadow_controller.update_equipment_state_and_shadow(
            equipment_type,
            is_active
        )

        return jsonify({
            'success': True,
            'data': {
                'equipment_type': equipment_type,
                'requested_state': is_active,
                'actual_state': actual_state,
                'timestamp': int(time.time())
            }
        })

    except Exception as e:
        logger.error(f"Error controlling equipment: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to control equipment',
            'message': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': f'The endpoint {request.method} {request.path} does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    # Start shadow controller in background thread
    init_thread = threading.Thread(target=initialize_shadow_controller, daemon=True)
    init_thread.start()

    # Get configuration
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting Flask application on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /equipment/status - Get all equipment status")
    logger.info("  POST /equipment/control - Control equipment")

    try:
        # Use threaded=True to handle multiple requests
        app.run(host=host, port=port, debug=debug, threaded=True)
    finally:
        cleanup_on_exit()