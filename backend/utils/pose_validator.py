import json
import os

class PoseValidator:
    def __init__(self, poses_json_path='pose_data/reference_poses.json'):
        """Initialize with reference poses from JSON file."""
        with open(poses_json_path, 'r') as f:
            self.reference_poses = json.load(f)
        
        # Pose-specific feedback templates
        self.pose_feedback_templates = {
            't_pose': {
                'shoulder': 'Keep arms straight out at shoulder level',
                'elbow': 'Extend arms fully, palms facing down',
                'knee': 'Stand tall with legs straight',
                'hip': 'Keep hips level and body upright'
            },
            'trikonasana': {
                'knee': 'Keep both legs straight and engaged',
                'shoulder': 'Extend arms in line with shoulders',
                'hip': 'Open hips towards the side, not forward',
                'general': 'Reach fingertips towards ankle while keeping chest open'
            },
            'virabhadrasana': {
                'knee': 'Front knee should be bent at 90°, back leg straight',
                'elbow': 'Extend arms straight overhead',
                'shoulder': 'Raise arms fully, reaching towards sky',
                'hip': 'Square hips forward and engage core'
            },
            'warrior_2': {
                'knee': 'Front knee bent at 90°, aligned over ankle',
                'shoulder': 'Arms parallel to ground, shoulders relaxed',
                'hip': 'Open hips to the side, torso upright',
                'general': 'Gaze over front hand, keep back leg strong'
            },
            'vrikshasana': {
                'knee': 'Lift knee out to the side, foot on inner thigh',
                'hip': 'Keep standing leg straight and engaged',
                'general': 'Balance on one leg, hands in prayer or overhead'
            },
            'naukasana': {
                'hip': 'Lift legs and torso to 45° angle',
                'knee': 'Keep legs straight or slightly bent',
                'shoulder': 'Extend arms parallel to ground',
                'general': 'Balance on sitting bones, engage core'
            },
            'bhujangasana': {
                'elbow': 'Keep elbows slightly bent, close to body',
                'shoulder': 'Lift chest up, shoulders back and down',
                'hip': 'Keep pelvis grounded, legs together',
                'general': 'Press palms down, lift chest without straining neck'
            },
            'chakrasana': {
                'knee': 'Bend knees at 90°, feet hip-width apart',
                'elbow': 'Keep arms bent, hands flat near shoulders',
                'shoulder': 'Press into hands, lift hips high',
                'general': 'Create strong arch, weight distributed evenly'
            },
            'balasana': {
                'knee': 'Knees wide, sit back on heels',
                'hip': 'Lower hips towards heels',
                'shoulder': 'Extend arms forward or alongside body',
                'general': 'Relax forehead to ground, breathe deeply'
            },
            'sukhasana': {
                'knee': 'Sit cross-legged, knees relaxed',
                'hip': 'Keep hips open and grounded',
                'shoulder': 'Shoulders relaxed, spine straight',
                'general': 'Sit tall with hands on knees, breathe naturally'
            },
            'shavasana': {
                'knee': 'Legs slightly apart, fully relaxed',
                'elbow': 'Arms by sides, palms facing up',
                'hip': 'Body completely relaxed, no tension',
                'general': 'Lie flat, release all muscle tension, breathe deeply'
            }
        }

    def get_pose_specific_feedback(self, pose_name, angle_name, diff, current_value, ref_value):
        """Generate pose-specific feedback instead of generic messages."""
        
        # Get pose-specific templates
        templates = self.pose_feedback_templates.get(pose_name, {})
        
        # Identify body part from angle name
        if 'knee' in angle_name:
            body_part = 'knee'
        elif 'elbow' in angle_name:
            body_part = 'elbow'
        elif 'shoulder' in angle_name:
            body_part = 'shoulder'
        elif 'hip' in angle_name:
            body_part = 'hip'
        else:
            body_part = 'general'
        
        # Get specific feedback for this pose and body part
        specific_feedback = templates.get(body_part, templates.get('general', ''))
        
        if specific_feedback:
            return specific_feedback
        
        # Fallback to generic feedback if no specific template
        joint_name = angle_name.replace('_', ' ').title()
        if current_value > ref_value:
            return f"Straighten your {joint_name} more ({round(diff, 1)}° off)"
        else:
            return f"Bend your {joint_name} more ({round(diff, 1)}° off)"

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
            
            # Generate POSE-SPECIFIC feedback
            if diff > tolerance:
                feedback_msg = self.get_pose_specific_feedback(
                    pose_name, angle_name, diff, current_value, ref_value
                )
                if feedback_msg not in feedback:  # Avoid duplicates
                    feedback.append(feedback_msg)
        
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