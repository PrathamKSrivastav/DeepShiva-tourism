import json
import os

class PoseValidator:
    def __init__(self, poses_json_path='pose_data/reference_poses.json'):
        """Initialize with reference poses from JSON file."""
        with open(poses_json_path, 'r') as f:
            self.reference_poses = json.load(f)
    
    def validate_pose(self, pose_name, calculated_angles):
        """
        Validate if current pose matches reference pose.
        
        Args:
            pose_name: Name of the pose to validate against
            calculated_angles: Dictionary of calculated angles from current frame
        
        Returns:
            dict: {
                'is_valid': bool,
                'accuracy': float (0-100),
                'feedback': list of correction messages,
                'angle_diffs': dict of angle differences
            }
        """
        if pose_name not in self.reference_poses:
            return {
                'is_valid': False,
                'accuracy': 0,
                'feedback': ['Pose not found in database'],
                'angle_diffs': {}
            }
        
        if not calculated_angles:
            return {
                'is_valid': False,
                'accuracy': 0,
                'feedback': ['No pose detected'],
                'angle_diffs': {}
            }
        
        reference = self.reference_poses[pose_name]['reference_angles']
        tolerance = reference.get('tolerance', 15)
        
        feedback = []
        angle_diffs = {}
        total_error = 0
        num_angles = 0
        
        # Compare each angle
        for angle_name, ref_value in reference.items():
            if angle_name == 'tolerance':
                continue
            
            if angle_name not in calculated_angles:
                continue
            
            current_value = calculated_angles[angle_name]
            diff = abs(current_value - ref_value)
            angle_diffs[angle_name] = {
                'current': round(current_value, 1),
                'reference': ref_value,
                'difference': round(diff, 1)
            }
            
            total_error += diff
            num_angles += 1
            
            # Generate feedback
            if diff > tolerance:
                joint_name = angle_name.replace('_', ' ').title()
                if current_value > ref_value:
                    feedback.append(f"Straighten your {joint_name} more ({round(diff, 1)}° off)")
                else:
                    feedback.append(f"Bend your {joint_name} more ({round(diff, 1)}° off)")
        
        # Calculate accuracy score
        if num_angles == 0:
            accuracy = 0
        else:
            avg_error = total_error / num_angles
            accuracy = max(0, 100 - (avg_error * 2))  # 2% penalty per degree error
        
        is_valid = accuracy >= 70  # 70% threshold for "correct" pose
        
        if not feedback:
            feedback = ['Perfect form! Hold this position.']
        
        return {
            'is_valid': is_valid,
            'accuracy': round(accuracy, 1),
            'feedback': feedback[:3],  # Max 3 feedback messages
            'angle_diffs': angle_diffs
        }
    
    def get_pose_info(self, pose_name):
        """Get full information about a specific pose."""
        return self.reference_poses.get(pose_name, None)
    
    def list_all_poses(self):
        """Return list of all available pose names."""
        return list(self.reference_poses.keys())
