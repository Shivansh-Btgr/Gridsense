"""
API routes for signal timing optimization
"""

from flask import Blueprint, request, jsonify
import os

from backend.uxsim.signal_optimizer import signal_optimizer, UXSIM_AVAILABLE
from config.settings import OUTPUTS_DIR

signal_bp = Blueprint('signal', __name__)


@signal_bp.route('/api/signal/load-network', methods=['POST'])
def load_network():
    """Load OSM network and identify signal candidates"""
    if not UXSIM_AVAILABLE:
        return jsonify({'error': 'UXsim not available'}), 503
    
    data = request.json
    north = float(data.get('north'))
    south = float(data.get('south'))
    east = float(data.get('east'))
    west = float(data.get('west'))
    osm_filter = data.get('filter', '["highway"~"primary|secondary"]')
    
    try:
        result = signal_optimizer.load_network_from_osm(north, south, east, west, osm_filter)
        
        # Get signal candidates
        signal_candidates = signal_optimizer.signal_nodes
        
        return jsonify({
            'success': True,
            'network': result,
            'signal_candidates': signal_candidates
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@signal_bp.route('/api/signal/run-optimization', methods=['POST'])
def run_optimization():
    """Run simulation with custom signal timings"""
    if not UXSIM_AVAILABLE:
        return jsonify({'error': 'UXsim not available'}), 503
    
    data = request.json
    signal_settings = data.get('signal_settings', [])
    duration = int(data.get('duration', 3600))
    demand = int(data.get('demand', 2000))
    
    try:
        # Create world with signals
        world_result = signal_optimizer.create_world_with_signals(
            signal_settings=signal_settings,
            duration=duration,
            demand_volume=demand
        )
        
        # Run simulation
        results = signal_optimizer.run_simulation(output_dir=OUTPUTS_DIR)
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@signal_bp.route('/api/signal/run-mode-comparison', methods=['POST'])
def run_mode_comparison():
    """Run transportation mode comparison simulation"""
    if not UXSIM_AVAILABLE:
        return jsonify({'error': 'UXsim not available'}), 503
    
    data = request.json
    signal_settings = data.get('signal_settings', [])
    duration = int(data.get('duration', 3600))
    demand = int(data.get('demand', 2000))
    rideshare_percent = int(data.get('rideshare_percent', 50))
    num_taxis = int(data.get('num_taxis', 100))
    
    try:
        # Run mode comparison
        results = signal_optimizer.run_mode_comparison(
            signal_settings=signal_settings,
            duration=duration,
            demand_volume=demand,
            rideshare_percent=rideshare_percent,
            num_taxis=num_taxis,
            output_dir=OUTPUTS_DIR
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
