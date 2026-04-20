# Yoga API Contract

## Overview

The Yoga API provides real-time pose detection, validation, and feedback using MediaPipe and computer vision. It supports both REST endpoints for single-image analysis and WebSocket connections for real-time video frame processing.

**Base URL**: `http://localhost:8000/api/yoga`
**WebSocket URL**: `ws://localhost:8000/api/yoga/ws`

---

## REST API Endpoints

### 1. Get Available Poses

**Endpoint**: `GET /poses`

**Description**: Retrieve a list of all available yoga poses with metadata.

**Response**: `PoseListResponse`

```json
{
  "poses": [
    {
      "name": "tree_pose",
      "display_name": "Tree Pose (Vrksasana)",
      "description": "Stand on one leg with the other foot placed on the inner thigh",
      "difficulty": "beginner",
      "benefits": [
        "Improves balance",
        "Strengthens legs",
        "Enhances focus"
      ]
    }
  ],
  "total": 3
}
```

**Response Model**:
```python
class PoseListResponse(BaseModel):
    poses: List[PoseInfo]
    total: int

class PoseInfo(BaseModel):
    name: str
    display_name: str
    description: str
    difficulty: str
    benefits: List[str]
```

---

### 2. Get Pose Details

**Endpoint**: `GET /poses/{pose_name}`

**Description**: Get detailed information about a specific yoga pose.

**Path Parameters**:
- `pose_name` (string, required): Name of the pose (e.g., "tree_pose", "warrior_pose")

**Response**:

```json
{
  "name": "tree_pose",
  "display_name": "Tree Pose (Vrksasana)",
  "description": "Stand on one leg with the other foot placed on the inner thigh",
  "difficulty": "beginner",
  "benefits": [
    "Improves balance",
    "Strengthens legs",
    "Enhances focus"
  ],
  "instructions": [
    "Stand tall with feet together",
    "Shift weight to left foot",
    "Place right foot on inner left thigh"
  ],
  "key_angles": {
    "left_knee": 180,
    "right_knee": 90,
    "left_shoulder": 170,
    "right_shoulder": 170
  },
  "contraindications": [
    "Recent leg injury",
    "Balance disorders"
  ]
}
```

**Error Responses**:
- `404`: Pose not found

---

### 3. Analyze Pose (Image Upload)

**Endpoint**: `POST /analyze`

**Description**: Analyze an uploaded image for yoga pose detection and validation.

**Request**: `multipart/form-data`

**Form Parameters**:
- `pose_name` (string, required): Name of the pose to analyze
- `image` (file, required): Image file (JPEG/PNG) containing the person performing the pose

**Response**: `PoseAnalysisResponse`

```json
{
  "pose_name": "tree_pose",
  "detected_angles": {
    "left_elbow": 165.2,
    "right_elbow": 168.5,
    "left_knee": 178.3,
    "right_knee": 88.7,
    "left_shoulder": 169.4,
    "right_shoulder": 171.2,
    "left_hip": 175.6,
    "right_hip": 92.3
  },
  "validation": {
    "valid": false,
    "accuracy": 85.5,
    "feedback": [
      {
        "joint": "Right Knee",
        "expected": 90.0,
        "detected": 88.7,
        "correction": "Slightly increase angle to match the target"
      }
    ],
    "angle_diffs": {
      "right_knee": {
        "reference": 90.0,
        "current": 88.7,
        "difference": 1.3
      }
    }
  },
  "landmarks": [
    {
      "x": 0.5234,
      "y": 0.3245,
      "z": -0.1234,
      "visibility": 0.9876
    }
  ]
}
```

**Response Model**:
```python
class PoseAnalysisResponse(BaseModel):
    pose_name: str
    detected_angles: Dict[str, float]
    validation: ValidationResult
    landmarks: Optional[List[Dict[str, float]]]

class ValidationResult(BaseModel):
    valid: bool
    accuracy: float
    feedback: List[FeedbackItem]
    angle_diffs: Dict[str, Dict[str, float]]

class FeedbackItem(BaseModel):
    joint: str
    expected: float
    detected: float
    correction: str
```

