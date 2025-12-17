"""
Yoga Pose Detection and Validation API
Handles pose analysis with MediaPipe and provides real-time feedback via WebSocket
"""

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Form,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import logging
import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path
import json
import base64
from pydantic import BaseModel
import asyncio

# ✅ Import utility functions
from utils.angle_calculator import calculate_body_angles as calc_angles_util
from utils.pose_validator import PoseValidator

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Pose detection instance
pose_detector = mp_pose.Pose(
    min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1
)

# Load reference poses
POSE_DATA_PATH = Path(__file__).parent.parent / "pose_data" / "reference_poses.json"

# ✅ Initialize PoseValidator utility
pose_validator = PoseValidator(poses_json_path=str(POSE_DATA_PATH))

# Store active WebSocket sessions
active_sessions: Dict[str, Dict[str, Any]] = {}


def load_reference_poses() -> Dict[str, Any]:
    """Load reference yoga poses from JSON file"""
    try:
        if POSE_DATA_PATH.exists():
            with open(POSE_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(
                    f"✅ Loaded {len(data)} reference poses from {POSE_DATA_PATH}"
                )
                return data
        else:
            logger.warning(f"⚠️ Reference poses file not found: {POSE_DATA_PATH}")
            return {}
    except Exception as e:
        logger.error(f"❌ Failed to load reference poses: {str(e)}")
        return {}


reference_poses = load_reference_poses()


# ============= Pydantic Models =============


class PoseAnalysisRequest(BaseModel):
    """Request model for pose analysis"""

    pose_name: str
    image_base64: str


class FeedbackItem(BaseModel):
    """Individual feedback item"""

    joint: str
    expected: float
    detected: float
    correction: str


class ValidationResult(BaseModel):
    """Validation result structure"""

    valid: bool
    accuracy: float
    feedback: List[FeedbackItem]
    angle_diffs: Dict[str, Dict[str, float]]


class PoseAnalysisResponse(BaseModel):
    """Response model for pose analysis"""

    pose_name: str
    detected_angles: Dict[str, float]
    validation: ValidationResult
    landmarks: Optional[List[Dict[str, float]]] = None


class PoseInfo(BaseModel):
    """Individual pose information"""

    name: str
    display_name: str
    description: str
    difficulty: str
    benefits: List[str]
    duration: Optional[int] = None
    image: Optional[str] = None


class PoseListResponse(BaseModel):
    """Response model for available poses"""

    poses: List[PoseInfo]
    total: int


# ============= Helper Functions =============


def parse_benefits(benefits: Any) -> List[str]:
    """
    Parse benefits field from pose data
    Handles both string and list formats
    
    Args:
        benefits: Benefits data (can be string or list)
        
    Returns:
        List of benefit strings
    """
    if isinstance(benefits, list):
        return benefits
    elif isinstance(benefits, str):
        # Split by common separators
        if "," in benefits:
            return [b.strip() for b in benefits.split(",")]
        elif ";" in benefits:
            return [b.strip() for b in benefits.split(";")]
        elif "\n" in benefits:
            return [b.strip() for b in benefits.split("\n") if b.strip()]
        else:
            return [benefits]
    else:
        return []


def format_validation_feedback(validation_result: Dict[str, Any]) -> ValidationResult:
    """
    Convert PoseValidator output to API contract format

    Args:
        validation_result: Output from pose_validator.validate_pose()

    Returns:
        ValidationResult with proper structure
    """
    feedback_items = []

    # Convert string feedback to structured format
    if isinstance(validation_result.get("feedback"), list):
        for feedback_msg in validation_result["feedback"]:
            # Parse feedback message to extract joint and correction
            # Example: "Left Knee: increase angle (currently 145.2°, target 160.0°)"
            if ":" in feedback_msg:
                joint_part, correction_part = feedback_msg.split(":", 1)
                joint = joint_part.strip()
                correction = correction_part.strip()

                # Try to extract angles from correction
                expected = 0.0
                detected = 0.0

                # Extract from angle_diffs if available
                joint_key = joint.lower().replace(" ", "_")
                if joint_key in validation_result.get("angle_diffs", {}):
                    angle_info = validation_result["angle_diffs"][joint_key]
                    expected = angle_info.get("reference", 0.0)
                    detected = angle_info.get("current", 0.0)

                feedback_items.append(
                    FeedbackItem(
                        joint=joint,
                        expected=expected,
                        detected=detected,
                        correction=correction,
                    )
                )
            else:
                # Generic feedback without joint info
                feedback_items.append(
                    FeedbackItem(
                        joint="General",
                        expected=0.0,
                        detected=0.0,
                        correction=feedback_msg,
                    )
                )

    return ValidationResult(
        valid=validation_result.get("is_valid", False),
        accuracy=validation_result.get("accuracy", 0.0),
        feedback=feedback_items,
        angle_diffs=validation_result.get("angle_diffs", {}),
    )


def validate_pose_with_feedback(
    detected_angles: Dict[str, float], pose_name: str
) -> ValidationResult:
    """
    Validate detected pose using PoseValidator utility

    Args:
        detected_angles: Dictionary of detected joint angles
        pose_name: Name of the yoga pose to validate against

    Returns:
        Validation result with pose-specific feedback
    """
    try:
        # Use the PoseValidator utility for intelligent feedback
        validation_result = pose_validator.validate_pose(pose_name, detected_angles)

        # Convert to API contract format
        return format_validation_feedback(validation_result)

    except Exception as e:
        logger.error(f"❌ Validation error: {str(e)}")
        return ValidationResult(
            valid=False,
            accuracy=0.0,
            feedback=[
                FeedbackItem(
                    joint="Error",
                    expected=0.0,
                    detected=0.0,
                    correction=f"Validation failed: {str(e)}",
                )
            ],
            angle_diffs={},
        )


def process_video_frame(image_data: str, pose_name: str) -> Dict[str, Any]:
    """
    Process a single video frame for pose detection

    Args:
        image_data: Base64 encoded image
        pose_name: Name of the pose to analyze

    Returns:
        Dict containing landmarks and validation results
    """
    try:
        # Remove base64 header if present
        if "," in image_data:
            image_data = image_data.split(",")[1]

        # Decode image
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {
                "error": "Failed to decode image",
                "landmarks": [],
                "feedback": ValidationResult(
                    valid=False,
                    accuracy=0.0,
                    feedback=[
                        FeedbackItem(
                            joint="Detection",
                            expected=0.0,
                            detected=0.0,
                            correction="Failed to decode image",
                        )
                    ],
                    angle_diffs={},
                ),
            }

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process with MediaPipe
        results = pose_detector.process(frame_rgb)

        if results.pose_landmarks:
            # Extract landmarks
            landmarks_list = [
                {
                    "x": float(lm.x),
                    "y": float(lm.y),
                    "z": float(lm.z),
                    "visibility": float(lm.visibility),
                }
                for lm in results.pose_landmarks.landmark
            ]

            # Calculate angles
            angles = calc_angles_util(results.pose_landmarks)

            if angles:
                # Validate pose
                validation_result = validate_pose_with_feedback(angles, pose_name)

                return {"landmarks": landmarks_list, "feedback": validation_result}
            else:
                return {
                    "landmarks": landmarks_list,
                    "feedback": ValidationResult(
                        valid=False,
                        accuracy=0.0,
                        feedback=[
                            FeedbackItem(
                                joint="Calculation",
                                expected=0.0,
                                detected=0.0,
                                correction="Unable to calculate angles",
                            )
                        ],
                        angle_diffs={},
                    ),
                }
        else:
            # No pose detected
            return {
                "landmarks": [],
                "feedback": ValidationResult(
                    valid=False,
                    accuracy=0.0,
                    feedback=[
                        FeedbackItem(
                            joint="Detection",
                            expected=0.0,
                            detected=0.0,
                            correction="No pose detected. Please ensure full body is visible.",
                        )
                    ],
                    angle_diffs={},
                ),
            }

    except Exception as e:
        logger.error(f"❌ Frame processing error: {str(e)}")
        return {
            "error": str(e),
            "landmarks": [],
            "feedback": ValidationResult(
                valid=False,
                accuracy=0.0,
                feedback=[
                    FeedbackItem(
                        joint="Error",
                        expected=0.0,
                        detected=0.0,
                        correction=f"Error: {str(e)}",
                    )
                ],
                angle_diffs={},
            ),
        }


# ============= WebSocket Endpoint =============


@router.websocket("/ws")
async def websocket_yoga_analysis(websocket: WebSocket):
    """
    WebSocket endpoint for real-time yoga pose analysis

    Protocol:
    Client sends: {"action": "start", "pose_name": "tree_pose"}
    Client sends: {"action": "frame", "image": "base64...", "pose_name": "tree_pose"}
    Client sends: {"action": "stop"}

    Server responds with:
    - {"type": "connected"}
    - {"type": "analysis_started", "pose_name": "..."}
    - {"type": "landmarks", "landmarks": [...]}
    - {"type": "feedback", "data": {...}}
    - {"type": "analysis_stopped"}
    - {"type": "error", "message": "..."}
    """
    await websocket.accept()
    client_id = id(websocket)

    logger.info(f"✅ WebSocket client connected: {client_id}")

    # Initialize session
    active_sessions[str(client_id)] = {
        "is_analyzing": False,
        "current_pose": None,
        "frame_count": 0,
    }

    try:
        # Send connection confirmation
        await websocket.send_json({"type": "connected", "client_id": str(client_id)})

        while True:
            # Receive message from client
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "start":
                # Start analysis
                pose_name = data.get("pose_name")
                if not pose_name:
                    await websocket.send_json(
                        {"type": "error", "message": "pose_name is required"}
                    )
                    continue

                # Validate pose exists
                if pose_name not in pose_validator.list_all_poses():
                    await websocket.send_json(
                        {"type": "error", "message": f"Pose '{pose_name}' not found"}
                    )
                    continue

                active_sessions[str(client_id)]["is_analyzing"] = True
                active_sessions[str(client_id)]["current_pose"] = pose_name
                active_sessions[str(client_id)]["frame_count"] = 0

                logger.info(f"🎯 Started analysis for: {pose_name}")

                await websocket.send_json(
                    {"type": "analysis_started", "pose_name": pose_name}
                )

            elif action == "stop":
                # Stop analysis
                active_sessions[str(client_id)]["is_analyzing"] = False
                active_sessions[str(client_id)]["current_pose"] = None

                logger.info(f"⏸️ Stopped analysis")

                await websocket.send_json({"type": "analysis_stopped"})

            elif action == "frame":
                # Process video frame
                session = active_sessions[str(client_id)]

                if not session["is_analyzing"]:
                    continue

                image_data = data.get("image")
                pose_name = data.get("pose_name") or session["current_pose"]

                if not image_data or not pose_name:
                    continue

                # Process frame
                result = process_video_frame(image_data, pose_name)

                # Update frame count
                session["frame_count"] += 1

                # Send landmarks
                await websocket.send_json(
                    {"type": "landmarks", "landmarks": result.get("landmarks", [])}
                )

                # Send feedback (convert Pydantic model to dict)
                feedback_data = result.get("feedback")
                if isinstance(feedback_data, ValidationResult):
                    feedback_dict = feedback_data.dict()
                else:
                    feedback_dict = feedback_data

                await websocket.send_json({"type": "feedback", "data": feedback_dict})

                # Log every 30 frames
                if session["frame_count"] % 30 == 0:
                    accuracy = (
                        feedback_dict.get("accuracy", 0)
                        if isinstance(feedback_dict, dict)
                        else 0
                    )
                    logger.info(
                        f"📊 {pose_name} | Accuracy: {accuracy}% | Frames: {session['frame_count']}"
                    )

            elif action == "get_pose_info":
                # Get pose information
                pose_name = data.get("pose_name")
                if not pose_name:
                    await websocket.send_json(
                        {"type": "error", "message": "pose_name is required"}
                    )
                    continue

                pose_info = pose_validator.get_pose_info(pose_name)
                if pose_info:
                    await websocket.send_json({"type": "pose_info", "data": pose_info})
                else:
                    await websocket.send_json(
                        {"type": "error", "message": f"Pose '{pose_name}' not found"}
                    )

            elif action == "list_poses":
                # List all available poses
                poses = pose_validator.list_all_poses()
                await websocket.send_json({"type": "poses_list", "poses": poses})

            elif action == "ping":
                # Respond to ping (keep-alive)
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json(
                    {"type": "error", "message": f"Unknown action: {action}"}
                )

    except WebSocketDisconnect:
        logger.info(f"❌ WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        # Cleanup session
        if str(client_id) in active_sessions:
            del active_sessions[str(client_id)]

        try:
            await websocket.close()
        except:
            pass


# ============= REST API Endpoints =============


@router.get("/poses", response_model=PoseListResponse)
async def get_available_poses():
    """Get list of all available yoga poses"""
    try:
        poses = []

        # ✅ Use PoseValidator utility to list poses
        available_poses = pose_validator.list_all_poses()

        for pose_name in available_poses:
            pose_info = pose_validator.get_pose_info(pose_name)

            if pose_info:
                poses.append(
                    PoseInfo(
                        name=pose_name,
                        display_name=pose_info.get(
                            "name", pose_name.replace("_", " ").title()
                        ),
                        description=pose_info.get("description", ""),
                        difficulty=pose_info.get("difficulty", "beginner"),
                        benefits=parse_benefits(pose_info.get("benefits", [])),
                        duration=pose_info.get("duration"),
                        image=pose_info.get("image"),
                    )
                )

        logger.info(f"✅ Returning {len(poses)} available poses")
        return PoseListResponse(poses=poses, total=len(poses))

    except Exception as e:
        logger.error(f"❌ Error fetching poses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching poses: {str(e)}")


@router.get("/poses/{pose_name}")
async def get_pose_details(pose_name: str):
    """Get detailed information about a specific pose"""
    try:
        # ✅ Use PoseValidator utility
        pose_info = pose_validator.get_pose_info(pose_name)

        if not pose_info:
            raise HTTPException(status_code=404, detail=f"Pose '{pose_name}' not found")

        logger.info(f"✅ Returning details for pose: {pose_name}")
        return {
            "name": pose_name,
            "display_name": pose_info.get("name", pose_name.replace("_", " ").title()),
            "description": pose_info.get("description", ""),
            "difficulty": pose_info.get("difficulty", "beginner"),
            "benefits": parse_benefits(pose_info.get("benefits", [])),
            "duration": pose_info.get("duration"),
            "image": pose_info.get("image"),
            "instructions": pose_info.get("instructions", []),
            "key_angles": pose_info.get("reference_angles", {}),
            "contraindications": pose_info.get("contraindications", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching pose details: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching pose details: {str(e)}"
        )


@router.post("/analyze", response_model=PoseAnalysisResponse)
async def analyze_pose(pose_name: str = Form(...), image: UploadFile = File(...)):
    """Analyze uploaded image for yoga pose detection and validation"""
    try:
        logger.info(f"🔍 Analyzing pose: {pose_name}")

        # Validate pose exists
        if pose_name not in pose_validator.list_all_poses():
            raise HTTPException(status_code=404, detail=f"Pose '{pose_name}' not found")

        # Read image file
        image_bytes = await image.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect pose
        results = pose_detector.process(frame_rgb)

        if not results.pose_landmarks:
            return PoseAnalysisResponse(
                pose_name=pose_name,
                detected_angles={},
                validation=ValidationResult(
                    valid=False,
                    accuracy=0.0,
                    feedback=[
                        FeedbackItem(
                            joint="Detection",
                            expected=0.0,
                            detected=0.0,
                            correction="No pose detected. Please ensure your full body is visible in the frame",
                        )
                    ],
                    angle_diffs={},
                ),
                landmarks=None,
            )

        # Extract landmarks
        landmarks = [
            {
                "x": float(lm.x),
                "y": float(lm.y),
                "z": float(lm.z),
                "visibility": float(lm.visibility),
            }
            for lm in results.pose_landmarks.landmark
        ]

        # ✅ Use utility function for angle calculation
        detected_angles = calc_angles_util(results.pose_landmarks)

        if not detected_angles:
            raise HTTPException(status_code=500, detail="Failed to calculate angles")

        # ✅ Use PoseValidator for intelligent feedback
        validation = validate_pose_with_feedback(detected_angles, pose_name)

        logger.info(f"✅ Analysis complete - Accuracy: {validation.accuracy}%")

        return PoseAnalysisResponse(
            pose_name=pose_name,
            detected_angles=detected_angles,
            validation=validation,
            landmarks=landmarks,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Pose analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pose analysis failed: {str(e)}")


@router.post("/analyze-base64")
async def analyze_pose_base64(request: PoseAnalysisRequest):
    """Analyze base64 encoded image for yoga pose detection"""
    try:
        logger.info(f"🔍 Analyzing pose (base64): {request.pose_name}")

        # Validate pose exists
        if request.pose_name not in pose_validator.list_all_poses():
            raise HTTPException(
                status_code=404, detail=f"Pose '{request.pose_name}' not found"
            )

        # Use the helper function
        result = process_video_frame(request.image_base64, request.pose_name)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        # Get detected angles from the frame processing
        # We need to recalculate or store them - let's decode and process again
        image_data = request.image_base64
        if "," in image_data:
            image_data = image_data.split(",")[1]

        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose_detector.process(frame_rgb)

        detected_angles = {}
        if results.pose_landmarks:
            detected_angles = calc_angles_util(results.pose_landmarks)

        logger.info(
            f"✅ Base64 analysis complete - Accuracy: {result['feedback'].accuracy}%"
        )

        return PoseAnalysisResponse(
            pose_name=request.pose_name,
            detected_angles=detected_angles,
            validation=result["feedback"],
            landmarks=result.get("landmarks"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Base64 analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
async def yoga_health_check():
    """Health check endpoint for yoga system"""
    try:
        status = {
            "status": "healthy",
            "mediapipe_loaded": pose_detector is not None,
            "reference_poses_loaded": len(reference_poses) > 0,
            "total_poses": len(pose_validator.list_all_poses()),
            "pose_data_path": str(POSE_DATA_PATH),
            "pose_data_exists": POSE_DATA_PATH.exists(),
            "validator_loaded": pose_validator is not None,
            "websocket_enabled": True,
            "active_sessions": len(active_sessions),
        }

        if len(reference_poses) == 0:
            status["status"] = "unhealthy"
            status["error"] = "No reference poses loaded"

        return status

    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}
