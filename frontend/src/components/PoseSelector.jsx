import React from 'react';

function PoseSelector({ poses, currentPose, completedPoses, onPoseSelect }) {
  
  // Group poses by category
  const groupedPoses = poses.reduce((acc, pose) => {
    if (!acc[pose.category]) {
      acc[pose.category] = [];
    }
    acc[pose.category].push(pose);
    return acc;
  }, {});

  return (
    <div className="pose-selector">
      <h3>🎯 Select Your Pose</h3>
      
      {Object.entries(groupedPoses).map(([category, categoryPoses]) => (
        <div key={category} className="pose-category">
          <h4 className="category-title">{category} Poses</h4>
          <div className="pose-buttons">
            {categoryPoses.map((pose) => {
              const isCompleted = completedPoses.includes(pose.id);
              const isCurrent = currentPose === pose.id;
              
              return (
                <button
                  key={pose.id}
                  className={`pose-button ${isCurrent ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                  onClick={() => onPoseSelect(pose.id)}
                >
                  <span className="pose-button-text">{pose.name}</span>
                  {isCompleted && <span className="checkmark">✓</span>}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

export default PoseSelector;