**Error Responses**:
- `400`: Invalid image format
- `404`: Pose not found
- `500`: Analysis failed

---

### 4. Analyze Pose (Base64)

**Endpoint**: `POST /analyze-base64`

**Description**: Analyze a base64-encoded image for yoga pose detection.

**Request**: `application/json`

```json
{
  "pose_name": "tree_pose",
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Request Model**:
```python
class PoseAnalysisRequest(BaseModel):
    pose_name: str
    image_base64: str
```

**Response**: Same as `/analyze` endpoint (`PoseAnalysisResponse`)

**Error Responses**:
- `400`: Invalid image data
- `404`: Pose not found
- `500`: Analysis failed

---

### 5. Health Check

**Endpoint**: `GET /health`

**Description**: Check the health status of the yoga analysis system.

**Response**:

```json
{
  "status": "healthy",
  "mediapipe_loaded": true,
  "reference_poses_loaded": true,
  "total_poses": 3,
  "pose_data_path": "/path/to/reference_poses.json",
  "pose_data_exists": true,
  "validator_loaded": true,
  "websocket_enabled": true,
  "active_sessions": 2
}
```

**Error Response**:

```json
{
  "status": "unhealthy",
  "error": "No reference poses loaded"
}
```

---

## WebSocket API

### Connection

**Endpoint**: `WS /ws`

**Description**: Establish a WebSocket connection for real-time pose analysis.

**Connection Flow**:

1. Client connects to `ws://localhost:8000/api/yoga/ws`
2. Server sends connection confirmation:
```json
{
  "type": "connected",
  "client_id": "12345678"
}
```

---

### WebSocket Protocol

#### Message Types (Client → Server)

##### 1. Start Analysis

```json
{
  "action": "start",
  "pose_name": "tree_pose"
}
```

**Server Response**:
```json
{
  "type": "analysis_started",
  "pose_name": "tree_pose"
}
```

---

##### 2. Send Video Frame

```json
{
  "action": "frame",
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "pose_name": "tree_pose"
}
```

**Server Responses**:

*Landmarks Update*:
```json
{
  "type": "landmarks",
  "landmarks": [
    {
      "x": 0.5234,
      "y": 0.3245,
      "z": -0.1234,
      "visibility": 0.9876
    }
  ]
}
```

*Feedback Update*:
```json
{
  "type": "feedback",
  "data": {
    "valid": false,
    "accuracy": 85.5,
    "feedback": [
      {
        "joint": "Right Knee",
        "expected": 90.0,
        "detected": 88.7,
        "correction": "Slightly increase angle to match the target"
      }
    ],
    "angle_diffs": {
      "right_knee": {
        "reference": 90.0,
        "current": 88.7,
        "difference": 1.3
      }
    }
  }
}
```

---

##### 3. Stop Analysis

```json
{
  "action": "stop"
}
```

**Server Response**:
```json
{
  "type": "analysis_stopped"
}
```

---

##### 4. Get Pose Info

```json
{
  "action": "get_pose_info",
  "pose_name": "tree_pose"
}
```

**Server Response**:
```json
{
  "type": "pose_info",
  "data": {
    "name": "Tree Pose (Vrksasana)",
    "description": "...",
    "benefits": [...],
    "reference_angles": {...}
  }
}
```

---

##### 5. List All Poses

```json
{
  "action": "list_poses"
}
```

**Server Response**:
```json
{
  "type": "poses_list",
  "poses": ["tree_pose", "warrior_pose", "mountain_pose"]
}
```

---

##### 6. Ping (Keep-Alive)

```json
{
  "action": "ping"
}
```

**Server Response**:
```json
{
  "type": "pong"
}
```

---

#### Message Types (Server → Client)

