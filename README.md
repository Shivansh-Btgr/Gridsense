# gridsense

An AI-powered web application for traffic video analysis and traffic signal optimization using machine learning and reinforcement learning.

## 🎯 Features

### Video Analysis
- ✨ **Beautiful Modern UI** - Gradient-based design with smooth animations
- 🎥 **Video Labeling** - Upload videos and get objects automatically labeled
- 🤖 **AI-Powered Detection** - Uses YOLOv8 neural network for accurate vehicle detection
- ⚡ **Fast Processing** - Optimized for speed and accuracy
- � **Real-time Progress** - Track video processing with live updates

### Traffic Signal Optimization
- 🚦 **RL-Based Optimization** - Reinforcement learning to optimize traffic light timing
- 🗺️ **Multiple Scenarios** - Choose from 5+ built-in intersections (Cologne, Arterial, Ingolstadt)
- 🎮 **Custom Grid Generator** - Create custom NxM grid networks
- 🧠 **SUMO Integration** - Realistic traffic simulation with SUMO-RL
- 📈 **Training Metrics** - Visualize learning progress with charts
- 💾 **Agent Persistence** - Save and reuse trained agents
- ⏱️ **Performance Tracking** - Monitor wait times and average speeds

## 🏗️ Project Structure

```
Final/
├── backend/              # Modular Python backend
│   ├── agents/          # RL agents (SARSA lambda)
│   ├── simulation/      # Traffic simulation logic
│   ├── video_processing/# YOLO detection
│   └── api/            # API route blueprints
├── config/             # Configuration files
├── data/models/        # ML models (YOLO)
├── static/             # Frontend assets (CSS, JS)
├── templates/          # HTML templates
├── outputs/            # Simulation results
├── trained_agents/     # Saved RL agents
└── app_new.py         # Main application entry point
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed documentation.

## 🛠️ Tech Stack

- **Backend**: Flask (Python 3.12.9)
- **ML Model**: YOLOv8 (Ultralytics)
- **RL Framework**: SUMO-RL with True Online SARSA(λ)
- **Traffic Simulation**: SUMO (Simulation of Urban MObility)
- **Function Approximation**: Fourier basis with linear approximation
- **Computer Vision**: OpenCV
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charts**: Chart.js for visualization
- **Architecture**: Modular blueprint-based design

## 📦 Installation

### Prerequisites
- Python 3.12+ 
- pip (Python package manager)
- SUMO (optional, for traffic signal optimization)

### Quick Start

1. **Navigate to project directory**
```cmd
cd C:\Users\Shivansh\Desktop\Shivansh\Codes\Hackathon\Final
```

2. **Install dependencies**
```cmd
pip install -r requirements.txt
```

3. **Run the application**
```cmd
python app_new.py
```

4. **Open in browser**
```
http://localhost:5000
```

### Dependencies Installed
- Flask 3.0.3 & Flask-CORS 5.0.0
- Ultralytics 8.3.0 (YOLOv8)
- OpenCV 4.10.0.84
- PyTorch 2.5.1 & TorchVision 0.20.1
- SUMO-RL 1.4.7 & Gymnasium 0.29.1
- Pandas 2.2.3, NumPy 1.26.4, Matplotlib 3.9.2

### SUMO Installation (For Traffic Optimization)

**Windows:**
- Download: https://www.eclipse.org/sumo/
- Install and add to PATH
- Set: `SUMO_HOME=C:\Program Files (x86)\Eclipse\Sumo`

**Linux:**
```bash
sudo apt-get install sumo sumo-tools sumo-doc
export SUMO_HOME=/usr/share/sumo
```

**macOS:**
```bash
brew install sumo
export SUMO_HOME=/usr/local/share/sumo
```

4. **Run the application**
```cmd
python app.py
```

5. **Open your browser and visit**
```
http://localhost:5000
```

## Usage

### Label Your Video

1. Navigate to the **Dashboard** from the landing page
2. Click on **"Label Your Video"** feature card
3. Upload a traffic video (MP4, AVI, MOV, or MKV - max 500MB)
4. Click **"Process Video with AI"**
5. Wait for the AI to analyze and label the video
6. Download your labeled video with detected objects

### Optimize Traffic Signals

1. Navigate to the **Dashboard**
2. Click on **"Optimize Traffic Signals"** feature card
3. Configure RL parameters (episodes, learning rate, etc.)
4. Click **"Start Optimization"**
5. View real-time learning progress
6. Analyze results with interactive charts

**Requirements**: SUMO must be installed and SUMO_HOME environment variable set

### Detected Objects

The ML model can detect:
- 🚗 Cars
- 🚚 Trucks
- 🚌 Buses
- 🏍️ Motorcycles
- 🚲 Bicycles
- 🚶 Pedestrians
- 🚦 Traffic Lights
- 🛑 Stop Signs
- And 70+ other object classes from COCO dataset

## Project Structure

```
Final/
├── app.py                      # Flask backend server
├── traffic_simulation.py       # SUMO-RL integration
├── network_manager.py          # Network scenario management
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── NETWORK_SCENARIOS.md        # Network scenarios guide
├── SUMO_GUI_GUIDE.md          # SUMO GUI integration guide
├── .gitignore                 # Git ignore file
├── linear_rl/                 # RL algorithms
│   ├── __init__.py
│   └── true_online_sarsa.py   # SARSA(λ) implementation
├── networks/                  # SUMO network files
│   └── custom/                # User-created custom networks
├── templates/
│   ├── index.html             # Landing page
│   ├── dashboard.html         # Dashboard page
│   ├── label_video.html       # Video labeling page
│   └── optimize_signals.html  # Traffic optimization page
├── static/
│   ├── css/
│   │   ├── style.css          # Main stylesheet
│   │   ├── dashboard.css      # Dashboard styles
│   │   ├── label-video.css    # Label video page styles
│   │   └── optimize-signals.css # Optimization page styles
│   └── js/
│       ├── main.js            # Landing page scripts
│       ├── dashboard.js       # Dashboard scripts
│       ├── label-video.js     # Video labeling scripts
│       └── optimize-signals.js # Optimization scripts
├── uploads/                   # Temporary upload folder (auto-created)
├── outputs/                   # Processed videos & simulation results (auto-created)
└── yolov8n.pt                # YOLO model (auto-downloaded)
```

## API Endpoints

### `GET /`
Landing page

### `GET /dashboard`
Dashboard page

### `GET /label-video`
Video labeling interface

### `POST /api/process-video`
Process and label a video
- **Body**: FormData with 'video' file
- **Returns**: JSON with success status and output filename

### `GET /api/download/<filename>`
Download processed video

## Features Coming Soon

- 📊 Traffic Analytics - Analyze patterns and peak hours
- 🔍 Vehicle Tracking - Track individual vehicles across cameras
- 📈 Historical Data - Track and compare traffic over time

## Model Information

The application uses **YOLOv8 Nano (yolov8n.pt)** for optimal speed-accuracy balance:
- First run will download the model (~6MB)
- Model is cached for subsequent runs
- 99% detection accuracy on COCO dataset
- Real-time processing capability

## Troubleshooting

### Issue: SUMO not found
- Install SUMO from https://www.eclipse.org/sumo/
- Set SUMO_HOME environment variable
- Restart terminal/IDE after setting environment variables
- The video labeling feature will still work without SUMO

### Issue: Model not downloading
- Ensure you have internet connection for first run
- Model will be downloaded automatically to `~/.cache/ultralytics/`

### Issue: Out of memory
- Try processing shorter videos
- Close other applications
- Consider using a smaller model or reducing video resolution

### Issue: Slow processing
- Use YOLOv8 Nano (default) for fastest results
- Processing time depends on video length and resolution
- GPU acceleration available if CUDA-compatible GPU detected

## Performance Tips

- **Video Length**: Shorter videos process faster
- **Resolution**: Lower resolution = faster processing
- **Format**: MP4 with H.264 codec works best
- **GPU**: CUDA-compatible GPU will significantly speed up processing

## License

This project is created for educational and demonstration purposes.

## Credits

- **YOLOv8**: Ultralytics
- **Icons**: Font Awesome
- **Fonts**: Segoe UI


