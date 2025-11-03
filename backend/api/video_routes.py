"""
Video processing API routes
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import cv2
from ultralytics import YOLO

from config.settings import UPLOADS_DIR, OUTPUTS_DIR, YOLO_MODEL_PATH, ALLOWED_VIDEO_EXTENSIONS

video_bp = Blueprint('video', __name__)

# Load YOLO model
model = None

def load_model():
    global model
    if model is None:
        print("Loading YOLO model...")
        model = YOLO(YOLO_MODEL_PATH)
        print("Model loaded successfully!")

def allowed_file(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


@video_bp.route('/api/process-video', methods=['POST'])
def process_video():
    """Process video with YOLO object detection"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file format. Allowed: {", ".join(ALLOWED_VIDEO_EXTENSIONS)}'}), 400
        
        # Load model if not already loaded
        load_model()
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOADS_DIR, filename)
        file.save(input_path)
        
        # Process video
        output_filename = f"labeled_{filename}"
        output_path = os.path.join(OUTPUTS_DIR, output_filename)
        
        # Open video
        cap = cv2.VideoCapture(input_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Vehicle tracking
        vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        vehicle_counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run YOLO detection
            results = model(frame, verbose=False)
            
            # Annotate frame
            annotated_frame = results[0].plot()
            
            # Count vehicles
            for box in results[0].boxes:
                cls = int(box.cls[0])
                if cls in vehicle_classes:
                    class_name = results[0].names[cls]
                    vehicle_counts[class_name] = vehicle_counts.get(class_name, 0) + 1
            
            out.write(annotated_frame)
            frame_count += 1
            
            if frame_count % 30 == 0:
                print(f"Processed {frame_count}/{total_frames} frames")
        
        cap.release()
        out.release()
        
        # Clean up input file
        os.remove(input_path)
        
        return jsonify({
            'success': True,
            'output_file': output_filename,
            'vehicle_counts': vehicle_counts,
            'total_frames': frame_count
        })
    
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/api/download-video/<filename>')
def download_video(filename):
    """Download processed video"""
    try:
        filepath = os.path.join(OUTPUTS_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