| Type | Description | Data Structure |
|------|-------------|----------------|
| `connected` | Connection confirmation | `{ "client_id": "..." }` |
| `analysis_started` | Analysis session started | `{ "pose_name": "..." }` |
| `analysis_stopped` | Analysis session stopped | `{}` |
| `landmarks` | Pose landmarks detected | `{ "landmarks": [...] }` |
| `feedback` | Pose validation feedback | `{ "data": {...} }` |
| `pose_info` | Pose information | `{ "data": {...} }` |
| `poses_list` | Available poses list | `{ "poses": [...] }` |
| `pong` | Ping response | `{}` |
| `error` | Error occurred | `{ "message": "..." }` |

---

## Data Models

### FeedbackItem

```python
class FeedbackItem(BaseModel):
    joint: str          # Joint name (e.g., "Left Knee", "Right Shoulder")
    expected: float     # Expected angle in degrees
    detected: float     # Detected angle in degrees
    correction: str     # Human-readable correction advice
```

**Example**:
```json
{
  "joint": "Left Knee",
  "expected": 180.0,
  "detected": 165.2,
  "correction": "Straighten your left knee more to reach the target angle"
}
```

---

### ValidationResult

```python
class ValidationResult(BaseModel):
    valid: bool                                      # Whether pose is correct
    accuracy: float                                   # Overall accuracy (0-100)
    feedback: List[FeedbackItem]                     # List of corrections
    angle_diffs: Dict[str, Dict[str, float]]         # Detailed angle differences
```

**Example**:
```json
{
  "valid": false,
  "accuracy": 85.5,
  "feedback": [
    {
      "joint": "Right Knee",
      "expected": 90.0,
      "detected": 88.7,
      "correction": "Slightly increase angle"
    }
  ],
  "angle_diffs": {
    "right_knee": {
      "reference": 90.0,
      "current": 88.7,
      "difference": 1.3
    }
  }
}
```

---

### PoseInfo

```python
class PoseInfo(BaseModel):
    name: str                   # Internal pose identifier
    display_name: str           # Human-readable name
    description: str            # Pose description
    difficulty: str             # "beginner", "intermediate", "advanced"
    benefits: List[str]         # Health benefits
```

---

### Detected Angles

All angles are in degrees (0-180).

**Available Joints**:
- `left_elbow`: Left elbow angle
- `right_elbow`: Right elbow angle
- `left_knee`: Left knee angle
- `right_knee`: Right knee angle
- `left_shoulder`: Left shoulder angle
- `right_shoulder`: Right shoulder angle
- `left_hip`: Left hip angle
- `right_hip`: Right hip angle

**Example**:
```json
{
  "left_elbow": 165.2,
  "right_elbow": 168.5,
  "left_knee": 178.3,
  "right_knee": 88.7,
  "left_shoulder": 169.4,
  "right_shoulder": 171.2,
  "left_hip": 175.6,
  "right_hip": 92.3
}
```

---

### Landmarks

MediaPipe Pose landmarks (33 keypoints) with normalized coordinates.

**Structure**:
```json
{
  "x": 0.5234,        // X coordinate (0-1, normalized by frame width)
  "y": 0.3245,        // Y coordinate (0-1, normalized by frame height)
  "z": -0.1234,       // Depth coordinate
  "visibility": 0.9876 // Confidence score (0-1)
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request (invalid image, missing parameters) |
| `404` | Pose Not Found |
| `500` | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Pose 'invalid_pose' not found"
}
```

### WebSocket Error Messages

```json
{
  "type": "error",
  "message": "pose_name is required"
}
```

---

## Usage Examples

### REST API - Single Image Analysis

#### JavaScript (Fetch)

```javascript
// Analyze pose from uploaded file
const formData = new FormData();
formData.append('image', imageFile);
formData.append('pose_name', 'tree_pose');

const response = await fetch('http://localhost:8000/api/yoga/analyze', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Accuracy:', result.validation.accuracy);
```

#### Python (requests)

```python
import requests

with open('yoga_pose.jpg', 'rb') as f:
    files = {'image': f}
    data = {'pose_name': 'tree_pose'}
    response = requests.post(
        'http://localhost:8000/api/yoga/analyze',
        files=files,
        data=data
    )
    
result = response.json()
print(f"Accuracy: {result['validation']['accuracy']}%")
```

---

### WebSocket - Real-Time Analysis

#### JavaScript

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/yoga/ws');

