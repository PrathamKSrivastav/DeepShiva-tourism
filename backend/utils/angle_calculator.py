import numpy as np
import math

def calculate_angle(point_a, point_b, point_c):
    """
    Calculate angle between three points (in degrees).
    point_b is the vertex of the angle.
    
    Args:
        point_a: [x, y] coordinates of first point
        point_b: [x, y] coordinates of vertex point
        point_c: [x, y] coordinates of third point
    
    Returns:
        angle in degrees (0-180)
    """
    a = np.array(point_a)  # First point
    b = np.array(point_b)  # Vertex (mid point)
    c = np.array(point_c)  # End point
    
    # Calculate vectors
    ba = a - b
    bc = c - b
    
    # Calculate angle using arctangent2
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])
    
    angle = np.abs(radians * 180.0 / np.pi)
    
    # Normalize to 0-180 range
    if angle > 180.0:
        angle = 360 - angle
    
    return angle


def extract_landmarks_as_points(landmarks, indices):
    """
    Extract specific landmarks as [x, y] coordinate points.
    
    Args:
        landmarks: MediaPipe landmarks object
        indices: List of landmark indices to extract
    
    Returns:
        List of [x, y] coordinates
    """
    points = []
    for idx in indices:
        landmark = landmarks[idx]
        points.append([landmark.x, landmark.y])
    
    return points


def calculate_body_angles(landmarks):
    """
    Calculate key body angles from MediaPipe pose landmarks.
    
    Args:
        landmarks: MediaPipe pose landmarks
    
    Returns:
        Dictionary of body angles
    """
    # MediaPipe landmark indices
    # 11: Left Shoulder, 13: Left Elbow, 15: Left Wrist
    # 12: Right Shoulder, 14: Right Elbow, 16: Right Wrist
    # 23: Left Hip, 25: Left Knee, 27: Left Ankle
    # 24: Right Hip, 26: Right Knee, 28: Right Ankle
    
    angles = {}
    
    try:
        # Left arm angle (shoulder-elbow-wrist)
        left_arm = extract_landmarks_as_points(landmarks.landmark, [11, 13, 15])
        angles['left_elbow'] = calculate_angle(left_arm[0], left_arm[1], left_arm[2])
        
        # Right arm angle
        right_arm = extract_landmarks_as_points(landmarks.landmark, [12, 14, 16])
        angles['right_elbow'] = calculate_angle(right_arm[0], right_arm[1], right_arm[2])
        
        # Left leg angle (hip-knee-ankle)
        left_leg = extract_landmarks_as_points(landmarks.landmark, [23, 25, 27])
        angles['left_knee'] = calculate_angle(left_leg[0], left_leg[1], left_leg[2])
        
        # Right leg angle
        right_leg = extract_landmarks_as_points(landmarks.landmark, [24, 26, 28])
        angles['right_knee'] = calculate_angle(right_leg[0], right_leg[1], right_leg[2])
        
        # Left shoulder angle (hip-shoulder-elbow)
        left_shoulder = extract_landmarks_as_points(landmarks.landmark, [23, 11, 13])
        angles['left_shoulder'] = calculate_angle(left_shoulder[0], left_shoulder[1], left_shoulder[2])
        
        # Right shoulder angle
        right_shoulder = extract_landmarks_as_points(landmarks.landmark, [24, 12, 14])
        angles['right_shoulder'] = calculate_angle(right_shoulder[0], right_shoulder[1], right_shoulder[2])
        
        # Left hip angle (shoulder-hip-knee)
        left_hip = extract_landmarks_as_points(landmarks.landmark, [11, 23, 25])
        angles['left_hip'] = calculate_angle(left_hip[0], left_hip[1], left_hip[2])
        
        # Right hip angle
        right_hip = extract_landmarks_as_points(landmarks.landmark, [12, 24, 26])
        angles['right_hip'] = calculate_angle(right_hip[0], right_hip[1], right_hip[2])
        
    except Exception as e:
        print(f"Error calculating angles: {e}")
        return None
    
    return angles
