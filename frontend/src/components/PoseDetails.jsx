import React from 'react';

function PoseDetails({ poseInfo, currentPose, feedback, accuracy }) {
  if (!currentPose) {
    return (
      <div className="pose-details">
        <h2>Select a Pose</h2>
        <p className="placeholder">Choose a yoga pose from the checklist below to begin</p>
      </div>
    );
  }

  return (
    <div className="pose-details">
      <h2>{poseInfo?.name || 'Loading...'}</h2>
      
      {poseInfo?.image && (
        <div className="pose-image-container">
          <img 
            src={`http://localhost:5000/static/images/poses/${poseInfo.image}`}
            alt={poseInfo.name}
            className="pose-reference-image"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </div>
      )}
      
      {poseInfo && (
        <>
          <div className="info-section">
            <h3>📋 Instructions</h3>
            <p>{poseInfo.instructions}</p>
          </div>

          <div className="info-section">
            <h3>💪 Benefits</h3>
            <p>{poseInfo.benefits}</p>
          </div>

          <div className="info-section">
            <h3>⏱️ Recommended Hold Time</h3>
            <p className="duration">{poseInfo.duration} seconds</p>
          </div>
        </>
      )}

      {feedback.length > 0 && (
        <div className="feedback-section">
          <h3>🎯 Real-time Feedback</h3>
          <div className="accuracy-bar">
            <div 
              className="accuracy-fill"
              style={{ 
                width: `${accuracy}%`,
                backgroundColor: accuracy >= 70 ? '#4caf50' : accuracy >= 50 ? '#ff9800' : '#f44336'
              }}
            />
            <span className="accuracy-text">{accuracy}%</span>
          </div>
          <ul className="feedback-list">
            {feedback.map((msg, idx) => (
              <li key={idx}>{msg}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default PoseDetails;