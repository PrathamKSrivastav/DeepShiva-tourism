import numpy as np
from typing import List, Dict, Any, Optional


def calculate_angle(point_a, point_b, point_c) -> float:
    """
    Angle at point_b formed by a→b→c, in degrees (0-180).
    Accepts [x, y] lists or tuples.
    """
    a = np.array(point_a[:2], dtype=float)
    b = np.array(point_b[:2], dtype=float)
    c = np.array(point_c[:2], dtype=float)

    radians = (
        np.arctan2(c[1] - b[1], c[0] - b[0])
        - np.arctan2(a[1] - b[1], a[0] - b[0])
    )
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return float(angle)


def _pt(landmarks: List[Dict[str, float]], idx: int) -> List[float]:
    """Return [x, y] from a landmark list (plain dicts with x/y keys)."""
    lm = landmarks[idx]
    return [lm["x"], lm["y"]]


def calculate_body_angles(landmarks) -> Optional[Dict[str, float]]:
    """
    Calculate key body angles from pose landmarks.

    Accepts either:
    - A list of 33 dicts with {x, y, z, visibility}  (new browser-side format)
    - A MediaPipe NormalizedLandmarkList object        (legacy, still works locally)

    MediaPipe landmark indices used:
        11 Left Shoulder  12 Right Shoulder
        13 Left Elbow     14 Right Elbow
        15 Left Wrist     16 Right Wrist
        23 Left Hip       24 Right Hip
        25 Left Knee      26 Right Knee
        27 Left Ankle     28 Right Ankle
    """
    try:
        # Normalise: accept both plain list-of-dicts and mediapipe landmark objects
        if isinstance(landmarks, list):
            lms = landmarks  # already list of dicts
        else:
            # MediaPipe NormalizedLandmarkList — wrap into dicts
            lms = [{"x": lm.x, "y": lm.y, "z": getattr(lm, "z", 0.0),
                    "visibility": getattr(lm, "visibility", 1.0)}
                   for lm in landmarks.landmark]

        def pt(idx):
            return _pt(lms, idx)

        return {
            "left_elbow":    calculate_angle(pt(11), pt(13), pt(15)),
            "right_elbow":   calculate_angle(pt(12), pt(14), pt(16)),
            "left_knee":     calculate_angle(pt(23), pt(25), pt(27)),
            "right_knee":    calculate_angle(pt(24), pt(26), pt(28)),
            "left_shoulder": calculate_angle(pt(23), pt(11), pt(13)),
            "right_shoulder":calculate_angle(pt(24), pt(12), pt(14)),
            "left_hip":      calculate_angle(pt(11), pt(23), pt(25)),
            "right_hip":     calculate_angle(pt(12), pt(24), pt(26)),
        }

    except Exception as e:
        print(f"Error calculating angles: {e}")
        return None
