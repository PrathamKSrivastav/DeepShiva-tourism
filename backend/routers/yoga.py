"""
Yoga Pose Validation API

Pose *detection* runs entirely in the browser via @mediapipe/pose (WebAssembly).
This backend only receives the 33 landmarks, calculates joint angles with numpy,
and returns validation feedback.  No cv2 / mediapipe / torch required.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import json
from pathlib import Path

from utils.angle_calculator import calculate_body_angles
from utils.pose_validator import PoseValidator

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Reference pose data
# ---------------------------------------------------------------------------
POSE_DATA_PATH = Path(__file__).parent.parent / "pose_data" / "reference_poses.json"
pose_validator = PoseValidator(poses_json_path=str(POSE_DATA_PATH))
active_sessions: Dict[str, Dict[str, Any]] = {}


def _load_reference_poses() -> Dict[str, Any]:
    try:
        if POSE_DATA_PATH.exists():
            with open(POSE_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"✅ Loaded {len(data)} reference poses")
                return data
        logger.warning(f"Reference poses file not found: {POSE_DATA_PATH}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load reference poses: {e}")
        return {}


reference_poses = _load_reference_poses()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class Landmark(BaseModel):
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0


class LandmarkAnalysisRequest(BaseModel):
    pose_name: str
    landmarks: List[Landmark]   # 33 MediaPipe landmarks from browser


class FeedbackItem(BaseModel):
    joint: str
    expected: float
    detected: float
    correction: str


class ValidationResult(BaseModel):
    valid: bool
    accuracy: float
    feedback: List[FeedbackItem]
    angle_diffs: Dict[str, Dict[str, float]]


class LandmarkAnalysisResponse(BaseModel):
    pose_name: str
    detected_angles: Dict[str, float]
    validation: ValidationResult


class PoseInfo(BaseModel):
    name: str
    display_name: str
    description: str
    difficulty: str
    benefits: List[str]
    duration: Optional[int] = None
    image: Optional[str] = None


class PoseListResponse(BaseModel):
    poses: List[PoseInfo]
    total: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_benefits(benefits: Any) -> List[str]:
    if isinstance(benefits, list):
        return benefits
    if isinstance(benefits, str):
        for sep in (",", ";", "\n"):
            if sep in benefits:
                return [b.strip() for b in benefits.split(sep) if b.strip()]
        return [benefits]
    return []


def _format_validation(result: Dict[str, Any]) -> ValidationResult:
    items = []
    for msg in result.get("feedback", []):
        if ":" in msg:
            joint, correction = msg.split(":", 1)
            joint = joint.strip()
            correction = correction.strip()
            expected = detected = 0.0
            key = joint.lower().replace(" ", "_")
            if key in result.get("angle_diffs", {}):
                info = result["angle_diffs"][key]
                expected = info.get("reference", 0.0)
                detected = info.get("current", 0.0)
            items.append(FeedbackItem(joint=joint, expected=expected,
                                      detected=detected, correction=correction))
        else:
            items.append(FeedbackItem(joint="General", expected=0.0,
                                      detected=0.0, correction=msg))
    return ValidationResult(
        valid=result.get("is_valid", False),
        accuracy=result.get("accuracy", 0.0),
        feedback=items,
        angle_diffs=result.get("angle_diffs", {}),
    )


def _validate(landmarks_dicts: List[dict], pose_name: str) -> tuple[Dict[str, float], ValidationResult]:
    detected_angles = calculate_body_angles(landmarks_dicts) or {}
    try:
        raw = pose_validator.validate_pose(pose_name, detected_angles)
        validation = _format_validation(raw)
    except Exception as e:
        logger.error(f"Validation error: {e}")
        validation = ValidationResult(
            valid=False, accuracy=0.0,
            feedback=[FeedbackItem(joint="Error", expected=0.0, detected=0.0, correction=str(e))],
            angle_diffs={},
        )
    return detected_angles, validation


# ---------------------------------------------------------------------------
# WebSocket — real-time (browser sends landmarks, not images)
# ---------------------------------------------------------------------------

@router.websocket("/ws")
async def websocket_yoga_analysis(websocket: WebSocket):
    """
    Protocol (browser → backend):
      {action: "start",  pose_name: "tree_pose"}
      {action: "frame",  pose_name: "tree_pose", landmarks: [{x,y,z,visibility}×33]}
      {action: "stop"}
      {action: "ping"}

    Backend → browser:
      {type: "connected"}
      {type: "analysis_started", pose_name}
      {type: "feedback", data: {valid, accuracy, feedback[], angle_diffs{}}}
      {type: "analysis_stopped"}
      {type: "error", message}
      {type: "pong"}
    """
    await websocket.accept()
    client_id = str(id(websocket))
    active_sessions[client_id] = {"is_analyzing": False, "current_pose": None, "frame_count": 0}
    logger.info(f"WebSocket connected: {client_id}")

    try:
        await websocket.send_json({"type": "connected", "client_id": client_id})

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "start":
                pose_name = data.get("pose_name")
                if not pose_name:
                    await websocket.send_json({"type": "error", "message": "pose_name is required"})
                    continue
                if pose_name not in pose_validator.list_all_poses():
                    await websocket.send_json({"type": "error", "message": f"Pose '{pose_name}' not found"})
                    continue
                active_sessions[client_id].update(
                    {"is_analyzing": True, "current_pose": pose_name, "frame_count": 0}
                )
                await websocket.send_json({"type": "analysis_started", "pose_name": pose_name})

            elif action == "stop":
                active_sessions[client_id].update({"is_analyzing": False, "current_pose": None})
                await websocket.send_json({"type": "analysis_stopped"})

            elif action == "frame":
                session = active_sessions[client_id]
                if not session["is_analyzing"]:
                    continue

                raw_landmarks = data.get("landmarks")
                pose_name = data.get("pose_name") or session["current_pose"]

                if not raw_landmarks or not pose_name:
                    continue

                _, validation = _validate(raw_landmarks, pose_name)
                session["frame_count"] += 1

                await websocket.send_json({"type": "feedback", "data": validation.dict()})

                if session["frame_count"] % 30 == 0:
                    logger.info(f"{pose_name} | {validation.accuracy:.1f}% | frames={session['frame_count']}")

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

            elif action == "list_poses":
                await websocket.send_json({"type": "poses_list", "poses": pose_validator.list_all_poses()})

            elif action == "get_pose_info":
                pose_name = data.get("pose_name")
                info = pose_validator.get_pose_info(pose_name) if pose_name else None
                if info:
                    await websocket.send_json({"type": "pose_info", "data": info})
                else:
                    await websocket.send_json({"type": "error", "message": f"Pose '{pose_name}' not found"})

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown action: {action}"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        active_sessions.pop(client_id, None)
        try:
            await websocket.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@router.post("/analyze-landmarks", response_model=LandmarkAnalysisResponse)
async def analyze_landmarks(request: LandmarkAnalysisRequest):
    """
    Validate a pose from browser-detected landmarks.
    The browser runs @mediapipe/pose and sends the 33 landmark points here.
    """
    if len(request.landmarks) < 29:
        raise HTTPException(status_code=400, detail="Need at least 29 landmarks")
    if request.pose_name not in pose_validator.list_all_poses():
        raise HTTPException(status_code=404, detail=f"Pose '{request.pose_name}' not found")

    lm_dicts = [lm.dict() for lm in request.landmarks]
    detected_angles, validation = _validate(lm_dicts, request.pose_name)

    return LandmarkAnalysisResponse(
        pose_name=request.pose_name,
        detected_angles=detected_angles,
        validation=validation,
    )


@router.get("/poses", response_model=PoseListResponse)
async def get_available_poses():
    try:
        poses = []
        for pose_name in pose_validator.list_all_poses():
            info = pose_validator.get_pose_info(pose_name)
            if info:
                poses.append(PoseInfo(
                    name=pose_name,
                    display_name=info.get("name", pose_name.replace("_", " ").title()),
                    description=info.get("description", ""),
                    difficulty=info.get("difficulty", "beginner"),
                    benefits=parse_benefits(info.get("benefits", [])),
                    duration=info.get("duration"),
                    image=info.get("image"),
                ))
        return PoseListResponse(poses=poses, total=len(poses))
    except Exception as e:
        logger.error(f"Error fetching poses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/poses/{pose_name}")
async def get_pose_details(pose_name: str):
    info = pose_validator.get_pose_info(pose_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Pose '{pose_name}' not found")
    return {
        "name": pose_name,
        "display_name": info.get("name", pose_name.replace("_", " ").title()),
        "description": info.get("description", ""),
        "difficulty": info.get("difficulty", "beginner"),
        "benefits": parse_benefits(info.get("benefits", [])),
        "duration": info.get("duration"),
        "image": info.get("image"),
        "instructions": info.get("instructions", []),
        "key_angles": info.get("reference_angles", {}),
        "contraindications": info.get("contraindications", []),
    }


@router.get("/health")
async def yoga_health():
    return {
        "status": "healthy",
        "pose_detection": "browser-side (@mediapipe/pose)",
        "reference_poses_loaded": len(reference_poses) > 0,
        "total_poses": len(pose_validator.list_all_poses()),
        "active_sessions": len(active_sessions),
    }
