"""
UXsim OpenStreetMap simulation API routes
"""

from flask import Blueprint, request, jsonify, send_file
import os
import threading

from backend.uxsim.osm_scenarios import osm_scenarios, UXSIM_AVAILABLE
from config.settings import OUTPUTS_DIR

uxsim_bp = Blueprint('uxsim', __name__)

# Global simulation state
simulation_running = False
simulation_progress = 0
simulation_results = None


@uxsim_bp.route('/api/uxsim/presets', methods=['GET'])
def get_presets():
    """Get available preset OSM locations"""
    if not UXSIM_AVAILABLE:
        return jsonify({'error': 'UXsim not available'}), 503
    
    presets = osm_scenarios.get_available_presets()
    return jsonify({'presets': presets})


@uxsim_bp.route('/api/uxsim/validate-bounds', methods=['POST'])
def validate_bounds():
    """Validate custom map bounds"""
    if not UXSIM_AVAILABLE:
        return jsonify({'error': 'UXsim not available'}), 503
    
    data = request.json
    north = float(data.get('north'))
    south = float(data.get('south'))
    east = float(data.get('east'))
    west = float(data.get('west'))
    
    valid, message = osm_scenarios.validate_bounds(north, south, east, west)
    
    return jsonify({
        'valid': valid,
        'message': message
    })


@uxsim_bp.route('/api/uxsim/run-simulation', methods=['POST'])
def run_simulation():
    """Run OSM-based traffic simulation"""
    global simulation_running, simulation_results
    
    if not UXSIM_AVAILABLE:
        return jsonify({'error': 'UXsim not installed. Please install: pip install uxsim'}), 503
    
    if simulation_running:
        return jsonify({'error': 'Simulation already running'}), 400
    
    data = request.json
    
    scenario_key = data.get('scenario_key')
    custom_bounds = data.get('custom_bounds')
    duration = int(data.get('duration', 3600))  # Default 1 hour
    demand = int(data.get('demand', 3000))
    custom_filter = data.get('custom_filter')  # Road type filter
    
    # Validate inputs
    if not scenario_key and not custom_bounds:
        return jsonify({'error': 'Must provide either scenario_key or custom_bounds'}), 400
    
    if custom_bounds:
        valid, message = osm_scenarios.validate_bounds(
            custom_bounds['north'],
            custom_bounds['south'],
            custom_bounds['east'],
            custom_bounds['west']
        )
        if not valid:
            return jsonify({'error': message}), 400
    
    try:
        # Run simulation synchronously (can take a while)
        print(f"Starting OSM simulation: {scenario_key or 'custom'}")
        
        results = osm_scenarios.run_osm_simulation(
            scenario_key=scenario_key,
            custom_bounds=custom_bounds,
            duration=duration,
            demand_volume=demand,
            custom_filter=custom_filter,
            output_dir=OUTPUTS_DIR
        )
        
        simulation_results = results
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        print(f"Simulation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@uxsim_bp.route('/api/uxsim/download-animation/<path:filename>')
def download_animation(filename):
    """Download generated animation file"""
    try:
        # Security: Ensure filename is within outputs directory
        safe_path = os.path.normpath(os.path.join(OUTPUTS_DIR, filename))
        
        if not safe_path.startswith(os.path.normpath(OUTPUTS_DIR)):
            return jsonify({'error': 'Invalid file path'}), 403
        
        if os.path.exists(safe_path):
            return send_file(safe_path, as_attachment=True)
        
        return jsonify({'error': 'File not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@uxsim_bp.route('/api/uxsim/status', methods=['GET'])
def get_status():
    """Get simulation status"""
    return jsonify({
        'running': simulation_running,
        'progress': simulation_progress,
        'uxsim_available': UXSIM_AVAILABLE
    })