ws.onopen = () => {
  console.log('✅ Connected');
  
  // Start analysis
  ws.send(JSON.stringify({
    action: 'start',
    pose_name: 'tree_pose'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'connected':
      console.log('Client ID:', data.client_id);
      break;
      
    case 'landmarks':
      console.log('Landmarks:', data.landmarks.length);
      break;
      
    case 'feedback':
      console.log('Accuracy:', data.data.accuracy);
      console.log('Feedback:', data.data.feedback);
      break;
  }
};

// Send video frames (from webcam)
function sendFrame(base64Image) {
  ws.send(JSON.stringify({
    action: 'frame',
    image: base64Image,
    pose_name: 'tree_pose'
  }));
}

// Stop analysis
function stopAnalysis() {
  ws.send(JSON.stringify({
    action: 'stop'
  }));
}
```

#### Python (websockets)

```python
import asyncio
import websockets
import json

async def analyze_realtime():
    uri = "ws://localhost:8000/api/yoga/ws"
    
    async with websockets.connect(uri) as websocket:
        # Start analysis
        await websocket.send(json.dumps({
            "action": "start",
            "pose_name": "tree_pose"
        }))
        
        # Send frames
        for frame in video_frames:
            await websocket.send(json.dumps({
                "action": "frame",
                "image": base64_encode(frame),
                "pose_name": "tree_pose"
            }))
            
            # Receive feedback
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "feedback":
                print(f"Accuracy: {data['data']['accuracy']}%")
        
        # Stop analysis
        await websocket.send(json.dumps({
            "action": "stop"
        }))

asyncio.run(analyze_realtime())
```

---

## Rate Limits & Performance

### REST API
- **Recommended**: Max 10 requests/second per client
- **Image Size**: Max 10MB
- **Timeout**: 30 seconds

### WebSocket
- **Frame Rate**: Recommended 10 FPS (100ms interval)
- **Max Concurrent Connections**: 100
- **Automatic Reconnection**: Client should implement exponential backoff
- **Keep-Alive**: Send `ping` every 30 seconds

---

## Best Practices

### 1. Image Quality
- **Resolution**: Minimum 640x480, recommended 1280x720
- **Format**: JPEG or PNG
- **Content**: Full body must be visible
- **Lighting**: Adequate lighting for pose detection

### 2. WebSocket Usage
- Always send `stop` action before disconnecting
- Implement reconnection logic with exponential backoff
- Handle connection errors gracefully
- Limit frame rate to avoid overwhelming the server

### 3. Error Handling
```javascript
try {
  const result = await analyzePose(image, 'tree_pose');
  if (result.validation.accuracy < 70) {
    // Show feedback to user
    result.validation.feedback.forEach(item => {
      console.log(`${item.joint}: ${item.correction}`);
    });
  }
} catch (error) {
  console.error('Analysis failed:', error);
  // Show user-friendly error message
}
```

---

## Validation Logic

### Accuracy Calculation
- Each joint angle is compared against the reference pose
- Tolerance: ±15 degrees
- Accuracy score: Weighted average of all joint accuracies
- **Valid Pose**: Accuracy ≥ 70%

### Feedback Generation
- Pose-specific feedback templates (via `PoseValidator`)
- Intelligent correction suggestions
- Joint-by-joint breakdown
- Contextual advice based on pose type

---

## Dependencies

### Backend
- FastAPI
- MediaPipe
- OpenCV (cv2)
- NumPy
- Pydantic

### Frontend
- react-webcam
- WebSocket API (native)

---

## Changelog

### Version 1.0.0 (Current)
- ✅ REST API for single image analysis
- ✅ WebSocket API for real-time analysis
- ✅ MediaPipe pose detection
- ✅ Intelligent pose validation with feedback
- ✅ Support for multiple yoga poses
- ✅ Health check endpoint

---

## Support

For issues or questions:
1. Check backend logs for detailed error messages
2. Use `/health` endpoint to verify system status
3. Ensure MediaPipe dependencies are properly installed
4. Verify `reference_poses.json` exists and is properly formatted
