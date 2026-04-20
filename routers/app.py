from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import mediapipe as mp
import numpy as np
import base64
import json
from utils.angle_calculator import calculate_body_angles
from utils.pose_validator import PoseValidator
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
os.environ.get('FLASK_SECRET_KEY', 'fallback-dev-key')

# Enable CORS for React frontend
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# Initialize SocketIO
socketio = SocketIO(app, 
                    cors_allowed_origins="http://localhost:3000",
                    async_mode='eventlet',
                    logger=True,
                    engineio_logger=False)


# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1
)

# Initialize Pose Validator
pose_validator = PoseValidator('pose_data/reference_poses.json')

# Store active sessions
active_sessions = {}

print("🚀 Flask server initializing...")
print("📊 MediaPipe Pose loaded")
print("✅ Ready to accept connections")


@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'AI Yoga Trainer Backend',
        'available_poses': pose_validator.list_all_poses()
    })

@app.route('/static/img/')
def serve_static(filename):
    return send_from_directory('static', filename)


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'✅ Client connected: {request.sid}')
    active_sessions[request.sid] = {
        'is_analyzing': False,
        'current_pose': None,
        'frame_count': 0
    }
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect(sid):
    """Handle client disconnection"""
    print(f'❌ Client disconnected')
    # Get sid from the socket context instead
    from flask import request as flask_request
    session_id = flask_request.sid if hasattr(flask_request, 'sid') else None
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]

@socketio.on('get_pose_info')
def handle_get_pose_info(data):
    """Send pose information to client"""
    pose_name = data.get('pose_name')
    
    print(f"🔍 Requesting pose info for: {pose_name}")
    
    if not pose_name:
        print("❌ No pose name provided")
        emit('error', {'message': 'No pose name provided'})
        return
    
    try:
        pose_info = pose_validator.get_pose_info(pose_name)
        
        if pose_info:
            print(f"📋 Sending pose info: {pose_name}")
            emit('pose_info', pose_info)
        else:
            error_msg = f'Pose "{pose_name}" not found in database'
            print(f"❌ {error_msg}")
            print(f"Available poses: {pose_validator.list_all_poses()}")
            emit('error', {'message': error_msg})
    except Exception as e:
        error_msg = f'Error getting pose info: {str(e)}'
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': error_msg})


@socketio.on('start_analysis')
def handle_start_analysis(data):
    """Start pose analysis for the session"""
    pose_name = data.get('pose_name')
    
    if request.sid in active_sessions:
        active_sessions[request.sid]['is_analyzing'] = True
        active_sessions[request.sid]['current_pose'] = pose_name
        active_sessions[request.sid]['frame_count'] = 0
        print(f"🎯 Started analysis for: {pose_name}")
        emit('analysis_started', {'pose_name': pose_name})


@socketio.on('stop_analysis')
def handle_stop_analysis():
    """Stop pose analysis for the session"""
    if request.sid in active_sessions:
        active_sessions[request.sid]['is_analyzing'] = False
        active_sessions[request.sid]['current_pose'] = None
        print(f"⏸️  Stopped analysis")
        emit('analysis_stopped', {})


# @socketio.on('video_frame')
# def handle_video_frame(data):
#     """Process incoming video frame from client"""
    
#     # Check if session is analyzing
#     if request.sid not in active_sessions:
#         return
    
#     session = active_sessions[request.sid]
    
#     if not session['is_analyzing']:
#         return
    
#     try:
#         # Decode base64 image
#         image_data = data.get('image', '')
#         pose_name = data.get('pose_name')
        
#         if not image_data or not pose_name:
#             return
        
#         # Remove base64 header if present
#         if ',' in image_data:
#             image_data = image_data.split(',')[1]
        
#         # Decode image
#         img_bytes = base64.b64decode(image_data)
#         nparr = np.frombuffer(img_bytes, np.uint8)
#         frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
#         if frame is None:
#             emit('error', {'message': 'Failed to decode image'})
#             return
        
#         # Convert BGR to RGB
#         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
#         # Process with MediaPipe
#         results = pose.process(frame_rgb)
        
#         # Update frame count
#         session['frame_count'] += 1
        
#         if results.pose_landmarks:
#             # Extract landmarks as serializable format
#             landmarks_list = []
#             for landmark in results.pose_landmarks.landmark:
#                 landmarks_list.append({
#                     'x': landmark.x,
#                     'y': landmark.y,
#                     'z': landmark.z,
#                     'visibility': landmark.visibility
#                 })
            
#             # Send landmarks to client for visualization
#             emit('landmarks', {'landmarks': landmarks_list})
            
#             # Calculate angles
#             angles = calculate_body_angles(results.pose_landmarks)
            
#             if angles:
#                 # Validate pose
#                 validation_result = pose_validator.validate_pose(pose_name, angles)
                
