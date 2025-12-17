import React from 'react';

function PoseChecklist({ poses, currentPose, completedPoses, onPoseSelect, onToggleComplete }) {
  return (
    <div className="pose-checklist">
      <h3>📝 Pose Routine</h3>
      <ul className="checklist">
        {poses.map((pose) => {
          const isCompleted = completedPoses.includes(pose.id);
          const isCurrent = currentPose === pose.id;
          
          return (
            <li 
              key={pose.id}
              className={`checklist-item ${isCurrent ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
            >
              <input
                type="checkbox"
                checked={isCompleted}
                onChange={() => onToggleComplete(pose.id)}
              />
              <span 
                className="pose-name"
                onClick={() => onPoseSelect(pose.id)}
              >
                {pose.name}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default PoseChecklist;