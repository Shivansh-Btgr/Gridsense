"""
Smart Traffic Management System - Main Application
Reorganized structure with modular components
"""

from flask import Flask, render_template
from flask_cors import CORS
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import (
    SECRET_KEY, DEBUG, HOST, PORT,
    UPLOADS_DIR, OUTPUTS_DIR, NETWORKS_DIR, TRAINED_AGENTS_DIR
)
from backend.api.video_routes import video_bp
from backend.api.simulation_routes import simulation_bp, SUMO_AVAILABLE
from backend.api.uxsim_routes import uxsim_bp
from backend.api.signal_routes import signal_bp
from backend.simulation.network_mgr import network_manager


def create_app():
    """Application factory"""
    app = Flask(__name__)
    CORS(app)
    
    # Configuration
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
    
    # Ensure directories exist
    for directory in [UPLOADS_DIR, OUTPUTS_DIR, NETWORKS_DIR, TRAINED_AGENTS_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(video_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(uxsim_bp)
    app.register_blueprint(signal_bp)
    
    # Main routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
    
    @app.route('/label-video')
    def label_video_page():
        return render_template('label_video.html')
    
    @app.route('/optimize-signals')
    def optimize_signals_page():
        scenarios = network_manager.get_available_scenarios() if SUMO_AVAILABLE else {}
        return render_template('optimize_signals.html', 
                             sumo_available=SUMO_AVAILABLE, 
                             scenarios=scenarios)
    
    @app.route('/uxsim-scenarios')
    def uxsim_scenarios_page():
        return render_template('uxsim_scenarios.html')
    
    @app.route('/signal-tuning')
    def signal_tuning_page():
        return render_template('signal_tuning.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'sumo_available': SUMO_AVAILABLE,
            'version': '1.0.0'
        }
    
    return app


if __name__ == '__main__':
    app = create_app()
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║  Smart Traffic Management System                             ║
    ║  Server starting on http://{HOST}:{PORT}                   ║
    ║  SUMO-RL Available: {str(SUMO_AVAILABLE).ljust(41)}║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host=HOST, port=PORT, debug=DEBUG)