#                 # Send feedback to client
#                 emit('pose_feedback', {
#                     'is_valid': validation_result['is_valid'],
#                     'accuracy': validation_result['accuracy'],
#                     'feedback': validation_result['feedback'],
#                     'angle_diffs': validation_result['angle_diffs']
#                 })
                
#                 # Log every 30 frames (approximately every 3 seconds)
#                 if session['frame_count'] % 30 == 0:
#                     print(f"📊 {pose_name} | Accuracy: {validation_result['accuracy']}% | "
#                           f"Frames: {session['frame_count']}")
#             else:
#                 emit('pose_feedback', {
#                     'is_valid': False,
#                     'accuracy': 0,
#                     'feedback': ['Unable to calculate angles'],
#                     'angle_diffs': {}
#                 })
#         else:
#             # No pose detected
#             emit('landmarks', {'landmarks': []})
#             emit('pose_feedback', {
#                 'is_valid': False,
#                 'accuracy': 0,
#                 'feedback': ['No pose detected. Please ensure full body is visible.'],
#                 'angle_diffs': {}
#             })
    
#     except Exception as e:
#         print(f"❌ Error processing frame: {str(e)}")
#         emit('error', {'message': f'Error processing frame: {str(e)}'})

@socketio.on('video_frame')
def handle_video_frame(data):
    """Process incoming video frame from client"""
    
    # Check if session is analyzing
    if request.sid not in active_sessions:
        return
    
    session = active_sessions[request.sid]
    
    if not session['is_analyzing']:
        return
    
    try:
        # Decode base64 image
        image_data = data.get('image', '')
        pose_name = data.get('pose_name')
        
        if not image_data or not pose_name:
            return
        
        # Remove base64 header if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode image
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            emit('error', {'message': 'Failed to decode image'})
            return
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = pose.process(frame_rgb)
        
        # Update frame count
        session['frame_count'] += 1
        
        if results.pose_landmarks:
            # Extract landmarks as serializable format
            landmarks_list = []
            for landmark in results.pose_landmarks.landmark:
                landmarks_list.append({
                    'x': float(landmark.x),
                    'y': float(landmark.y),
                    'z': float(landmark.z),
                    'visibility': float(landmark.visibility)
                })
            
            # Send landmarks to client for visualization
            emit('landmarks', {'landmarks': landmarks_list})
            
            # Calculate angles
            angles = calculate_body_angles(results.pose_landmarks)
            
            if angles:
                # Validate pose
                validation_result = pose_validator.validate_pose(pose_name, angles)
                
                # Send feedback to client (convert numpy types to Python types)
                emit('pose_feedback', {
                    'is_valid': bool(validation_result['is_valid']),
                    'accuracy': float(validation_result['accuracy']),
                    'feedback': validation_result['feedback'],
                    'angle_diffs': {
                        k: {
                            'current': float(v['current']),
                            'reference': float(v['reference']),
                            'difference': float(v['difference'])
                        } for k, v in validation_result['angle_diffs'].items()
                    }
                })
                
                # Log every 30 frames (approximately every 3 seconds)
                if session['frame_count'] % 30 == 0:
                    print(f"📊 {pose_name} | Accuracy: {validation_result['accuracy']}% | "
                          f"Frames: {session['frame_count']}")
            else:
                emit('pose_feedback', {
                    'is_valid': False,
                    'accuracy': 0.0,
                    'feedback': ['Unable to calculate angles'],
                    'angle_diffs': {}
                })
        else:
            # No pose detected
            emit('landmarks', {'landmarks': []})
            emit('pose_feedback', {
                'is_valid': False,
                'accuracy': 0.0,
                'feedback': ['No pose detected. Please ensure full body is visible.'],
                'angle_diffs': {}
            })
    
    except Exception as e:
        print(f"❌ Error processing frame: {str(e)}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Error processing frame: {str(e)}'})


@socketio.on('list_poses')
def handle_list_poses():
    """Send list of all available poses"""
    poses = pose_validator.list_all_poses()
    emit('poses_list', {'poses': poses})


@socketio.on('ping')
def handle_ping():
    """Handle ping for connection keep-alive"""
    emit('pong')


# Error handler
@socketio.on_error_default
def default_error_handler(e):
    """Handle SocketIO errors"""
    print(f"❌ SocketIO Error: {str(e)}")
    emit('error', {'message': str(e)})


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🧘‍♀️  AI YOGA TRAINER - BACKEND SERVER")
    print("="*50)
    print(f"📡 Server running on: http://localhost:5000")
    print(f"🔌 SocketIO endpoint: ws://localhost:5000")
    print(f"🎯 Available poses: {len(pose_validator.list_all_poses())}")
    print(f"✨ Waiting for React frontend on http://localhost:3000")
    print("="*50 + "\n")
    
    # Run with eventlet
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
