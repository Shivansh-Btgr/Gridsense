"""
Traffic simulation API routes
"""

from flask import Blueprint, request, jsonify
import threading

from backend.simulation.traffic_sim import simulation_manager, SUMO_AVAILABLE
from backend.simulation.network_mgr import network_manager
from config.settings import DEFAULT_SIMULATION_PARAMS

simulation_bp = Blueprint('simulation', __name__)


@simulation_bp.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Get available traffic network scenarios"""
    if not SUMO_AVAILABLE:
        return jsonify({'error': 'SUMO not available'}), 503
    
    scenarios = network_manager.get_available_scenarios()
    return jsonify({'scenarios': scenarios})


@simulation_bp.route('/api/generate-grid', methods=['POST'])
def generate_grid():
    """Generate custom grid network"""
    if not SUMO_AVAILABLE:
        return jsonify({'error': 'SUMO not available'}), 503
    
    data = request.json
    rows = int(data.get('rows', 3))
    cols = int(data.get('cols', 3))
    name = data.get('name', f'grid_{rows}x{cols}')
    
    try:
        network_id = network_manager.create_grid_network(rows, cols, name)
        return jsonify({
            'success': True,
            'message': f'Grid network {name} created successfully',
            'network_id': network_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@simulation_bp.route('/api/run-simulation', methods=['POST'])
def run_simulation():
    """Run traffic signal optimization simulation"""
    if not SUMO_AVAILABLE:
        return jsonify({'error': 'SUMO-RL not available. Please install sumo-rl package.'}), 503
    
    if simulation_manager.is_running:
        return jsonify({'error': 'Simulation already running'}), 400
    
    data = request.json
    
    # Get parameters with defaults
    params = {
        'episodes': int(data.get('episodes', DEFAULT_SIMULATION_PARAMS['episodes'])),
        'alpha': float(data.get('alpha', DEFAULT_SIMULATION_PARAMS['alpha'])),
        'gamma': float(data.get('gamma', DEFAULT_SIMULATION_PARAMS['gamma'])),
        'epsilon': float(data.get('epsilon', DEFAULT_SIMULATION_PARAMS['epsilon'])),
        'lamb': float(data.get('lambda', DEFAULT_SIMULATION_PARAMS['lambda'])),
        'fourier_order': int(data.get('fourier_order', DEFAULT_SIMULATION_PARAMS['fourier_order'])),
        'scenario': data.get('scenario', 'cologne8'),
        'num_seconds': int(data.get('num_seconds', DEFAULT_SIMULATION_PARAMS['num_seconds'])),
        'use_gui': False  # Never use GUI for web-based runs
    }
    
    # Validate parameters
    if params['episodes'] < 1 or params['episodes'] > 200:
        return jsonify({'error': 'Episodes must be between 1 and 200'}), 400
    
    if params['fourier_order'] < 1 or params['fourier_order'] > 5:
        return jsonify({'error': 'Fourier order must be between 1 and 5'}), 400
    
    try:
        # Run simulation synchronously (blocks until complete)
        results = simulation_manager.run_simulation(**params)
        return jsonify(results)
    
    except Exception as e:
        print(f"Simulation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@simulation_bp.route('/api/simulation-status', methods=['GET'])
def simulation_status():
    """Get current simulation status"""
    return jsonify({
        'running': simulation_manager.is_running,
        'progress': simulation_manager.progress
    })


@simulation_bp.route('/api/trained-agents', methods=['GET'])
def get_trained_agents():
    """Get list of trained agents"""
    import os
    from config.settings import TRAINED_AGENTS_DIR
    
    agents = {}
    if os.path.exists(TRAINED_AGENTS_DIR):
        for scenario_dir in os.listdir(TRAINED_AGENTS_DIR):
            scenario_path = os.path.join(TRAINED_AGENTS_DIR, scenario_dir)
            if os.path.isdir(scenario_path):
                agent_files = [f for f in os.listdir(scenario_path) if f.endswith('.pkl')]
                agents[scenario_dir] = agent_files
    
    return jsonify({'agents': agents})
