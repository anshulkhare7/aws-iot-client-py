#!/usr/bin/env python3
"""
Delta DVP10SX PLC - REST API Server
Provides web API for dashboard control
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from plc_lib import DeltaPLC
import logging
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pi/plc_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web dashboard

# Initialize PLC connection
plc = DeltaPLC()

# ==================== API ENDPOINTS ====================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get complete PLC status"""
    try:
        status = plc.get_all_status()
        if status:
            return jsonify(status), 200
        else:
            return jsonify({'error': 'Failed to read PLC'}), 500
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/d/<int:address>', methods=['GET', 'POST'])
def d_register(address):
    """Read or write D register"""
    try:
        if request.method == 'GET':
            # Read single register
            values = plc.read_d_registers(address, 1)
            if values:
                return jsonify({'address': f'D{address}', 'value': values[0]}), 200
            else:
                return jsonify({'error': f'Failed to read D{address}'}), 500
        
        elif request.method == 'POST':
            # Write register
            data = request.get_json()
            value = int(data.get('value', 0))
            
            if 0 <= value <= 65535:
                if plc.write_d_register(address, value):
                    return jsonify({'success': True, 'address': f'D{address}', 'value': value}), 200
                else:
                    return jsonify({'error': f'Failed to write D{address}'}), 500
            else:
                return jsonify({'error': 'Value must be 0-65535'}), 400
                
    except Exception as e:
        logger.error(f"D register error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/m/<int:address>', methods=['GET', 'POST'])
def m_coil(address):
    """Read or write M coil"""
    try:
        if request.method == 'GET':
            # Read single coil
            values = plc.read_m_coils(address, 1)
            if values is not None:
                return jsonify({'address': f'M{address}', 'state': bool(values[0])}), 200
            else:
                return jsonify({'error': f'Failed to read M{address}'}), 500
        
        elif request.method == 'POST':
            # Write coil
            data = request.get_json()
            state = bool(data.get('state', False))
            
            if plc.write_m_coil(address, state):
                return jsonify({'success': True, 'address': f'M{address}', 'state': state}), 200
            else:
                return jsonify({'error': f'Failed to write M{address}'}), 500
                
    except Exception as e:
        logger.error(f"M coil error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/y/<int:address>', methods=['GET', 'POST'])
def y_output(address):
    """Read or write Y output"""
    try:
        if request.method == 'GET':
            # Read single output
            values = plc.read_y_outputs(address, 1)
            if values is not None:
                return jsonify({'address': f'Y{address}', 'state': bool(values[0])}), 200
            else:
                return jsonify({'error': f'Failed to read Y{address}'}), 500
        
        elif request.method == 'POST':
            # Write output
            data = request.get_json()
            state = bool(data.get('state', False))
            
            if plc.write_y_output(address, state):
                return jsonify({'success': True, 'address': f'Y{address}', 'state': state}), 200
            else:
                return jsonify({'error': f'Failed to write Y{address}'}), 500
                
    except Exception as e:
        logger.error(f"Y output error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/x/<int:address>', methods=['GET'])
def x_input(address):
    """Read X input (read-only)"""
    try:
        values = plc.read_x_inputs(address, 1)
        if values is not None:
            return jsonify({'address': f'X{address}', 'state': bool(values[0])}), 200
        else:
            return jsonify({'error': f'Failed to read X{address}'}), 500
    except Exception as e:
        logger.error(f"X input error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to PLC"""
    try:
        if plc.connect():
            return jsonify({'success': True, 'message': 'Connected to PLC'}), 200
        else:
            return jsonify({'error': 'Failed to connect'}), 500
    except Exception as e:
        logger.error(f"Connect error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from PLC"""
    try:
        plc.disconnect()
        return jsonify({'success': True, 'message': 'Disconnected from PLC'}), 200
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== BULK OPERATIONS ====================

@app.route('/api/bulk/m', methods=['POST'])
def bulk_write_m():
    """Write multiple M coils at once"""
    try:
        data = request.get_json()
        coils = data.get('coils', {})  # {'0': true, '3': false, ...}
        
        results = {}
        for address_str, state in coils.items():
            address = int(address_str)
            success = plc.write_m_coil(address, bool(state))
            results[f'M{address}'] = success
        
        return jsonify({'results': results}), 200
        
    except Exception as e:
        logger.error(f"Bulk M write error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bulk/y', methods=['POST'])
def bulk_write_y():
    """Write multiple Y outputs at once"""
    try:
        data = request.get_json()
        outputs = data.get('outputs', {})
        
        results = {}
        for address_str, state in outputs.items():
            address = int(address_str)
            success = plc.write_y_output(address, bool(state))
            results[f'Y{address}'] = success
        
        return jsonify({'results': results}), 200
        
    except Exception as e:
        logger.error(f"Bulk Y write error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== STARTUP ====================

if __name__ == '__main__':
    logger.info("Starting PLC API Server...")
    
    # Connect to PLC on startup
    if plc.connect():
        logger.info("PLC connected successfully")
    else:
        logger.warning("PLC connection failed - will retry on first request")
    
    # Run Flask server
    # For production, use gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 plc_api:app
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,
        debug=False,     # Set to False in production
        threaded=True    # Handle multiple requests
    )
