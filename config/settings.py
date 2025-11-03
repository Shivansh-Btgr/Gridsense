"""
Configuration settings for Smart Traffic Management System
"""

import os

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(DATA_DIR, 'models')
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
NETWORKS_DIR = os.path.join(BASE_DIR, 'networks')
TRAINED_AGENTS_DIR = os.path.join(BASE_DIR, 'trained_agents')

# Ensure directories exist
for directory in [DATA_DIR, MODELS_DIR, OUTPUTS_DIR, UPLOADS_DIR, NETWORKS_DIR, TRAINED_AGENTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# YOLO Model Configuration
YOLO_MODEL_PATH = os.path.join(MODELS_DIR, 'yolov8n.pt')

# Fallback to old location if new one doesn't exist
if not os.path.exists(YOLO_MODEL_PATH):
    old_path = os.path.join(BASE_DIR, 'yolov8n.pt')
    if os.path.exists(old_path):
        YOLO_MODEL_PATH = old_path

# SUMO Configuration
SUMO_HOME = os.environ.get("SUMO_HOME")
if not SUMO_HOME:
    # Try common installation paths
    possible_paths = [
        r"C:\Program Files (x86)\Eclipse\Sumo",
        r"C:\Program Files\Eclipse\Sumo",
        "/usr/share/sumo",
        "/usr/local/share/sumo"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            SUMO_HOME = path
            os.environ["SUMO_HOME"] = path
            break

# Traffic Simulation Settings
DEFAULT_SIMULATION_PARAMS = {
    'episodes': 10,
    'alpha': 0.00001,
    'gamma': 0.95,
    'epsilon': 0.05,
    'lambda': 0.1,
    'fourier_order': 3,
    'num_seconds': 1000,
    'begin_time': 25200,  # 7:00 AM for cologne networks
}

# Video Processing Settings
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB

# Flask Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))
